"""Exhaustive PRESENT component calculations and exact L32 matrix checks."""
import hashlib
import struct
from algebra import linear_inverse_rows, rank, verify_inverse
from common import oracle


def component_properties():
    if sorted(oracle.SBOX) != list(range(16)):
        raise AssertionError("S-box is not a permutation")
    ddt = [[0]*16 for _ in range(16)]
    lat = [[0]*16 for _ in range(16)]
    for difference in range(16):
        for x in range(16):
            ddt[difference][oracle.SBOX[x] ^ oracle.SBOX[x ^ difference]] += 1
    for a in range(16):
        for b in range(16):
            lat[a][b] = sum(1 if ((a & x).bit_count() ^ (b & oracle.SBOX[x]).bit_count()) & 1 == 0 else -1
                            for x in range(16))
    differential_max = max(ddt[a][b] for a in range(1,16) for b in range(16))
    walsh_max = max(abs(lat[a][b]) for a in range(1,16) for b in range(1,16))
    if any(sum(row) != 16 for row in ddt) or ddt[0] != [16]+[0]*15:
        raise AssertionError("DDT counting identities failed")
    for b in range(16):
        if sum(lat[a][b]**2 for a in range(16)) != 256:
            raise AssertionError("Walsh Parseval identity failed")
    coordinates = []
    for bit in range(4):
        coefficients = [(oracle.SBOX[x] >> bit) & 1 for x in range(16)]
        for variable in range(4):
            for mask in range(16):
                if mask & (1 << variable):
                    coefficients[mask] ^= coefficients[mask ^ (1 << variable)]
        terms = [mask for mask,value in enumerate(coefficients) if value]
        degree = max((mask.bit_count() for mask in terms),default=0)
        for x in range(16):
            evaluated = sum(1 for mask in terms if x & mask == mask) & 1
            if evaluated != (oracle.SBOX[x] >> bit) & 1:
                raise AssertionError("ANF truth-table reconstruction failed")
        coordinates.append({"output_bit_lsb_first":bit,"degree":degree,"anf_monomial_masks":terms})
    columns = [oracle.linear(1 << bit) for bit in range(32)]
    matrix_rank = rank(columns)
    verify_inverse()
    inverse = linear_inverse_rows()
    degrees = [c["degree"] for c in coordinates]
    if (differential_max,walsh_max,degrees,matrix_rank) != (4,8,[2,3,3,3],32):
        raise AssertionError("exact component properties differ from the fixed specification")
    return {"exact":True,"sbox_inputs_exhausted":16,"ddt":ddt,"walsh_lat":lat,
            "ddt_nonzero_input_row_max":differential_max,"max_differential_probability":"4/16",
            "walsh_nonzero_masks_max_absolute":walsh_max,"max_absolute_correlation":"8/16",
            "coordinate_degrees_lsb_first":degrees,"coordinates":coordinates,"l32_rank":matrix_rank,
            "l32_columns":[f"{x:08x}" for x in columns],"l32_inverse_rows":[f"{x:08x}" for x in inverse],
            "inverse_rows_sha256":hashlib.sha256(struct.pack("<32I",*inverse)).hexdigest(),
            "scope":"component properties only; not a 28-round security bound"}


def components(ctx):
    ctx.deadline.check()
    result = component_properties()
    ctx.checkpoint("components",result)
    return result
