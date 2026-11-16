"""Known-plaintext recovery of k0/k3 from a single reduced round."""
import hashlib
import struct
from algebra import inverse_linear, inverse_substitute, verify_inverse
from common import oracle, plaintexts, research_key


def recover(plain, cipher):
    a,b,_,d = struct.unpack("<4I",plain)
    output = struct.unpack("<4I",cipher)
    updated_a = oracle.ror(output[1],13)
    updated_d = oracle.ror(output[2],21)
    k0 = b ^ inverse_substitute(inverse_linear(updated_a ^ a))
    k3 = updated_a ^ inverse_substitute(inverse_linear(updated_d ^ d))
    return k0,k3


def recovery(ctx):
    verify_inverse()
    if recover(bytes(16),bytes.fromhex("bc3f5fdced85606be7d9ad9f4bd37a1e")) != (0x634a205d,0x9c8022bf):
        raise AssertionError("one-round fixed KAT subkey recovery mismatch")
    count = 8 if ctx.profile == "smoke" else 1024
    summary = {"planned_keys":count,"completed_keys":0,"plaintext_pairs_per_key":2,
               "recovered_round_key_words":[0,3],"recovered_bits_per_key":64,
               "master_key_recovered":False,"full_28_round_attack":False,
               "inverse_basis_checks":32,"input_sha256":""}
    fingerprint = hashlib.sha256()
    for start in range(0,count,32):
        ctx.deadline.check()
        cases,queries = [],[]
        for index in range(start,min(count,start+32)):
            key = research_key(index)
            blocks = plaintexts("discovery",1,0,index,2)
            if blocks[0] == blocks[1]:
                raise AssertionError("recovery verification plaintexts are not distinct")
            cases.append((index,key,blocks))
            queries += [("keys",28,key,bytes(16))] + [("enc",1,key,block) for block in blocks]
        answers = ctx.driver.query(queries)
        for position,(index,key,blocks) in enumerate(cases):
            schedule = struct.unpack("<112I",answers[3*position])
            recovered = recover(blocks[0],answers[3*position+1])
            if recovered != (schedule[0],schedule[3]):
                raise AssertionError(f"subkey recovery failed for key {index}")
            if recover(blocks[1],answers[3*position+2]) != recovered:
                raise AssertionError(f"second-plaintext recovery failed for key {index}")
            a,b,_,d = struct.unpack("<4I",blocks[1])
            out = struct.unpack("<4I",answers[3*position+2])
            updated_a,updated_d = oracle.ror(out[1],13),oracle.ror(out[2],21)
            if a ^ oracle.fs(b,recovered[0]) != updated_a or d ^ oracle.fs(updated_a,recovered[1]) != updated_d:
                raise AssertionError("recovered subkeys do not satisfy independent FS relations")
            fingerprint.update(key+b"".join(blocks))
            if index == 0:
                summary["example"] = {"key_index":0,"k0":f"{recovered[0]:08x}","k3":f"{recovered[1]:08x}"}
            summary["completed_keys"] += 1
        summary["input_sha256"] = fingerprint.hexdigest()
        ctx.checkpoint("recovery",summary)
    summary["plaintext_ciphertext_pairs"] = 2*summary["completed_keys"]
    return summary
