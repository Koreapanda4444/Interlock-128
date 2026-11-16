"""Deterministic inputs, private C driver, bounded execution and provenance."""
import hashlib
import json
import os
from pathlib import Path
import platform
import struct
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import reference as oracle

SEED = 20261109
CORE_PATHS = ("src/interlock.c", "src/interlock_key.c", "src/support.c",
              "src/internal.h", "include/interlock.h")


class BudgetExceeded(Exception):
    pass


class ResearchFailure(Exception):
    pass


class Deadline:
    def __init__(self, seconds):
        if seconds < 0:
            raise ValueError("negative execution budget")
        self.start = time.monotonic()
        self.end = self.start + seconds

    def remaining(self):
        value = self.end - time.monotonic()
        if value <= 0:
            raise BudgetExceeded("execution budget exhausted")
        return value

    def check(self):
        self.remaining()


def stream(label, rounds, input_bit, key_index, length, seed=SEED):
    if label not in ("key", "discovery", "holdout") or length < 0:
        raise ValueError("invalid research stream")
    fields = struct.pack("<IIII", seed, rounds, input_bit, key_index)
    return hashlib.shake_256(b"Interlock-128/research\0" + label.encode("ascii") + b"\0" + fields).digest(length)


def research_key(index):
    return stream("key", 0, 0, index, 32)


def plaintexts(label, rounds, bit, index, count):
    data = stream(label, rounds, bit, index, 16*count)
    return [data[j:j+16] for j in range(0, len(data), 16)]


def digest_json(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2)+"\n", encoding="utf-8")
    os.replace(temporary, path)


def provenance(root, driver):
    root = Path(root)
    paths = list(CORE_PATHS) + ["tests/reference.py", "tests/vectors.json", "tests/vector_runner.c", "CMakeLists.txt", "cmake/Research.cmake"]
    paths += sorted(p.relative_to(root).as_posix() for p in (root/"research").glob("*.py"))
    files = {name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in paths}
    return {"source_sha256": files, "source_manifest_sha256": digest_json(files),
            "core_source_sha256": {name: files[name] for name in CORE_PATHS},
            "driver_sha256": hashlib.sha256(Path(driver).read_bytes()).hexdigest(),
            "driver": Path(driver).name}


class Driver:
    def __init__(self, executable, deadline):
        self.command = list(executable) if isinstance(executable, (list, tuple)) else [str(executable)]
        self.deadline = deadline

    def raw(self, lines):
        self.deadline.check()
        try:
            result = subprocess.run(self.command, input=lines, text=True, capture_output=True,
                                    timeout=self.deadline.remaining(), check=False)
        except subprocess.TimeoutExpired as exc:
            raise BudgetExceeded("C driver exceeded remaining budget") from exc
        self.deadline.check()
        if result.returncode:
            raise ResearchFailure(f"C driver exit {result.returncode}: {result.stderr[:1000]}")
        return result.stdout.splitlines()

    def query(self, records):
        records = list(records)
        lines = "".join(f"{op} {r} {key.hex()} {block.hex()}\n" for op,r,key,block in records)
        outputs = self.raw(lines)
        if len(outputs) != len(records):
            raise ResearchFailure("C driver line count mismatch")
        values = []
        for output, (operation, _, _, _) in zip(outputs, records):
            try:
                value = bytes.fromhex(output)
            except ValueError as exc:
                raise ResearchFailure("invalid C driver hex") from exc
            if len(value) != (448 if operation == "keys" else 16):
                raise ResearchFailure("invalid C driver output size")
            values.append(value)
        return values

    def encrypt(self, key, rounds, blocks):
        return self.query(("enc", rounds, key, block) for block in blocks)

    def schedule(self, key):
        data = self.query([("keys", 28, key, bytes(16))])[0]
        words = struct.unpack("<112I", data)
        return tuple(words[j:j+4] for j in range(0, 112, 4))


class Context:
    def __init__(self, args, stages):
        self.args = args
        self.profile = args.profile
        self.deadline = Deadline(args.budget_seconds)
        self.driver = Driver(args.driver, self.deadline)
        cache = {}
        cache_path = (args.build_dir or args.driver.parent)/"CMakeCache.txt"
        if cache_path.exists():
            for line in cache_path.read_text(encoding="utf-8").splitlines():
                if not line.startswith(("//", "#")) and ":" in line and "=" in line:
                    name,value = line.split("=",1)
                    cache[name.split(":",1)[0]] = value
        self.report = {"schema_version": 1, "algorithm": "Interlock-128", "seed": SEED,
                       "profile": args.profile, "status": "running", "budget_seconds": args.budget_seconds,
                       "registered_stages": list(stages), "experiments": {},
                       "provenance": provenance(args.source, args.driver),
                       "environment": {"os": platform.system(), "architecture": platform.machine(),
                                       "python": platform.python_version(), "compiler_id": args.compiler_id,
                                       "compiler_version": args.compiler_version, "configuration": args.config,
                                       "openssl": args.openssl_version,
                                       "build_flags": {name:cache[name] for name in
                                           ("CMAKE_C_FLAGS","CMAKE_C_FLAGS_RELEASE","CMAKE_C_FLAGS_DEBUG",
                                            "CRYPTO_ENABLE_SANITIZERS","CMAKE_GENERATOR") if name in cache}},
                       "limits": "finite experiments; not an approval for protecting confidential data"}

    def checkpoint(self, name, data, status="running"):
        self.report["experiments"][name] = {"status": status, "data": data}
        self.flush()

    def flush(self):
        self.report["elapsed_seconds"] = round(time.monotonic()-self.deadline.start, 6)
        write_json(self.args.output, self.report)
