"""Only implemented experiments are registered; later commits add their stages."""
import hashlib
from common import oracle, plaintexts, research_key, stream


def harness(ctx):
    oracle.self_test(ctx.args.source/"tests"/"vectors.json")
    cases = 8 if ctx.profile == "smoke" else 32
    summary = {"completed_keys": 0, "planned_keys": cases, "deterministic_input_sha256": ""}
    fingerprint = hashlib.sha256()
    direct = b"Interlock-128/research\0discovery\0" + bytes.fromhex("f5283501040000001f00000000000000")
    expected = hashlib.shake_256(direct).digest(64)
    if stream("discovery", 4, 31, 0, 64) != expected:
        raise AssertionError("research domain/LE field framing mismatch")
    if stream("discovery",4,31,0,64) == stream("holdout",4,31,0,64):
        raise AssertionError("discovery/holdout streams are not separated")
    for index in range(cases):
        ctx.deadline.check()
        key = research_key(index)
        block = plaintexts("discovery",28,0,index,1)[0]
        if key != research_key(index) or block != plaintexts("discovery",28,0,index,1)[0]:
            raise AssertionError("input generation is not repeatable")
        fingerprint.update(key+block)
        schedule = oracle.round_keys(key)
        if ctx.driver.schedule(key) != schedule:
            raise AssertionError("C/oracle research schedule mismatch")
        cipher = ctx.driver.encrypt(key,28,[block])[0]
        if cipher != oracle.encrypt_prefix(block,schedule):
            raise AssertionError("C/oracle research encryption mismatch")
        if ctx.driver.query([("dec",28,key,cipher)])[0] != block:
            raise AssertionError("C research inverse mismatch")
        summary["completed_keys"] += 1
        summary["deterministic_input_sha256"] = fingerprint.hexdigest()
        ctx.checkpoint("harness",summary)
    return summary


STAGES = {"harness": harness}
from recovery import recovery
STAGES["recovery"] = recovery
