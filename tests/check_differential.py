"""Compare the private prefix driver and the public API driver with the oracle."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import time
from reference import (decrypt_prefix, encryption_trace, round_keys, self_test,
                       test_case, SEED)


def compare(executable, queries):
    result = subprocess.run([str(executable)], input="\n".join(q[1] for q in queries) + "\n",
                            text=True, capture_output=True, timeout=180, check=False)
    if result.returncode:
        raise AssertionError(f"{executable.name} exited {result.returncode}: {result.stderr[:1000]}")
    outputs = result.stdout.splitlines()
    if len(outputs) != len(queries):
        raise AssertionError(f"{executable.name}: {len(outputs)} lines for {len(queries)} queries")
    for (label, _, expected), output in zip(queries, outputs):
        if output != expected:
            raise AssertionError(f"{executable.name}: {label}: {output} != {expected}")


def main(args):
    started = time.monotonic()
    self_test(Path(__file__).with_name("vectors.json"))
    private, public = [], []
    fingerprint = hashlib.sha256()
    for index in range(args.cases):
        key, block = test_case(index)
        fingerprint.update(key + block)
        schedule = round_keys(key)
        states = encryption_trace(block, schedule)
        key_hex, plain_hex = key.hex(), block.hex()
        words = [x for row in schedule for x in row]
        private.append((f"case {index} full key schedule",
                        f"keys 28 {key_hex} {plain_hex}", struct.pack("<112I", *words).hex()))
        for rounds, output in enumerate(states):
            if decrypt_prefix(output, schedule, rounds) != block:
                raise AssertionError(f"oracle inverse failure, case {index}, rounds {rounds}")
            private.append((f"case {index} encrypt {rounds}",
                            f"enc {rounds} {key_hex} {plain_hex}", output.hex()))
            private.append((f"case {index} decrypt {rounds}",
                            f"dec {rounds} {key_hex} {output.hex()}", plain_hex))
        public.append((f"case {index} public encryption",
                       f"enc 28 {key_hex} {plain_hex}", states[-1].hex()))
        public.append((f"case {index} public decryption",
                       f"dec 28 {key_hex} {states[-1].hex()}", plain_hex))
    compare(args.prefix_runner, private)
    compare(args.vector_runner, public)
    invalid = [f"enc 29 {'00'*32} {'00'*16}", f"enc -1 {'00'*32} {'00'*16}",
               f"enc 184467440737095516160 {'00'*32} {'00'*16}",
               f"enc 28 {'00'*31} {'00'*16}", f"enc 28 {'00'*32} {'00'*16} extra"]
    for driver in (args.vector_runner, args.prefix_runner):
        result = subprocess.run([str(driver)], input="\n".join(invalid)+"\n", text=True,
                                capture_output=True, timeout=20, check=False)
        if result.returncode == 0 or result.stdout.splitlines() != ["ERR"]*len(invalid):
            raise AssertionError(f"{driver.name} accepted malformed protocol input")
    print(json.dumps({"status": "passed", "seed": SEED, "cases": args.cases,
                      "case_sha256": fingerprint.hexdigest(), "rounds": "0..28",
                      "schedule_comparisons": args.cases,
                      "prefix_encrypt_comparisons": 29*args.cases,
                      "prefix_decrypt_comparisons": 29*args.cases,
                      "public_api_comparisons": len(public),
                      "elapsed_seconds": round(time.monotonic()-started, 3)}, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix-runner", type=Path, required=True)
    parser.add_argument("--vector-runner", type=Path, required=True)
    parser.add_argument("--cases", type=int, default=1024)
    args = parser.parse_args()
    if not 1 <= args.cases <= 1024:
        parser.error("cases must be 1..1024; the acceptance target uses all 1024")
    main(args)
