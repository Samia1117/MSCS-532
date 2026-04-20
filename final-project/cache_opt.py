# cache_opt_final.py
# data locality optimization demo
# based on Azad et al. 2023 - data locality is the most common HPC perf fix (21% of all fixes)
#
# three parts:
#   1. matrix multiply: naive vs transposed vs cache-blocked
#   2. AoS vs SoA (particle kinetic energy)
#   3. numpy row-major vs column-major access

import os
import csv
import time
import random
import math

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)

REPEATS = 3  # best-of-N to reduce noise from OS scheduling


# helpers

def timeit(fn, *args, repeats=REPEATS):
    best = float('inf')
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn(*args)
        best = min(best, time.perf_counter() - t0)
    return best


def make_matrix(n):
    return [[random.random() for _ in range(n)] for _ in range(n)]  # n x n list-of-lists, row-major in memory


# Part 1 - matrix multiply
# all three use the same list-of-lists so the only difference is access order

def naive_matmul(A, B):
    n = len(A)
    C = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            for k in range(n):
                C[i][j] += A[i][k] * B[k][j]  # B[k][j]: k varies -> stride n, likely cache miss
    return C


def transposed_matmul(A, B):
    n = len(A)
    Bt = [[B[j][i] for j in range(n)] for i in range(n)]  # transpose B once, O(n^2) paid upfront
    C = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            s = 0.0
            for k in range(n):
                s += A[i][k] * Bt[j][k]  # Bt[j][k]: k varies -> sequential, cache friendly
            C[i][j] = s
    return C


def blocked_matmul(A, B, block=16):
    # block=16 -> each tile is 16*16*8 = 2 KB, fits in L1
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


def run_matmul_benchmark(sizes):
    print("=== Part 1: Matrix Multiplication ===")
    print(f"{'n':>5}  {'naive (s)':>10}  {'transposed (s)':>15}  {'blocked (s)':>12}  {'speedup-T':>10}  {'speedup-B':>10}")
    print(f"{'':->5}  {'':->10}  {'':->15}  {'':->12}  {'':->10}  {'':->10}")

    results = []
    for n in sizes:
        random.seed(42)
        A = make_matrix(n)
        B = make_matrix(n)

        t_n = timeit(naive_matmul, A, B)
        t_t = timeit(transposed_matmul, A, B)
        t_b = timeit(blocked_matmul, A, B)

        sp_t = t_n / t_t
        sp_b = t_n / t_b
        results.append((n, t_n, t_t, t_b, sp_t, sp_b))
        print(f"{n:>5}  {t_n:>10.4f}  {t_t:>15.4f}  {t_b:>12.4f}  {sp_t:>9.2f}x  {sp_b:>9.2f}x")

    csv_path = os.path.join(RESULTS_DIR, 'matmul.csv')
    with open(csv_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['n', 'naive_s', 'transposed_s', 'blocked_s', 'speedup_T', 'speedup_B'])
        w.writerows(results)
    print(f"saved: {csv_path}")

    print()
    return results


# Part 2 - AoS vs SoA
# AoS: each particle is a dict with x, y, z, mass interleaved
# SoA: each field is its own list, so mass is contiguous
# when we only need mass, SoA loads only that array; AoS wastes 75% of each cache line

def make_aos(n):
    random.seed(7)
    return [
        {'x': random.random(), 'y': random.random(),
         'z': random.random(), 'mass': random.random()}  # all 4 fields interleaved per particle
        for _ in range(n)
    ]


def make_soa(n):
    random.seed(7)
    return {
        'x':    [random.random() for _ in range(n)],
        'y':    [random.random() for _ in range(n)],
        'z':    [random.random() for _ in range(n)],
        'mass': [random.random() for _ in range(n)],  # each field contiguous; mass array fits in cache alone
    }


def kinetic_energy_aos(particles, v=1.0):
    return sum(0.5 * p['mass'] * v * v for p in particles)  # loads x,y,z,mass per particle even though only mass is used


def kinetic_energy_soa(data, v=1.0):
    return sum(0.5 * m * v * v for m in data['mass'])  # only the mass list is touched, no wasted loads


