"""Wilson boundary/symmetry checks and a published NIST rounded example."""
import math
import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
from statistics import NormalDist
from statistics_ci import wilson
from common import ResearchFailure, digest_json
from holdout import validate_discovery
from screening import registration, select_candidate


def require(condition,message):
    if not condition:
        raise AssertionError(message)


z = NormalDist().inv_cdf(0.975)
lo,hi = wilson(0,1)
require(abs(lo) < 1e-15 and abs(hi-z*z/(1+z*z)) < 1e-15,"n=1 Wilson boundary")
lo,hi = wilson(50,100)
radius = z/(2*math.sqrt(100+z*z))
require(abs(lo-(0.5-radius)) < 1e-15 and abs(hi-(0.5+radius)) < 1e-15,"balanced Wilson identity")
for n in (1,2,10,100,32768):
    for c in (0,n//2,n):
        lo,hi = wilson(c,n)
        complement = wilson(n-c,n)
        require(0 <= lo <= c/n <= hi <= 1,"Wilson range")
        require(abs(lo-(1-complement[1])) < 1e-12 and abs(hi-(1-complement[0])) < 1e-12,"Wilson complement symmetry")
require(abs(wilson(26,200,0.90)[0]-0.09577) < 0.00002,"NIST rounded one-sided95/two-sided90 example")
for c,n,confidence in ((0,0,0.95),(-1,10,0.95),(11,10,0.95),(1,10,0),(1,10,1)):
    try:
        wilson(c,n,confidence)
    except ValueError:
        continue
    raise AssertionError("invalid Wilson arguments accepted")
print("Wilson boundaries, symmetry, balanced identity and NIST reference passed")

plan = registration("smoke")
samples = plan["discovery"]["pairs_per_input_bit"]
rows = [{"rounds":r,"input_bit":bit,"pairs":samples,"counts":[samples//2]*128}
        for r in plan["rounds"] for bit in plan["input_bits"]]
raw = "".join(json.dumps(row,sort_keys=True,separators=(",",":"))+"\n" for row in rows).encode()
names = ("research/common.py","research/screening.py","tests/reference.py","tests/vectors.json","tests/vector_runner.c")
provenance = {"core_source_sha256":{"fixture":"a"*64},"driver_sha256":"b"*64,
              "source_sha256":{name:"c"*64 for name in names}}
data = {"registration":plan,"registration_sha256":digest_json(plan),
        "raw_count_file":{"name":"counts.jsonl","sha256":hashlib.sha256(raw).hexdigest()},
        "rounds":{},"selected_candidates":[]}
for rounds in plan["rounds"]:
    current = [(row["input_bit"],row["counts"]) for row in rows if row["rounds"] == rounds]
    digest = hashlib.sha256()
    for bit,counts in current:
        digest.update(struct.pack("<II",rounds,bit)+struct.pack("<128I",*counts))
    data["rounds"][str(rounds)] = {"count_matrix_sha256":digest.hexdigest()}
    candidate = select_candidate(current,samples); candidate["rounds"] = rounds
    data["selected_candidates"].append(candidate)
report = {"profile":"smoke","provenance":provenance,"experiments":{"discovery":{"status":"complete","data":data}}}
with tempfile.TemporaryDirectory() as folder:
    path = Path(folder)/"counts.jsonl"; path.write_bytes(raw)
    candidates,_ = validate_discovery(report,provenance,"smoke",path)
    require(len(candidates)==2 and all(c["input_bit"]==0 and c["output_bit"]==0 for c in candidates),"cache selection")
    variants = []
    changed = copy.deepcopy(report); changed["experiments"]["discovery"]["data"]["selected_candidates"][0]["output_bit"] = 1
    variants.append(changed)
    changed = copy.deepcopy(report); changed["provenance"]["driver_sha256"] = "d"*64
    variants.append(changed)
    changed = copy.deepcopy(report); changed["experiments"]["discovery"]["data"]["registration_sha256"] = "e"*64
    variants.append(changed)
    for changed in variants:
        try:
            validate_discovery(changed,provenance,"smoke",path)
        except ResearchFailure:
            continue
        raise AssertionError("invalid discovery cache accepted")
    path.write_bytes(raw+b" ")
    try:
        validate_discovery(report,provenance,"smoke",path)
    except ResearchFailure:
        pass
    else:
        raise AssertionError("corrupted raw counts accepted")
print("Frozen-candidate, binary, registration and raw-count cache rejection passed")
