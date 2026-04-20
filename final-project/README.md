# Final Project - Data Locality Optimization in HPC

Demos from Azad et al. (2023), "An Empirical Study of HPC Performance Bugs" (MSR 2023).
Data locality fixes were the most common category in that study (21% of all fixes).

## Setup

```bash
pip3 install numpy matplotlib
```

## Files

- `cache_opt.py` - rough first version, prints benchmark results to stdout, no charts
- `cache_opt_final.py` - full version, same benchmarks + saves CSV files to `results/`
- `plot_results.py` - reads the CSVs and generates charts into `results/`

## How to run

```bash
python3 cache_opt_final.py   # collect data -> results/*.csv
python3 plot_results.py      # generate charts -> results/*.png
```

## What it benchmarks

- matrix multiply: naive (cache unfriendly) vs transposed vs cache-blocked
- AoS vs SoA: particle kinetic energy sum, only mass field accessed
- numpy row vs column access on a C-order array
- block size sweep: effect of tile size on blocked matmul