def run_aos_soa_benchmark(sizes):
    print("=== Part 2: AoS vs SoA (kinetic energy sum) ===")
    print(f"{'N':>8}  {'AoS (ms)':>10}  {'SoA (ms)':>10}  {'speedup':>8}")
    print(f"{'':->8}  {'':->10}  {'':->10}  {'':->8}")

    results = []
    for n in sizes:
        aos = make_aos(n)
        soa = make_soa(n)

        t_aos = timeit(kinetic_energy_aos, aos)
        t_soa = timeit(kinetic_energy_soa, soa)
        sp = t_aos / t_soa
        results.append((n, t_aos * 1000, t_soa * 1000, sp))
        print(f"{n:>8}  {t_aos*1000:>10.3f}  {t_soa*1000:>10.3f}  {sp:>7.2f}x")

    csv_path = os.path.join(RESULTS_DIR, 'aos_soa.csv')
    with open(csv_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['n', 'aos_ms', 'soa_ms', 'speedup'])
        w.writerows(results)
    print(f"saved: {csv_path}")

    print()
    return results


# Part 3 - numpy row vs column access
# numpy C-order arrays are row-major; row access is stride 1, column access is stride n

def np_row_access(A):
    return [float(A[i, :].sum()) for i in range(A.shape[0])]  # A[i,:] is contiguous in C-order


def np_col_access(A):
    return [float(A[:, j].sum()) for j in range(A.shape[1])]  # A[:,j] skips n floats between elements


def run_numpy_benchmark(sizes):
    print("=== Part 3: NumPy row vs column access ===")
    print(f"{'n':>6}  {'row (ms)':>10}  {'col (ms)':>10}  {'speedup':>8}")
    print(f"{'':->6}  {'':->10}  {'':->10}  {'':->8}")

    results = []
    for n in sizes:
        rng = np.random.default_rng(0)
        A = rng.random((n, n))  # C-order (row-major) by default

        t_row = timeit(np_row_access, A)
        t_col = timeit(np_col_access, A)
        sp = t_col / t_row
        results.append((n, t_row * 1000, t_col * 1000, sp))
        print(f"{n:>6}  {t_row*1000:>10.3f}  {t_col*1000:>10.3f}  {sp:>7.2f}x")

    csv_path = os.path.join(RESULTS_DIR, 'numpy_access.csv')
    with open(csv_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['n', 'row_ms', 'col_ms', 'speedup'])
        w.writerows(results)
    print(f"saved: {csv_path}")

    print()
    return results


# block size sweep

def run_block_sweep(n=80):
    print(f"=== Block size sweep (n={n}) ===")
    random.seed(0)
    A = make_matrix(n)
    B = make_matrix(n)

    block_sizes = [4, 8, 16, 32, n]
    results = []
    for bs in block_sizes:
        t = timeit(blocked_matmul, A, B, bs)
        results.append((bs, t))
        label = f"(=n)" if bs == n else ""
        print(f"  block={bs:>3}{label:<5}  {t:.4f}s")

    csv_path = os.path.join(RESULTS_DIR, 'block_sweep.csv')
    with open(csv_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['block_size', 'time_s'])
        w.writerows(results)
    print(f"saved: {csv_path}")

    print()
    return results


# charts

