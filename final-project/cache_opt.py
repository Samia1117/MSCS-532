# cache_opt.py
# data locality demo
# three tests: matrix multiply access patterns, AoS vs SoA, numpy row/col
# based on Azad et al. 2023 (data locality = most common HPC perf fix)

import time
import random
import numpy as np


def make_matrix(n):
    return [[random.random() for _ in range(n)] for _ in range(n)]  # n x n list-of-lists, row-major in memory


# matrix multiply

def naive_matmul(A, B):
    # standard ijk order - B accessed column-wise, cache unfriendly
    n = len(A)
    C = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            for k in range(n):
                C[i][j] += A[i][k] * B[k][j]  # B[k][j]: k varies -> stride n, likely cache miss
    return C


def transposed_matmul(A, B):
    # transpose B first so inner loop is row-sequential
    n = len(A)
    Bt = [[B[j][i] for j in range(n)] for i in range(n)]  # Bt[j][k] = B[k][j], paid once O(n^2)
    C = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            s = 0.0
            for k in range(n):
                s += A[i][k] * Bt[j][k]  # Bt[j][k]: k varies -> sequential, cache friendly
            C[i][j] = s
    return C


def blocked_matmul(A, B, block=16):
    # tiled - working set fits in L1
    n = len(A)
    C = [[0.0] * n for _ in range(n)]
    for ii in range(0, n, block):       # step by tile size, not 1
        for jj in range(0, n, block):
            for kk in range(0, n, block):
                for i in range(ii, min(ii + block, n)):  # clamp to matrix edge
                    for j in range(jj, min(jj + block, n)):
                        s = 0.0
                        for k in range(kk, min(kk + block, n)):
                            s += A[i][k] * B[k][j]
                        C[i][j] += s
    return C


# AoS vs SoA

def make_aos(n):
    random.seed(7)
    return [{'x': random.random(), 'y': random.random(),
             'z': random.random(), 'mass': random.random()} for _ in range(n)]  # all 4 fields interleaved per particle


def make_soa(n):
    random.seed(7)
    return {
        'x':    [random.random() for _ in range(n)],
        'y':    [random.random() for _ in range(n)],
        'z':    [random.random() for _ in range(n)],
        'mass': [random.random() for _ in range(n)],  # each field contiguous; mass array fits in cache alone
    }


def ke_aos(particles):
    return sum(0.5 * p['mass'] for p in particles)  # loads x,y,z,mass per particle even though only mass is used


def ke_soa(data):
    return sum(0.5 * m for m in data['mass'])  # only the mass list is touched, no wasted loads


#numpy row vs column ---

def row_sum(A):
    return [float(A[i, :].sum()) for i in range(A.shape[0])]  # A[i,:] is contiguous in C-order


def col_sum(A):
    return [float(A[:, j].sum()) for j in range(A.shape[1])]  # A[:,j] skips n floats between elements


# timing helper

def timeit(fn, *args):
    best = float('inf')
    for _ in range(3):
        t0 = time.perf_counter()
        fn(*args)
        best = min(best, time.perf_counter() - t0)  # best-of-3 reduces noise from OS scheduling
    return best


if __name__ == '__main__':
    random.seed(42)

    print("=== matmul ===")
    for n in [32, 48, 64]:
        A = make_matrix(n)
        B = make_matrix(n)
        tn = timeit(naive_matmul, A, B)
        tt = timeit(transposed_matmul, A, B)
        tb = timeit(blocked_matmul, A, B)
        print(f"n={n}  naive={tn:.4f}s  transposed={tt:.4f}s ({tn/tt:.2f}x)  blocked={tb:.4f}s ({tn/tb:.2f}x)")

    print("\n=== AoS vs SoA ===")
    for n in [100_000, 500_000]:
        aos = make_aos(n)
        soa = make_soa(n)
        ta = timeit(ke_aos, aos)
        ts = timeit(ke_soa, soa)
        print(f"n={n}  aos={ta*1000:.2f}ms  soa={ts*1000:.2f}ms  speedup={ta/ts:.2f}x")

    print("\n=== numpy row vs col ===")
    for n in [500, 1000, 2000]:
        A = np.random.default_rng(0).random((n, n))
        tr = timeit(row_sum, A)
        tc = timeit(col_sum, A)
        print(f"n={n}  row={tr*1000:.2f}ms  col={tc*1000:.2f}ms  speedup={tc/tr:.2f}x")
