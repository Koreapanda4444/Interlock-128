"""Exact support bounds and empirical C reproduction of 2R/3R constraints."""
import hashlib
import struct
from common import oracle, plaintexts, research_key

TWO_ROUND_VALUES = (0x04004801,0x6c001800,0x94006801,0xfc003800)
THREE_ROUND_ZERO = 0x001f001f


def nibble_cover(mask):
    return sum((15 << (4*j)) for j in range(8) if mask & (15 << (4*j)))


def support_upper(mask):
    value = nibble_cover(mask)
    return value | oracle.rol(value,3) | oracle.rol(value,17)


def exact_support():
    differences = sorted({oracle.SBOX[x] ^ oracle.SBOX[x ^ 1] for x in range(16)})
    values = sorted({oracle.rol(oracle.linear(x),26) for x in differences})
    w0 = oracle.rol(support_upper(1),26)
    w1 = oracle.rol(support_upper(1 << 13),13)
    support = oracle.rol(w0 | support_upper(w1),13)
    zero = (~support) & oracle.MASK
    if differences != [3,7,9,13] or values != list(TWO_ROUND_VALUES):
        raise AssertionError("2R exact difference-set mismatch")
    if (w0,w1,support,zero) != (0xfc007801,0xfe003c00,0xffe0ffe0,THREE_ROUND_ZERO):
        raise AssertionError("3R exact support-bound mismatch")
    return {"sbox_input_difference_1":differences,"two_round_values":[f"{v:08x}" for v in values],
            "w0":f"{w0:08x}","w1":f"{w1:08x}","support":f"{support:08x}",
            "forced_zero":f"{zero:08x}","forced_zero_bits":zero.bit_count(),
            "support_is_upper_bound":True,
            "ideal_random_permutation_single_pair_probabilities":{
                "two_round":"4*2^96/(2^128-1)","three_round":"(2^118-1)/(2^128-1)"}}


def constraints(ctx):
    count,pairs = (8,32) if ctx.profile == "smoke" else (128,128)
    summary = {"exact":exact_support(),"planned_keys":count,"pairs_per_key_per_round":pairs,
               "completed_keys":0,"completed_pairs_by_round":{"2":0,"3":0},
               "input_word_difference":[1,0,0,0],"two_round_counts":{f"{x:08x}":0 for x in TWO_ROUND_VALUES},
               "three_round_violations":0,"input_sha256":"","full_28_round_attack":False}
    fingerprint = hashlib.sha256()
    for index in range(count):
        key = research_key(index)
        for rounds in (2,3):
            ctx.deadline.check()
            blocks = plaintexts("discovery",rounds,0,index,pairs)
            doubled = [item for block in blocks for item in (block,bytes([block[0] ^ 1])+block[1:])]
            outputs = ctx.driver.encrypt(key,rounds,doubled)
            for j,block in enumerate(blocks):
                left,right = outputs[2*j],outputs[2*j+1]
                difference = tuple(a ^ b for a,b in zip(struct.unpack("<4I",left),struct.unpack("<4I",right)))
                violated = difference[0] not in TWO_ROUND_VALUES if rounds == 2 else bool(difference[1] & THREE_ROUND_ZERO)
                if violated:
                    summary["counterexample"] = {"rounds":rounds,"key_index":index,"key":key.hex(),
                        "plaintext":block.hex(),"paired_plaintext":doubled[2*j+1].hex(),
                        "left_output":left.hex(),"right_output":right.hex()}
                    ctx.checkpoint("constraints",summary)
                    raise AssertionError(f"exact {rounds}R constraint counterexample at key {index}, pair {j}")
                if rounds == 2:
                    summary["two_round_counts"][f"{difference[0]:08x}"] += 1
                summary["completed_pairs_by_round"][str(rounds)] += 1
                fingerprint.update(key+struct.pack("<I",rounds)+block+doubled[2*j+1])
            summary["input_sha256"] = fingerprint.hexdigest()
            ctx.checkpoint("constraints",summary)
        summary["completed_keys"] += 1
        ctx.checkpoint("constraints",summary)
    return summary