def plot_matmul(results):
    ns    = [r[0] for r in results]
    naive = [r[1] for r in results]
    trans = [r[2] for r in results]
    block = [r[3] for r in results]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    # absolute times
    ax = axes[0]
    ax.plot(ns, naive, 'o-', label='Naive', color='#c0392b')
    ax.plot(ns, trans, 's-', label='Transposed', color='#2980b9')
    ax.plot(ns, block, '^-', label='Blocked (tile=16)', color='#27ae60')
    ax.set_xlabel('Matrix size n')
    ax.set_ylabel('Time (seconds)')
    ax.set_title('Matrix Multiply: Absolute Time')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # speedup over naive
    ax = axes[1]
    sp_t = [r[4] for r in results]
    sp_b = [r[5] for r in results]
    x = range(len(ns))
    w = 0.35
    bars1 = ax.bar([i - w/2 for i in x], sp_t, w, label='Transposed', color='#2980b9')
    bars2 = ax.bar([i + w/2 for i in x], sp_b, w, label='Blocked', color='#27ae60')
    ax.axhline(1.0, color='#c0392b', linestyle='--', label='Baseline (naive)')
    ax.set_xticks(list(x))
    ax.set_xticklabels([str(n) for n in ns])
    ax.set_xlabel('Matrix size n')
    ax.set_ylabel('Speedup over naive')
    ax.set_title('Matrix Multiply: Speedup')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    fig.tight_layout()
    path = os.path.join(RESULTS_DIR, 'matmul_benchmark.png')
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"saved: {path}")


def plot_aos_soa(results):
    ns    = [r[0] for r in results]
    t_aos = [r[1] for r in results]
    t_soa = [r[2] for r in results]
    sp    = [r[3] for r in results]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    ax = axes[0]
    ax.plot(ns, t_aos, 'o-', label='AoS', color='#c0392b')
    ax.plot(ns, t_soa, 's-', label='SoA', color='#27ae60')
    ax.set_xlabel('Number of particles N')
    ax.set_ylabel('Time (ms)')
    ax.set_title('AoS vs SoA: Absolute Time')
    ax.legend()
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.plot(ns, sp, 'D-', color='#8e44ad')
    ax.axhline(1.0, color='grey', linestyle='--')
    ax.set_xlabel('Number of particles N')
    ax.set_ylabel('Speedup (AoS time / SoA time)')
    ax.set_title('AoS vs SoA: Speedup')
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    path = os.path.join(RESULTS_DIR, 'aos_soa_benchmark.png')
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"saved: {path}")


def plot_numpy(results):
    ns    = [r[0] for r in results]
    t_row = [r[1] for r in results]
    t_col = [r[2] for r in results]
    sp    = [r[3] for r in results]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    ax = axes[0]
    ax.plot(ns, t_row, 'o-', label='Row access (cache friendly)', color='#27ae60')
    ax.plot(ns, t_col, 's-', label='Column access (cache unfriendly)', color='#c0392b')
    ax.set_xlabel('Array size n (n x n matrix)')
    ax.set_ylabel('Time (ms)')
    ax.set_title('NumPy: Row vs Column Access')
    ax.legend()
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.plot(ns, sp, 'D-', color='#2980b9')
    ax.axhline(1.0, color='grey', linestyle='--')
    ax.set_xlabel('Array size n')
    ax.set_ylabel('Speedup (col time / row time)')
    ax.set_title('NumPy Access Pattern Speedup')
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    path = os.path.join(RESULTS_DIR, 'numpy_access_benchmark.png')
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"saved: {path}")


def plot_block_sweep(sweep_results, n):
    block_sizes = [r[0] for r in sweep_results]
    times       = [r[1] for r in sweep_results]
    labels      = [str(b) if b != n else f'{b}\n(=n)' for b in block_sizes]

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(labels, times, color='#2980b9', edgecolor='white')
    ax.set_xlabel('Block (tile) size')
    ax.set_ylabel('Time (seconds)')
    ax.set_title(f'Block Size Sweep (n={n})')
    ax.grid(True, alpha=0.3, axis='y')
    fig.tight_layout()
    path = os.path.join(RESULTS_DIR, 'block_sweep.png')
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"saved: {path}")


