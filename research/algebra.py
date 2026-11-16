"""Research-only exact GF(2) operations and inverse nibble substitution."""
from functools import lru_cache
from common import oracle

INVERSE_SBOX = (5,14,15,8,12,1,2,13,11,4,6,3,0,7,9,10)


def matrix_rows(columns, width):
    return [sum(((columns[c] >> r) & 1) << c for c in range(width)) for r in range(width)]


def rank(columns, width=32):
    rows = matrix_rows(columns,width)
    pivot = 0
    for column in range(width):
        found = next((j for j in range(pivot,width) if (rows[j] >> column) & 1),None)
        if found is None:
            continue
        rows[pivot],rows[found] = rows[found],rows[pivot]
        for j in range(width):
            if j != pivot and ((rows[j] >> column) & 1):
                rows[j] ^= rows[pivot]
        pivot += 1
    return pivot


def inverse_rows(columns, width=32):
    rows = [row | (1 << (width+r)) for r,row in enumerate(matrix_rows(columns,width))]
    for column in range(width):
        found = next((j for j in range(column,width) if (rows[j] >> column) & 1),None)
        if found is None:
            raise ValueError("singular GF(2) matrix")
        rows[column],rows[found] = rows[found],rows[column]
        for j in range(width):
            if j != column and ((rows[j] >> column) & 1):
                rows[j] ^= rows[column]
    mask = (1 << width)-1
    if any((row & mask) != 1 << r for r,row in enumerate(rows)):
        raise AssertionError("GF(2) elimination did not produce the identity")
    return tuple(row >> width for row in rows)


def apply_rows(rows, value):
    return sum(((row & value).bit_count() & 1) << bit for bit,row in enumerate(rows))


@lru_cache(maxsize=1)
def linear_inverse_rows():
    return inverse_rows([oracle.linear(1 << bit) for bit in range(32)])


def inverse_linear(value):
    return apply_rows(linear_inverse_rows(),value)


def inverse_substitute(value):
    return sum(INVERSE_SBOX[(value >> (4*j)) & 15] << (4*j) for j in range(8))


def verify_inverse():
    columns = [oracle.linear(1 << bit) for bit in range(32)]
    if rank(columns) != 32:
        raise AssertionError("L32 is not rank 32")
    for bit in range(32):
        basis = 1 << bit
        if inverse_linear(oracle.linear(basis)) != basis or oracle.linear(inverse_linear(basis)) != basis:
            raise AssertionError(f"L32 inverse basis failure {bit}")
    for value in range(16):
        if INVERSE_SBOX[oracle.SBOX[value]] != value or oracle.SBOX[INVERSE_SBOX[value]] != value:
            raise AssertionError("inverse S-box mismatch")
    try:
        inverse_rows([0]*32)
    except ValueError:
        pass
    else:
        raise AssertionError("singular matrix accepted")
    return 32
