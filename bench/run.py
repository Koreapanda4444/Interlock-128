"""Run native timings and attach reproducible build/source/environment evidence."""
import argparse
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import statistics
import subprocess


def main(args):
    root, build = args.source.resolve(), args.build_dir.resolve()
    command = [str(args.driver.resolve()), "--samples", str(args.samples),
               "--target-ms", str(args.target_ms)]
    result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=240)
    report = json.loads(result.stdout)
    report["measured_at_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    assert report["status"] == "complete" and len(report["checksum"]) == 16
    assert report["rows"]
    for row in report["rows"]:
        samples = row["samples"]
        assert len(samples) >= 5
        ns = []
        for sample in samples:
            assert sample["iterations"] > 0 and math.isfinite(sample["elapsed_seconds"])
            assert sample["elapsed_seconds"] > 0
            ns.append(sample["elapsed_seconds"] * 1e9 / sample["iterations"])
        row["ns_per_iteration"] = {"median": statistics.median(ns), "min": min(ns), "max": max(ns)}
        if row["bytes_per_iteration"]:
            row["median_mib_per_second"] = row["bytes_per_iteration"] * 1e9 / statistics.median(ns) / 1048576
    cache = {}
    for line in (build/"CMakeCache.txt").read_text(encoding="utf-8").splitlines():
        if not line.startswith(("#", "//")) and ":" in line and "=" in line:
            name,value = line.split("=",1)
            cache[name.split(":",1)[0]] = value
    cpu = platform.processor()
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        cpu = next((x.split(":",1)[1].strip() for x in cpuinfo.read_text().splitlines()
                    if x.startswith("model name")), cpu)
    paths = ["CMakeLists.txt", "cmake/Bench.cmake", "include/interlock.h"]
    paths += [p.relative_to(root).as_posix() for directory in ("src", "bench")
              for p in (root/directory).iterdir() if p.suffix in (".c", ".h", ".py")]
    report["provenance"] = {
        "source_sha256": {p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in sorted(paths)},
        "driver_sha256": hashlib.sha256(args.driver.read_bytes()).hexdigest(),
        "git_head": subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip(),
        "command": [args.driver.name, *command[1:]],
    }
    report["environment"] = {"os":platform.platform(), "architecture":platform.machine(), "cpu":cpu,
        "logical_cpus":os.cpu_count(), "python":platform.python_version(), "configuration":args.config,
        "compiler":args.compiler_id+" "+args.compiler_version,
        "cache":{k:cache[k] for k in ("CMAKE_C_FLAGS", "CMAKE_C_FLAGS_RELEASE", "CMAKE_C_FLAGS_DEBUG",
                   "CRYPTO_ENABLE_SANITIZERS", "CMAKE_GENERATOR", "CMAKE_INTERPROCEDURAL_OPTIMIZATION") if k in cache},
        "openssl_ia32cap_override":os.environ.get("OPENSSL_ia32cap"),
        "affinity_and_frequency":"not pinned or controlled; shared host; no cycle-count claim"}
    report["boundaries"] = {
        "key_create":"callback/public API + allocation + SHAKE256 + 448-byte schedule; pointer-array allocation and later free excluded",
        "key_free":"callback/public API + schedule cleanse + free; preparation and pointer-array free excluded",
        "fresh_key_encrypt_free":"create + one public 16-byte encryption + cleanse/free; no input generation",
        "ready":"prepared key reused; callback + loop + public argument checks + full 28 rounds + public cleanup; no key creation",
        "excluded":"data generation, buffer allocation, correctness checks, checksum and JSON printing; no LTO requested",
        "samples":"three untimed warmup iterations and untimed doubling calibration; at least five timed samples; target is a calibration goal, not a guaranteed minimum",
        "interpretation":"independent block API calls; no cipher mode or security equivalence claim"}
    report["aes_boundaries"] = {
        "algorithm":"OpenSSL fetched AES-256-ECB; padding disabled; provider name recorded",
        "acceleration":"OpenSSL automatic runtime dispatch using reported CPU capabilities; actual executed instruction path not traced",
        "key_create":"EVP_CIPHER_CTX_new + EVP_CipherInit_ex2 + set_padding(0); algorithm fetch excluded",
        "key_free":"EVP_CIPHER_CTX_free; contexts precreated; no application cleanse wrapper added",
        "fresh_key_encrypt_free":"context allocation/init + 16-byte Update + Final (zero output) + context free",
        "ready":"context initialized before samples; Update per block versus per buffer are separate rows; Final checked after timed rows",
        "correctness":"fixed FIPS197 Appendix C.3 encrypt/decrypt + every-buffer roundtrip + timed output equality + zero-length Final",
        "scope":"reference throughput/call overhead only; not equal-security comparison or a file-encryption API"}
    if platform.machine().lower() in ("x86_64", "amd64", "i386", "i686"):
        try:
            caps = [int(x, 0) for x in report["cpu_settings"].split("=", 1)[1].split()[0].split(":")]
            report["aes_capabilities"] = {"aesni_bit":bool(caps[0] & (1 << 57)),
                                          "vaes_bit":bool(caps[1] & (1 << 41)),
                                          "meaning":"reported dispatch capability bits; instruction path not traced"}
        except (IndexError, ValueError):
            report["aes_capabilities"] = {"status":"CPU settings format unavailable; not inferred"}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    temporary = args.output.with_suffix(".tmp")
    temporary.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    os.replace(temporary,args.output)
    print(json.dumps({"status":"complete","rows":len(report["rows"]),"samples_per_row":args.samples,
                      "output":str(args.output),"checksum":report["checksum"]}))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("source","driver","build-dir","output"):
        p.add_argument("--"+name,type=Path,required=True)
    p.add_argument("--samples",type=int,default=5)
    p.add_argument("--target-ms",type=float,default=40)
    p.add_argument("--compiler-id",required=True)
    p.add_argument("--compiler-version",required=True)
    p.add_argument("--config",default="Release")
    main(p.parse_args())
