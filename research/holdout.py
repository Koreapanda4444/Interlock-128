"""Validate frozen discovery candidates using different keys and input streams."""
import hashlib
import json
from pathlib import Path
import struct
from common import ResearchFailure, digest_json, plaintexts, research_key
from screening import registration, select_candidate, xor_bit
from statistics_ci import wilson


def validate_discovery(report, provenance, profile, raw_path):
    plan = registration(profile)
    entry = report.get("experiments",{}).get("discovery",{})
    data = entry.get("data",{})
    previous = report.get("provenance",{})
    if report.get("profile") != profile or entry.get("status") != "complete":
        raise ResearchFailure("complete matching-profile discovery required")
    if data.get("registration") != plan or data.get("registration_sha256") != digest_json(plan):
        raise ResearchFailure("discovery registration mismatch")
    if previous.get("core_source_sha256") != provenance["core_source_sha256"] or previous.get("driver_sha256") != provenance["driver_sha256"]:
        raise ResearchFailure("discovery core/binary changed; rerun discovery")
    old_hashes = {name.replace("\\","/"):value for name,value in previous.get("source_sha256",{}).items()}
    new_hashes = provenance["source_sha256"]
    for name in ("research/common.py","research/screening.py","tests/reference.py","tests/vectors.json","tests/vector_runner.c"):
        if old_hashes.get(name) != new_hashes.get(name):
            raise ResearchFailure(f"discovery generator/scoring source changed: {name}; rerun discovery")
    raw = Path(raw_path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != data["raw_count_file"]["sha256"]:
        raise ResearchFailure("discovery raw-count hash mismatch")
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
    expected = {(r,b) for r in plan["rounds"] for b in plan["input_bits"]}
    if len(rows) != len(expected) or {(row["rounds"],row["input_bit"]) for row in rows} != expected:
        raise ResearchFailure("incomplete or duplicate discovery count rows")
    samples = plan["discovery"]["pairs_per_input_bit"]
    by_round = {r:[] for r in plan["rounds"]}
    for row in rows:
        if row["pairs"] != samples or len(row["counts"]) != 128 or any(type(c) is not int or not 0 <= c <= samples for c in row["counts"]):
            raise ResearchFailure("invalid discovery count row")
        by_round[row["rounds"]].append((row["input_bit"],row["counts"]))
    candidates = []
    for rounds in plan["rounds"]:
        ordered = sorted(by_round[rounds])
        matrix = hashlib.sha256()
        for bit,counts in ordered:
            matrix.update(struct.pack("<II",rounds,bit)+struct.pack("<128I",*counts))
        if matrix.hexdigest() != data["rounds"][str(rounds)]["count_matrix_sha256"]:
            raise ResearchFailure("discovery matrix digest mismatch")
        selected = select_candidate(ordered,samples)
        selected["rounds"] = rounds
        candidates.append(selected)
    if candidates != data["selected_candidates"]:
        raise ResearchFailure("frozen candidate does not match registered selection/tie order")
    return candidates,plan


def holdout(ctx):
    source = ctx.args.discovery_json
    if source is not None:
        report = json.loads(source.read_text(encoding="utf-8"))
        if report.get("status") != "complete":
            raise ResearchFailure("cached discovery report is incomplete or failed")
        folder = source.parent
    else:
        report = ctx.report
        folder = ctx.args.output.parent
    entry = report.get("experiments",{}).get("discovery",{}).get("data",{})
    filename = entry.get("raw_count_file",{}).get("name","")
    if not filename or Path(filename).name != filename:
        raise ResearchFailure("valid discovery raw-count filename required")
    candidates,plan = validate_discovery(report,ctx.report["provenance"],ctx.profile,folder/filename)
    key_indices = plan["holdout"]["key_indices"]
    samples = plan["holdout"]["pairs_per_candidate_per_key"]
    if len({research_key(index) for index in [0]+key_indices}) != 1+len(key_indices):
        raise AssertionError("discovery and holdout master keys are not distinct")
    frozen = digest_json(candidates)
    summary = {"registration_sha256":digest_json(plan),"frozen_candidates":candidates,
               "frozen_candidates_sha256":frozen,"discovery_raw_counts_sha256":entry["raw_count_file"]["sha256"],
               "discovery_report":source.name if source is not None else "current_run",
               "holdout_key_indices":key_indices,"pairs_per_candidate_per_key":samples,
               "completed_pairs":0,"completed_cohorts":0,"planned_cohorts":len(candidates)*len(key_indices),
               "cohorts":[],"aggregate":[],"interval_method":"Wilson score, marginal 95%, descriptive",
               "family_testing_performed":False,"simultaneous_95_percent_coverage_claim":False,
               "holdout_reselection_performed":False}
    for candidate in candidates:
        rounds,bit,out = (candidate[name] for name in ("rounds","input_bit","output_bit"))
        total = 0
        for index in key_indices:
            ctx.deadline.check()
            key = research_key(index)
            blocks = plaintexts("holdout",rounds,bit,index,samples)
            fingerprint = hashlib.sha256(key+struct.pack("<III",rounds,bit,index)+b"".join(blocks)).hexdigest()
            cohort = {"rounds":rounds,"input_bit":bit,"output_bit":out,"key_index":index,
                      "count":0,"completed_pairs":0,"planned_pairs":samples,"input_sha256":fingerprint,"status":"running"}
            summary["cohorts"].append(cohort)
            for start in range(0,samples,4096):
                ctx.deadline.check()
                chunk = blocks[start:start+4096]
                doubled = [item for block in chunk for item in (block,xor_bit(block,bit))]
                outputs = ctx.driver.encrypt(key,rounds,doubled)
                flips = sum(((outputs[j][out//8] ^ outputs[j+1][out//8]) >> (out%8)) & 1 for j in range(0,len(outputs),2))
                cohort["count"] += flips
                cohort["completed_pairs"] += len(chunk)
                summary["completed_pairs"] += len(chunk)
                ctx.checkpoint("holdout",summary)
            cohort["rate"] = cohort["count"]/samples
            cohort["wilson95"] = list(wilson(cohort["count"],samples))
            cohort["status"] = "complete"
            total += cohort["count"]
            summary["completed_cohorts"] += 1
            ctx.checkpoint("holdout",summary)
        n = samples*len(key_indices)
        summary["aggregate"].append({"rounds":rounds,"input_bit":bit,"output_bit":out,
            "discovery_count":candidate["count"],"discovery_pairs":candidate["pairs"],
            "holdout_count":total,"holdout_pairs":n,"holdout_rate":total/n,
            "note":"pooled descriptive rate for these keys; intervals are reported separately per key"})
    if digest_json(candidates) != frozen:
        raise AssertionError("holdout changed the frozen candidate selection")
    return summary
