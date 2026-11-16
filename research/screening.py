"""Pre-registered single-input/single-output-bit differential screening."""
import hashlib
import json
import struct
from common import SEED, digest_json, plaintexts, research_key


def registration(profile):
    full = profile == "full"
    return {"version":1,"seed":SEED,"profile":profile,
            "rounds":[4,8,16,28] if full else [4,28],
            "input_bits":list(range(128)) if full else [0,31,63,95,127],"output_bits":128,
            "discovery":{"key_index":0,"pairs_per_input_bit":1024 if full else 128},
            "holdout":{"key_indices":[1,2,3,4] if full else [1],"pairs_per_candidate_per_key":32768 if full else 256},
            "bit_order":"serialized byte b//8, LSB bit b%8",
            "selection":{"score":"abs(2*count-N)","tie_break":["input_bit ascending","output_bit ascending"],
                         "candidates_per_round":1},
            "statistics":"descriptive counts and independent holdouts; no post-selection discovery p-values"}


def xor_bit(block, bit):
    if len(block) != 16 or not 0 <= bit < 128:
        raise ValueError("16-byte block and serialized bit 0..127 required")
    return (int.from_bytes(block,"little") ^ (1 << bit)).to_bytes(16,"little")


def flip_counts(outputs):
    if len(outputs) % 2:
        raise ValueError("paired outputs required")
    counts = [0]*128
    for j in range(0,len(outputs),2):
        if len(outputs[j]) != 16 or len(outputs[j+1]) != 16:
            raise ValueError("16-byte outputs required")
        difference = int.from_bytes(outputs[j],"little") ^ int.from_bytes(outputs[j+1],"little")
        while difference:
            low = difference & -difference
            counts[low.bit_length()-1] += 1
            difference ^= low
    return counts


def select_candidate(rows, samples):
    if samples <= 0 or not rows:
        raise ValueError("nonempty positive-size experiment required")
    best = None
    for bit,counts in rows:
        if not 0 <= bit < 128 or len(counts) != 128 or any(not 0 <= c <= samples for c in counts):
            raise ValueError("invalid flip-count row")
        for output,count in enumerate(counts):
            candidate = {"input_bit":bit,"output_bit":output,"count":count,"pairs":samples,
                         "rate":count/samples,"score":abs(2*count-samples)}
            order = (-candidate["score"],bit,output)
            if best is None or order < best[0]:
                best = order,candidate
    return best[1]


def discovery(ctx):
    plan = registration(ctx.profile)
    samples = plan["discovery"]["pairs_per_input_bit"]
    key = research_key(0)
    summary = {"registration":plan,"registration_sha256":digest_json(plan),
               "completed_rows":0,"planned_rows":len(plan["rounds"])*len(plan["input_bits"]),
               "completed_pairs":0,"rounds":{},"selected_candidates":[],
               "discovery_key_index":0,"holdout_data_used_for_selection":False}
    raw_path = ctx.args.output.with_name(ctx.args.output.stem+"-counts.jsonl")
    raw_path.parent.mkdir(parents=True,exist_ok=True)
    raw_digest = hashlib.sha256()
    with raw_path.open("w",encoding="utf-8",newline="\n") as raw:
        for rounds in plan["rounds"]:
            rows = []
            input_digest = hashlib.sha256(key)
            round_digest = hashlib.sha256()
            for bit in plan["input_bits"]:
                ctx.deadline.check()
                blocks = plaintexts("discovery",rounds,bit,0,samples)
                doubled = [item for block in blocks for item in (block,xor_bit(block,bit))]
                counts = flip_counts(ctx.driver.encrypt(key,rounds,doubled))
                rows.append((bit,counts))
                input_digest.update(struct.pack("<II",rounds,bit)+b"".join(blocks))
                round_digest.update(struct.pack("<II",rounds,bit)+struct.pack("<128I",*counts))
                row = {"rounds":rounds,"input_bit":bit,"pairs":samples,"counts":counts}
                line = json.dumps(row,sort_keys=True,separators=(",",":"))+"\n"
                raw.write(line); raw.flush(); raw_digest.update(line.encode())
                candidate = select_candidate(rows,samples)
                summary["completed_rows"] += 1
                summary["completed_pairs"] += samples
                summary["rounds"][str(rounds)] = {
                    "completed_input_bits":len(rows),"planned_input_bits":len(plan["input_bits"]),
                    "count_matrix_sha256":round_digest.hexdigest(),"input_sha256":input_digest.hexdigest(),
                    "selection_comparisons":len(rows)*128,"best_so_far":candidate}
                summary["raw_count_file"] = {"name":raw_path.name,"sha256":raw_digest.hexdigest()}
                ctx.checkpoint("discovery",summary)
            selected = select_candidate(rows,samples)
            selected["rounds"] = rounds
            summary["selected_candidates"].append(selected)
            summary["rounds"][str(rounds)]["selected_input_flip_counts"] = next(counts for bit,counts in rows if bit == selected["input_bit"])
            ctx.checkpoint("discovery",summary)
    return summary
