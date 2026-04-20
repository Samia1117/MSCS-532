# plot_results.py
# reads CSVs produced by cache_opt_final.py and generates charts

import os
import csv

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')


def read_csv(filename):
    path = os.path.join(RESULTS_DIR, filename)
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)


def plot_matmul():
    rows = read_csv('matmul.csv')
    ns    = [int(r['n']) for r in rows]
    naive = [float(r['naive_s']) for r in rows]
    trans = [float(r['transposed_s']) for r in rows]
    block = [float(r['blocked_s']) for r in rows]
    sp_t  = [float(r['speedup_T']) for r in rows]
    sp_b  = [float(r['speedup_B']) for r in rows]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    ax = axes[0]
    ax.plot(ns, naive, 'o-', label='Naive',             color='#c0392b')
    ax.plot(ns, trans, 's-', label='Transposed',        color='#2980b9')
    ax.plot(ns, block, '^-', label='Blocked (tile=16)', color='#27ae60')
    ax.set_xlabel('Matrix size n')
    ax.set_ylabel('Time (seconds)')
    ax.set_title('Matrix Multiply: Absolute Time')
    ax.legend()
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    x = range(len(ns))
    w = 0.35
    ax.bar([i - w/2 for i in x], sp_t, w, label='Transposed', color='#2980b9')
    ax.bar([i + w/2 for i in x], sp_b, w, label='Blocked',    color='#27ae60')
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


def plot_aos_soa():
    rows  = read_csv('aos_soa.csv')
    ns    = [int(r['n']) for r in rows]
    t_aos = [float(r['aos_ms']) for r in rows]
    t_soa = [float(r['soa_ms']) for r in rows]
    sp    = [float(r['speedup']) for r in rows]

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


def plot_numpy():
    rows  = read_csv('numpy_access.csv')
    ns    = [int(r['n']) for r in rows]
    t_row = [float(r['row_ms']) for r in rows]
    t_col = [float(r['col_ms']) for r in rows]
    sp    = [float(r['speedup']) for r in rows]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    ax = axes[0]
    ax.plot(ns, t_row, 'o-', label='Row access (cache friendly)',   color='#27ae60')
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


def plot_block_sweep():
    rows   = read_csv('block_sweep.csv')
    sizes  = [r['block_size'] for r in rows]  # keep as strings for x-axis labels
    times  = [float(r['time_s']) for r in rows]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(sizes, times, color='#2980b9', edgecolor='white')
    ax.set_xlabel('Block (tile) size')
    ax.set_ylabel('Time (seconds)')
    ax.set_title('Block Size Sweep')
    ax.grid(True, alpha=0.3, axis='y')
    fig.tight_layout()
    path = os.path.join(RESULTS_DIR, 'block_sweep.png')
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"saved: {path}")


if __name__ == '__main__':
    plot_matmul()
    plot_aos_soa()
    plot_numpy()
    plot_block_sweep()
    print("done")