def plot_cache_hierarchy():
    # diagram of memory hierarchy levels - widening rectangles = increasing size and latency
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    levels = [
        (4.5, 8.5, 1.5, 0.7, '#e74c3c', 'Registers\n~1 ns'),
        (3.5, 7.0, 3.0, 0.8, '#e67e22', 'L1 Cache  ~32 KB\n~4 cycles'),
        (2.5, 5.5, 5.0, 0.9, '#f1c40f', 'L2 Cache  ~256 KB\n~12 cycles'),
        (1.5, 4.0, 7.0, 0.9, '#2ecc71', 'L3 Cache  ~8 MB\n~40 cycles'),
        (0.5, 2.3, 9.0, 1.0, '#3498db', 'Main Memory (RAM)  GBs\n~200 cycles'),
    ]

    for x, y, w, h, color, label in levels:
        rect = plt.Rectangle((x, y), w, h, facecolor=color, edgecolor='white', linewidth=1.5)
        ax.add_patch(rect)
        ax.text(5, y + h / 2, label, ha='center', va='center', fontsize=10,
                color='white', fontweight='bold')

    ax.text(5, 9.6, 'Memory Hierarchy (typical x86 CPU)', ha='center',
            fontsize=12, fontweight='bold')
    ax.annotate('', xy=(5, 2.2), xytext=(5, 1.5),
                arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))

    fig.tight_layout()
    path = os.path.join(RESULTS_DIR, 'cache_hierarchy.png')
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"saved: {path}")


def plot_access_pattern():
    # side-by-side grid showing row-sequential vs column-skip access order
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))

    for ax, title, pattern in [
        (axes[0], 'Row-major access (cache friendly)', 'row'),
        (axes[1], 'Column access (cache unfriendly)',  'col'),
    ]:
        n = 6
        grid = np.zeros((n, n))
        order = []
        if pattern == 'row':
            for i in range(n):
                for k in range(n):
                    order.append((i, k))
        else:
            for j in range(n):
                for k in range(n):
                    order.append((k, j))

        ax.set_xlim(-0.5, n - 0.5)
        ax.set_ylim(-0.5, n - 0.5)
        ax.set_aspect('equal')
        ax.invert_yaxis()

        for r in range(n):
            for c in range(n):
                color = '#ecf0f1'
                rect = plt.Rectangle((c - 0.5, r - 0.5), 1, 1,
                                     facecolor=color, edgecolor='#bdc3c7')
                ax.add_patch(rect)

        access_color = '#e74c3c' if pattern == 'col' else '#27ae60'
        highlight = order[:n]  # first n accesses
        for step, (r, c) in enumerate(highlight):
            alpha = 0.3 + 0.7 * (step / (n - 1))  # fade in to show access order
            rect = plt.Rectangle((c - 0.5, r - 0.5), 1, 1,
                                  facecolor=access_color, alpha=alpha, edgecolor='white')
            ax.add_patch(rect)
            ax.text(c, r, str(step + 1), ha='center', va='center',
                    fontsize=8, color='white', fontweight='bold')

        ax.set_title(title, fontsize=11)
        ax.set_xticks(range(n))
        ax.set_yticks(range(n))
        ax.set_xticklabels([f'col {i}' for i in range(n)], fontsize=7)
        ax.set_yticklabels([f'row {i}' for i in range(n)], fontsize=7)

        note = 'Sequential in memory' if pattern == 'row' else 'Jumps n floats per step'
        ax.set_xlabel(note, fontsize=9,
                      color='#27ae60' if pattern == 'row' else '#e74c3c')

    fig.suptitle('Memory Access Patterns for Matrix B (row-major storage)',
                 fontsize=12, fontweight='bold')
    fig.tight_layout()
    path = os.path.join(RESULTS_DIR, 'access_pattern.png')
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"saved: {path}")


# main

if __name__ == '__main__':
    random.seed(0)

    print("Generating diagrams...")
    plot_cache_hierarchy()
    plot_access_pattern()
    print()

    matmul_results  = run_matmul_benchmark(sizes=[32, 48, 64, 80])
    aos_soa_results = run_aos_soa_benchmark(sizes=[50_000, 100_000, 250_000, 500_000])
    numpy_results   = run_numpy_benchmark(sizes=[500, 1000, 2000, 3000])
    sweep_results   = run_block_sweep(n=80)

    print("Saving charts...")
    plot_matmul(matmul_results)
    plot_aos_soa(aos_soa_results)
    plot_numpy(numpy_results)
    plot_block_sweep(sweep_results, n=80)

    print()
    print("Done. Results saved to ./results/")
