"""Verify a fresh checkout of a specified local Git commit, with no cached build.

The caller separately verifies this commit against GitHub. This runner clones
local objects without hard links; it never assumes network authentication.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(args):
    source, work = args.source.resolve(), args.work.resolve()
    if not work.is_relative_to(source) or not work.relative_to(source).parts[0].startswith("build"):
        raise ValueError("work must be a new child of an ignored build* directory")
    if work.exists():
        raise ValueError("acceptance directory already exists; choose a fresh path")
    work.mkdir(parents=True)
    report = {"status":"running","started_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "host":platform.platform(),"driver_sha256":sha(Path(__file__)),"commands":[],
              "clone_method":"git clone --no-hardlinks --no-checkout from local objects; remote SHA checked separately through GitHub"}
    def flush():
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    def run(label, command, env=None, allowed=(0,), timeout=1500):
        start=time.monotonic()
        result=subprocess.run([str(x) for x in command],capture_output=True,text=True,env=env,timeout=timeout)
        log=work/(label+".log")
        log.write_text(result.stdout+result.stderr,encoding="utf-8")
        entry={"check":label,"returncode":result.returncode,"elapsed_seconds":round(time.monotonic()-start,6),
               "log_sha256":sha(log)}
        if "ctest" in label:
            match=re.search(r"100% tests passed(?:, 0 tests failed)? out of (\d+)",result.stdout)
            if match: entry["tests_passed"]=int(match[1])
        report["commands"].append(entry)
        flush()
        print(label+": exit "+str(result.returncode),flush=True)
        if result.returncode not in allowed:
            raise RuntimeError(f"{label} failed; see {log}")
        return result
    try:
        checkout=work/"checkout"
        run("clone",["git","clone","--no-hardlinks","--no-checkout",source,checkout])
        run("checkout",["git","-C",checkout,"checkout","--detach",args.commit])
        head=run("head",["git","-C",checkout,"rev-parse","HEAD"]).stdout.strip()
        if head != args.commit: raise AssertionError("checkout SHA mismatch")
        if run("initial-status",["git","-C",checkout,"status","--porcelain"]).stdout.strip():
            raise AssertionError("initial checkout not clean")
        report["commit"]=head
        release=checkout/"build-release"
        run("release-configure",[args.cmake,"-S",checkout,"-B",release,"-DCMAKE_BUILD_TYPE=Release",
            "-DBUILD_TESTING=ON","-DCRYPTO_BUILD_RESEARCH=ON","-DCRYPTO_BUILD_BENCHMARKS=ON"])
        run("release-build",[args.cmake,"--build",release,"-j","4"])
        ctest=args.cmake.with_name("ctest.exe" if os.name == "nt" else "ctest")
        run("release-ctest",[ctest,"--test-dir",release,"-C","Release","--output-on-failure"])
        for target in ("check-differential","research-smoke","research-full","bench"):
            run(target,[args.cmake,"--build",release,"--config","Release","--target",target])
        research=json.loads((release/"research/full.json").read_text())
        if research["status"] != "complete" or not all(v["status"] == "complete" for v in research["experiments"].values()):
            raise AssertionError("full research incomplete")
        original=json.loads((checkout/"research/results/full-baseline.json").read_text())
        for stage in ("harness","recovery","constraints","components"):
            if research["experiments"][stage]["data"] != original["experiments"][stage]["data"]:
                raise AssertionError("exact/recovery results changed: "+stage)
        for field in ("selected_candidates","registration_sha256","completed_pairs"):
            if research["experiments"]["discovery"]["data"][field] != original["experiments"]["discovery"]["data"][field]:
                raise AssertionError("discovery changed: "+field)
        for field in ("aggregate","cohorts","completed_pairs","frozen_candidates"):
            if research["experiments"]["holdout"]["data"][field] != original["experiments"]["holdout"]["data"][field]:
                raise AssertionError("holdout changed: "+field)
        report["research"]={"status":"complete","stages":list(research["experiments"]),
                            "data_matches_registered_baseline":True,"report_sha256":sha(release/"research/full.json")}
        audit=json.loads((checkout/"docs/audit_gcc14_x86_64.json").read_text())
        report["core_source_sha256"]={name:sha(checkout/name) for name in audit["source_sha256"]}
        if report["core_source_sha256"] != audit["source_sha256"]:
            raise AssertionError("product core changed since reviewed baseline")
        benchmark=json.loads((release/"bench/full.json").read_text())
        if (benchmark["status"] != "complete" or len(benchmark["rows"]) != 33
            or any(len(r["samples"]) < 5 for r in benchmark["rows"])):
            raise AssertionError("benchmark incomplete")
        report["benchmark"]={"status":"complete","rows":len(benchmark["rows"]),"minimum_samples":min(len(r["samples"]) for r in benchmark["rows"]),
                             "report_sha256":sha(release/"bench/full.json"),"timings_are_local_only":True}
        product=checkout/"build-product"
        run("product-configure",[args.cmake,"-S",checkout,"-B",product,"-DCMAKE_BUILD_TYPE=Release",
            "-DBUILD_TESTING=OFF","-DCRYPTO_BUILD_RESEARCH=OFF","-DCRYPTO_BUILD_BENCHMARKS=OFF"])
        run("product-build",[args.cmake,"--build",product,"-j","4"])
        run("product-consumer",["python3",checkout/"tests/check_consumer.py","--cmake",args.cmake,
            "--parent-build",product,"--work",product/"consumer-check","--config","Release"])
        for name,options,target in (("research-only",["-DCRYPTO_BUILD_RESEARCH=ON","-DCRYPTO_BUILD_BENCHMARKS=OFF"],"research-smoke"),
                                    ("bench-only",["-DCRYPTO_BUILD_RESEARCH=OFF","-DCRYPTO_BUILD_BENCHMARKS=ON"],"bench")):
            build=checkout/("build-"+name)
            run(name+"-configure",[args.cmake,"-S",checkout,"-B",build,"-DCMAKE_BUILD_TYPE=Release","-DBUILD_TESTING=OFF",*options])
            run(name+"-build",[args.cmake,"--build",build,"-j","4"])
            run(name+"-target",[args.cmake,"--build",build,"--target",target])
        sanitize=checkout/"build-sanitize"
        run("sanitize-configure",[args.cmake,"-S",checkout,"-B",sanitize,"-DCMAKE_BUILD_TYPE=Debug",
            "-DBUILD_TESTING=ON","-DCRYPTO_BUILD_RESEARCH=ON","-DCRYPTO_BUILD_BENCHMARKS=ON","-DCRYPTO_ENABLE_SANITIZERS=ON"])
        run("sanitize-build",[args.cmake,"--build",sanitize,"-j","4"])
        env=os.environ.copy()
        env.update(ASAN_OPTIONS="detect_leaks=1:halt_on_error=1",UBSAN_OPTIONS="halt_on_error=1:print_stacktrace=1")
        probe=run("lsan-probe",[sanitize/"test_platform"],env=env,allowed=(0,1))
        if probe.returncode:
            if "LeakSanitizer does not work under ptrace" not in probe.stderr:
                raise AssertionError("unexpected sanitizer probe failure")
            report["local_lsan"]="blocked by ptrace; not a leak pass"
            env["ASAN_OPTIONS"]="detect_leaks=0:halt_on_error=1"
        else: report["local_lsan"]="enabled for all following sanitizer tests"
        run("sanitize-ctest",[ctest,"--test-dir",sanitize,"--output-on-failure"],env=env)
        tracked=run("final-status",["git","-C",checkout,"status","--porcelain"]).stdout
        if tracked.strip(): raise AssertionError("checkout tracked/unignored files changed")
        report["checkout_clean_before_and_after"]=True
        report["product_install_consumer_and_private_symbol_isolation"]="passed"
        report["status"]="complete"
        report["scope"]="spec9.1 commands and local acceptance; remote CI and licensing recorded separately; no cryptographic approval"
    except Exception as exc:
        report["status"]="failed"
        report["error"]=str(exc)
        flush()
        raise
    flush()
    print(json.dumps({"status":report["status"],"commit":report["commit"],"output":str(args.output)}),flush=True)


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("source","work","cmake","output"):
        p.add_argument("--"+name,type=Path,required=True)
    p.add_argument("--commit",required=True)
    main(p.parse_args())
