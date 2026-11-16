from common import digest_json
from screening import flip_counts, registration, select_candidate, xor_bit


def require(condition, message):
    if not condition:
        raise AssertionError(message)


for bit in range(128):
    expected = bytearray(16); expected[bit//8] = 1 << (bit%8)
    require(xor_bit(bytes(16),bit) == bytes(expected),"serialized input bit order")
outputs = []
for bits in ((0,),(7,),(8,),(0,127)):
    changed = bytearray(16)
    for bit in bits:
        changed[bit//8] |= 1 << (bit%8)
    outputs += [bytes(16),bytes(changed)]
counts = flip_counts(outputs)
expected = [0]*128
for bit,count in ((0,2),(7,1),(8,1),(127,1)):
    expected[bit] = count
require(counts == expected,"serialized output counts")
require(flip_counts([bytes(16),bytes([255])*16]) == [1]*128,"all output bits")
row_a,row_b = [5]*128,[5]*128
row_a[0] = 10; row_b[1] = 0; row_b[2] = 0
candidate = select_candidate([(63,row_a),(0,row_b)],10)
require((candidate["input_bit"],candidate["output_bit"],candidate["score"]) == (0,1,10),"tie order")
require(select_candidate([(31,[5]*128),(0,[5]*128)],10)["input_bit"] == 0,"zero-score tie")
for profile in ("smoke","full"):
    require(digest_json(registration(profile)) == digest_json(registration(profile)),"registration reproducibility")
full = registration("full")
require(full["rounds"] == [4,8,16,28] and full["input_bits"] == list(range(128)),"full search space")
require(full["discovery"]["pairs_per_input_bit"] == 1024,"discovery size")
require(full["holdout"] == {"key_indices":[1,2,3,4],"pairs_per_candidate_per_key":32768},"holdout registration")
print("bit serialization, count conservation, deterministic tie order and registration passed")
