"""Specification oracle: Python integers, table S-box and hashlib SHAKE256.

This module neither imports nor executes the C implementation. Its fixed JSON
expectations are read-only, and are never regenerated from either implementation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

MASK = (1 << 32) - 1
SBOX = (12, 5, 6, 11, 9, 0, 10, 13, 3, 14, 15, 8, 4, 7, 1, 2)
SEED = 20261109


def rol(x, n):
    n %= 32
    x &= MASK
    return ((x << n) | (x >> ((32 - n) % 32))) & MASK


def ror(x, n):
    return rol(x, -n)


def substitute(x):
    return sum(SBOX[(x >> (4 * nibble)) & 15] << (4 * nibble)
               for nibble in range(8))


def linear(x):
    return x ^ rol(x, 3) ^ rol(x, 17)


def fs(x, k):
    return linear(substitute(x ^ k))


def fm(x, k):
    y = substitute(x ^ k)
    u = (y + rol(k, 9)) & MASK
    v = rol(y ^ k, 7)
    w = rol((u + v) & MASK, 11) ^ rol(y & rol(k, 3), 19)
    return linear(substitute(w ^ rol(k, 13)))


def round_keys(key):
    if len(key) != 32:
        raise ValueError("key must contain exactly 32 bytes")
    stream = hashlib.shake_256(b"Interlock-128/roundkeys\0" + key).digest(448)
    words = struct.unpack("<112I", stream)
    return tuple(words[i:i + 4] for i in range(0, 112, 4))


def forward(state, key):
    a, b, c, d = state
    a ^= fs(b, key[0])
    c ^= fm(d, key[1])
    b ^= fm(c, key[2])
    d ^= fs(a, key[3])
    return rol(c, 5), rol(a, 13), rol(d, 21), rol(b, 27)


def backward(state, key):
    o0, o1, o2, o3 = state
    a, b, c, d = ror(o1, 13), ror(o3, 27), ror(o0, 5), ror(o2, 21)
    d ^= fs(a, key[3])
    b ^= fm(c, key[2])
    c ^= fm(d, key[1])
    a ^= fs(b, key[0])
    return a, b, c, d


def _validate(block, schedule, rounds):
    if len(block) != 16 or len(schedule) != 28 or not 0 <= rounds <= 28:
        raise ValueError("16-byte block, 28-row schedule and 0..28 rounds required")


def encrypt_prefix(block, schedule, rounds=28):
    _validate(block, schedule, rounds)
    state = struct.unpack("<4I", block)
    for r in range(rounds):
        state = forward(state, schedule[r])
    return struct.pack("<4I", *state)


def decrypt_prefix(block, schedule, rounds=28):
    _validate(block, schedule, rounds)
    state = struct.unpack("<4I", block)
    for r in reversed(range(rounds)):
        state = backward(state, schedule[r])
    return struct.pack("<4I", *state)


def encryption_trace(block, schedule):
    _validate(block, schedule, 28)
    state = struct.unpack("<4I", block)
    result = [block]
    for subkey in schedule:
        state = forward(state, subkey)
        result.append(struct.pack("<4I", *state))
    return result


def test_case(index):
    data = hashlib.shake_256(b"Interlock-128/test\0" +
                            struct.pack("<II", SEED, index)).digest(48)
    return data[:32], data[32:]


def self_test(path):
    document = json.loads(Path(path).read_text())
    if hashlib.shake_256(b"").hexdigest(64) != document["shake256_empty_64"]:
        raise AssertionError("SHAKE256 fixed KAT mismatch")
    zero_schedule = round_keys(bytes(32))
    expected_words = tuple(int(x, 16) for x in document["zero_key_first_round_words"])
    if zero_schedule[0] != expected_words:
        raise AssertionError("first round-key KAT mismatch")
    for rounds, expected in document["zero_prefixes"].items():
        if encrypt_prefix(bytes(16), zero_schedule, int(rounds)).hex() != expected:
            raise AssertionError(f"{rounds}-round fixed KAT mismatch")
    for vector in document["vectors"]:
        key, plain, cipher = (bytes.fromhex(vector[x]) for x in ("key", "plaintext", "ciphertext"))
        schedule = round_keys(key)
        if encrypt_prefix(plain, schedule) != cipher or decrypt_prefix(cipher, schedule) != plain:
            raise AssertionError("full-round fixed KAT mismatch")
        for r, prefix in enumerate(encryption_trace(plain, schedule)):
            if decrypt_prefix(prefix, schedule, r) != plain:
                raise AssertionError(f"oracle prefix inverse mismatch: {r}")
    for x in (0, 1, MASK, 0x81234567):
        for n in (0, 1, 31, 32, 64):
            if ror(rol(x, n), n) != x:
                raise AssertionError("rotation edge mismatch")
    for bad in (b"", bytes(31), bytes(33)):
        try:
            round_keys(bad)
        except ValueError:
            continue
        raise AssertionError("invalid key accepted")
    for block, rounds in ((b"", 28), (bytes(15), 28), (bytes(17), 28), (bytes(16), -1), (bytes(16), 29)):
        for function in (encrypt_prefix, decrypt_prefix):
            try:
                function(block, zero_schedule, rounds)
            except ValueError:
                continue
            raise AssertionError("invalid prefix arguments accepted")
    return {"status": "passed", "fixed_full_vectors": len(document["vectors"]),
            "fixed_prefixes": len(document["zero_prefixes"]), "oracle_inverse_checks": 116,
            "shake_independence": "hashlib may share OpenSSL; no independent SHAKE claim"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vectors", type=Path, default=Path(__file__).with_name("vectors.json"))
    args = parser.parse_args()
    print(json.dumps(self_test(args.vectors), sort_keys=True))
