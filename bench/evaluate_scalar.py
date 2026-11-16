"""Compare one generated scalar ANF factorization with the unchanged product.

The candidate is generated below build/, never added to the product or installed.
Results, successful regressions and raw timing samples decide whether it helps.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import re
import tarfile
import time


def run(command, log, timeout=1500):
    command = [str(x) for x in command]
    result = subprocess.run(command, text=True, capture_output=True, timeout=timeout)
    log.write_text(result.stdout+result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"exit {result.returncode}: {command}; see {log}")
    return result.stdout


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_archive(data, destination):
    with tarfile.open(fileobj=io.BytesIO(data)) as tree:
        for member in tree.getmembers():
            if not (member.isfile() or member.isdir()) or not (destination/member.name).resolve().is_relative_to(destination.resolve()):
                raise ValueError("archive contains unsupported entry or escaping path")
        tree.extractall(destination)


def invariants(report):
    data = {k:v["data"] for k,v in report["experiments"].items()}
    for field in ("raw_count_file",):
        data["discovery"].pop(field, None)
    data["holdout"].pop("discovery_report", None)
    return data


def main(args):
    root, work = args.source.resolve(), args.work.resolve()
    if (not work.is_relative_to(root) or not work.name.startswith("scalar-")
        or not work.relative_to(root).parts[0].startswith("build")):
        raise ValueError("work must be a new scalar-* directory below this repository's build directory")
    if work.exists():
        raise ValueError("work already exists; choose a fresh path to preserve evidence")
    work.mkdir(parents=True)
    started = time.monotonic()
    head = subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()
    archive = subprocess.check_output(["git","-C",str(root),"archive","HEAD"])
    candidate = work/"candidate-source"
    candidate.mkdir()
    extract_archive(archive, candidate)
    source = candidate/"src/interlock.c"
    original = source.read_text()
    start = original.index("    uint32_t y0 =")
    stop = original.index("    return y0",start)
    replacement = '''    uint32_t t01 = x0 & x1, t12 = x1 & x2, t03 = x0 & x3;
    uint32_t t13 = x1 & x3, t23 = x2 & x3;
    uint32_t t012 = t01 & x2, t013 = t01 & x3, t023 = t03 & x2;
    uint32_t y0 = x0 ^ x2 ^ t12 ^ x3;
    uint32_t y1 = x1 ^ t012 ^ x3 ^ t13 ^ t013 ^ t23 ^ t023;
    uint32_t y2 = lanes ^ t01 ^ x2 ^ x3 ^ t03 ^ t13 ^ t013 ^ t023;
    uint32_t y3 = lanes ^ x0 ^ x1 ^ t12 ^ t012 ^ x3 ^ t013 ^ t023;
'''
    source.write_text(original[:start]+replacement+original[stop:])
    report = {"status":"running","base_commit":head,"experiment":"explicit shared ANF monomials in scalar PRESENT substitution",
              "candidate_source_sha256":digest(source),"baseline_source_sha256":digest(root/"src/interlock.c"),
              "adoption_rule":"consider only if every paired 1MiB encryption AND decryption median improves at least 5%, full regressions agree, and machine code actually differs; no auto-adoption",
              "runs":[],"regressions":{}}
    builds = {}
    compilers = {}
    for name, src in (("baseline",root),("candidate",candidate)):
        build = work/(name+"-build")
        builds[name] = build
        print(f"{name}: configuring and running full regressions",flush=True)
        run([args.cmake,"-S",src,"-B",build,"-DCMAKE_BUILD_TYPE=Release","-DBUILD_TESTING=ON",
             "-DCRYPTO_BUILD_RESEARCH=ON","-DCRYPTO_BUILD_BENCHMARKS=ON"],work/(name+"-configure.log"))
        compiler_file = next((build/"CMakeFiles").glob("*/CMakeCCompiler.cmake"))
        metadata = compiler_file.read_text()
        compilers[name] = tuple(re.search(r'set\(CMAKE_C_COMPILER_'+field+r' "([^"\n]+)"\)',metadata)[1] for field in ("ID","VERSION"))
        run([args.cmake,"--build",build,"-j","4"],work/(name+"-build.log"))
        ctest = args.cmake.with_name("ctest")
        run([ctest,"--test-dir",build,"--output-on-failure"],work/(name+"-ctest.log"))
        run([args.cmake,"--build",build,"--target","research-full"],work/(name+"-research.log"))
        research = json.loads((build/"research/full.json").read_text())
        if research["status"] != "complete" or not all(x["status"] == "complete" for x in research["experiments"].values()):
            raise AssertionError("full research incomplete")
        text_path = work/(name+"-text.bin")
        obj = build/"CMakeFiles/interlock.dir/src/interlock.c.o"
        run(["objcopy","-O","binary","--only-section=.text",obj,text_path],work/(name+"-objcopy.log"))
        report["regressions"][name] = {"ctest":"23/23 passed (includes KAT, all1024 round prefixes, research smoke and benchmark correctness)",
            "full_research":"all six registered stages complete", "research_elapsed_seconds":research["elapsed_seconds"],
            "research_report_sha256":digest(build/"research/full.json"),"product_text_sha256":digest(text_path),
            "core_source_sha256":research["provenance"]["core_source_sha256"]}
    before = json.loads((builds["baseline"]/"research/full.json").read_text())
    after = json.loads((builds["candidate"]/"research/full.json").read_text())
    if invariants(before) != invariants(after):
        raise AssertionError("research invariants/counts differ")
    report["full_research_data_identical"] = True
    for pair in range(3):
        order = ("baseline","candidate") if pair%2 == 0 else ("candidate","baseline")
        print(f"paired native timing {pair+1}/3: {order}",flush=True)
        for name in order:
            build = builds[name]
            output = work/f"{name}-timing-{pair}.json"
            run(["python3",root/"bench/run.py","--source",root if name == "baseline" else candidate,
                 "--driver",build/"interlock_bench","--build-dir",build,"--compiler-id",compilers[name][0],
                 "--compiler-version",compilers[name][1],"--config","Release","--target-ms","20",
                 "--output",output],work/f"{name}-timing-{pair}.log",240)
            timing = json.loads(output.read_text())
            report["runs"].append({"pair":pair,"variant":name,
                "rows":[r for r in timing["rows"] if r["backend"] == "Interlock-128"],
                "driver_sha256":timing["provenance"]["driver_sha256"],"environment":timing["environment"],
                "checksum":timing["checksum"]})
    comparisons = []
    for pair in range(3):
        runs = {r["variant"]:r for r in report["runs"] if r["pair"] == pair}
        for operation in ("encrypt_ready","decrypt_ready"):
            values = {name:next(r["ns_per_iteration"]["median"] for r in value["rows"]
                        if r["operation"] == operation and r["bytes_per_iteration"] == 1048576)
                      for name,value in runs.items()}
            comparisons.append({"pair":pair,"operation":operation,
                                "baseline_over_candidate":values["baseline"]/values["candidate"]})
    report["paired_comparisons"] = comparisons
    report["product_text_identical"] = report["regressions"]["baseline"]["product_text_sha256"] == report["regressions"]["candidate"]["product_text_sha256"]
    report["meets_timing_rule"] = all(x["baseline_over_candidate"] >= 1/0.95 for x in comparisons)
    report["decision"] = "retain baseline" if report["product_text_identical"] or not report["meets_timing_rule"] else "candidate merits separate adoption and audit; not auto-applied"
    report["limits"] = "one GCC14 x86_64 shared-host scalar experiment, no affinity/frequency control; no proof across compilers/platforms; candidate kept only below ignored build/"
    report["elapsed_seconds"] = round(time.monotonic()-started,6)
    report["status"] = "complete"
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("status","decision","product_text_identical","meets_timing_rule","elapsed_seconds")}),flush=True)


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("source","work","cmake","output"):
        p.add_argument("--"+name,type=Path,required=True)
    main(p.parse_args())
