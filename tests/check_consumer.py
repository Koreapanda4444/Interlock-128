"""Install, relocate, and build a consumer from only the installed CMake package."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


def run(command):
    result = subprocess.run([str(x) for x in command], text=True, encoding="utf-8",
                            errors="replace", capture_output=True, timeout=150, check=False)
    if result.returncode:
        raise RuntimeError(f"{command!r} exited {result.returncode}\n{result.stdout}\n{result.stderr}")
    return result.stdout


def cache_variables(build):
    result = {}
    for line in (build / "CMakeCache.txt").read_text(encoding="utf-8").splitlines():
        if not line.startswith(("//", "#")) and ":" in line and "=" in line:
            key, value = line.split("=", 1)
            result[key.split(":", 1)[0]] = value
    return result


def symbols(archive, cache):
    candidate = cache.get("CMAKE_NM", "")
    tool = shutil.which(candidate) if candidate else None
    if tool is None and candidate and Path(candidate).is_file():
        tool = candidate
    if tool is None:
        tool = shutil.which("nm")
    if tool is not None and Path(tool).stem.lower() == "dumpbin":
        command = [tool, "/linkermember:1", archive]
    elif tool is not None:
        command = [tool, "-gU" if sys.platform == "darwin" else "--defined-only", archive]
        if sys.platform != "darwin":
            command.insert(1, "-g")
    else:
        archiver = cache.get("CMAKE_AR", "")
        dumpbin = Path(archiver).with_name("dumpbin.exe") if archiver else Path("dumpbin.exe")
        tool = str(dumpbin) if dumpbin.is_file() else shutil.which("dumpbin")
        if tool is None:
            raise RuntimeError("nm/dumpbin unavailable: cannot verify product symbol isolation")
        command = [tool, "/linkermember:1", archive]
    output = run(command)
    if "il_test_" in output or re.search(r"\b_?prefix_runner\b", output):
        raise AssertionError("test/reduced-round entrypoint present in installed product archive")
    for name in ("interlock_key_ctx_create", "interlock_key_ctx_free", "interlock_encrypt_block", "interlock_decrypt_block"):
        if name not in output:
            raise AssertionError(f"public symbol missing: {name}")
    return Path(tool).name


def main(args):
    parent = args.parent_build.resolve()
    work = args.work.resolve()
    if not work.is_relative_to(parent) or work == parent:
        raise ValueError("consumer work directory must be a child of the parent build")
    cache = cache_variables(parent)
    config = args.config or cache.get("CMAKE_BUILD_TYPE") or "Release"
    stage, prefix, source, build = (work / name for name in ("install-stage", "relocated-prefix", "source", "build"))
    for path in (stage, prefix, source, build):
        if path.exists():
            shutil.rmtree(path)
    work.mkdir(parents=True, exist_ok=True)
    run([args.cmake, "--install", parent, "--prefix", stage, "--config", config])
    stage.rename(prefix)
    shutil.copytree(Path(__file__).with_name("consumer"), source)
    archives = [p for p in prefix.rglob("*") if p.name in ("libinterlock.a", "interlock.lib")]
    if len(archives) != 1:
        raise AssertionError(f"expected exactly one installed product archive: {archives}")
    if any(p.name in ("internal.h", "prefix_runner", "prefix_runner.exe", "vector_runner", "vector_runner.exe") for p in prefix.rglob("*")):
        raise AssertionError("private header or driver was installed")
    symbol_tool = symbols(archives[0], cache)
    command = [args.cmake, "-S", source, "-B", build, f"-DCMAKE_PREFIX_PATH={prefix}", f"-DCMAKE_BUILD_TYPE={config}"]
    generator = cache.get("CMAKE_GENERATOR", "")
    if generator:
        command += ["-G", generator]
    for option, name in (("-A", "CMAKE_GENERATOR_PLATFORM"), ("-T", "CMAKE_GENERATOR_TOOLSET")):
        if cache.get(name):
            command += [option, cache[name]]
    for name in ("CMAKE_C_COMPILER", "CMAKE_TOOLCHAIN_FILE", "VCPKG_TARGET_TRIPLET", "OPENSSL_ROOT_DIR"):
        if cache.get(name):
            command.append(f"-D{name}={cache[name]}")
    run(command)
    run([args.cmake, "--build", build, "--config", config])
    ctest = Path(args.cmake).with_name("ctest.exe" if os.name == "nt" else "ctest")
    run([ctest, "--test-dir", build, "-C", config, "--output-on-failure"])
    print(json.dumps({"status": "passed", "relocated": True, "public_header_only": True,
                      "symbol_tool": symbol_tool, "private_symbols_absent": True,
                      "configuration": config, "sanitizer_library": cache.get("CRYPTO_ENABLE_SANITIZERS") == "ON"}, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cmake", type=Path, required=True)
    parser.add_argument("--parent-build", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--config", default="")
    main(parser.parse_args())
