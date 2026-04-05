import random
import time
import sys

sys.setrecursionlimit(15000)

# -----------------
# Part 1: Selection Algorithms
#
# Both algorithms find the k-th smallest element (0-indexed) in
# an unsorted array in O(n) time. The key difference is the
# guarantee: randomized quickselect is O(n) in expectation but
# O(n^2) in the worst case (astronomically unlikely with random
# pivots). Median of medians is O(n) in the worst case guaranteed,
# but with a larger constant due to the expensive pivot selection.
# ------------------------


# Randomized Quickselect
#
# How it works:
#   1. Pick a random pivot from the current subarray.
#   2. Three-way partition: elements smaller than pivot go left,
#      equal to pivot go middle, larger go right.
#   3. Based on where k falls relative to the partition sizes,
#      recurse into exactly one of the three groups.
#
# Three-way partition (vs standard two-way) handles duplicates
# correctly. If all elements are equal, the middle group captures
# everything in one pass and we return immediately.
#
# Time complexity:
#   - Expected O(n). Each partition call is O(n) (scans the array
#     once). With a random pivot, the expected split is at least
#     25/75 with probability 1/2, so the expected number of
#     elements at each level sums to O(n) (Cormen et al., 2022,
#     pp. 215-221).
#   - Worst case O(n^2): if every pivot chosen happens to be the
#     min or max. This requires adversarial input + adversarial
#     random seed, which does not happen in practice.
#
# Space complexity: O(log n) expected recursion depth. The
# three-way partition creates new lists each call, so total space
# is O(n) per level. This implementation trades extra memory for
# simplicity; an in-place version would use O(log n) total space.
# ===================================================================

def randomized_select(arr, k):
    # Returns the k-th smallest element (0-indexed) of arr.
    # Does not modify arr.
    if len(arr) == 1:
        return arr[0]

    pivot = arr[random.randint(0, len(arr) - 1)]

    low  = [x for x in arr if x < pivot]
    mid  = [x for x in arr if x == pivot]
    high = [x for x in arr if x > pivot]

    if k < len(low):
        return randomized_select(low, k)
    elif k < len(low) + len(mid):
        return pivot
    else:
        return randomized_select(high, k - len(low) - len(mid))


######### Median of Medians (deterministic linear-time selection) ########

# How it works:
#   1. Split arr into groups of 5 (last group may be smaller).
#   2. Sort each group and take its median - O(1) per group,
#      O(n/5) groups, O(n) total.
#   3. Recursively find the median of those n/5 medians.
#      This gives a pivot guaranteed to split the array at least
#      30/70 in either direction (Blum et al., 1973).
#   4. Three-way partition around this pivot and recurse into
#      the correct side.


# Time complexity:
#   - Worst case O(n). Let T(n) be the cost. The pivot selection
#     recurses on n/5 elements (T(n/5)). The partition is O(n).
#     The good-split guarantee means the recursive selection
#     step is T(7n/10 + 6) in the worst case.
#     Recurrence: T(n) = T(n/5) + T(7n/10 + 6) + O(n)
#     This solves to T(n) = O(n) by the substitution method
#     (Cormen et al., 2022, pp. 225-229).
#   - The constant factor is large: roughly 10-30x slower than
#     randomized quickselect on typical inputs.

# Space complexity: O(n) per level (new lists each call), O(log n)
# recursion depth. Same note as randomized_select about in-place.

def median_of_medians(arr, k):
    # Returns the k-th smallest element (0-indexed) of arr.
    # Does not modify arr.
    n = len(arr)

    # base case: small enough to sort directly
    if n <= 5:
        return sorted(arr)[k]

    # step 1: split into groups of 5 and find each group's median
    groups  = [arr[i:i + 5] for i in range(0, n, 5)]
    medians = [sorted(g)[len(g) // 2] for g in groups]

    # step 2: recursively find the median of the medians list
    pivot = median_of_medians(medians, len(medians) // 2)

    # step 3: three-way partition around pivot
    low  = [x for x in arr if x < pivot]
    mid  = [x for x in arr if x == pivot]
    high = [x for x in arr if x > pivot]

    if k < len(low):
        return median_of_medians(low, k)
    elif k < len(low) + len(mid):
        return pivot
    else:
        return median_of_medians(high, k - len(low) - len(mid))


# ============
# Tests
# ============

def _brute(arr, k):
    return sorted(arr)[k]


if __name__ == "__main__":

    # Test 1: basic correctness on small arrays
    print("=== Test 1: Basic correctness ===\n")

    cases = [
        ([3, 1, 4, 1, 5, 9, 2, 6], 0, "min"),
        ([3, 1, 4, 1, 5, 9, 2, 6], 7, "max"),
        ([3, 1, 4, 1, 5, 9, 2, 6], 3, "median of 8"),
        ([7],                        0, "single element"),
        ([2, 2, 2, 2],               2, "all duplicates"),
        ([5, 4, 3, 2, 1],            2, "reverse sorted"),
        ([1, 2, 3, 4, 5],            1, "already sorted"),
    ]

    all_pass = True
    for arr, k, label in cases:
        expected = _brute(arr, k)
        rs  = randomized_select(arr, k)
        mom = median_of_medians(arr, k)
        ok  = (rs == expected == mom)
        all_pass = all_pass and ok
        status = "ok" if ok else f"FAIL (expected {expected}, rs={rs}, mom={mom})"
        print(f"  {label:<25} k={k}  expected={expected}  rs={rs}  mom={mom}  {status}")

    print(f"\n  all correct: {all_pass}\n")

    # Test 2: larger random arrays, verify against sorted()
    print("=== Test 2: Random arrays vs sorted() ground truth ===\n")

    rng = random.Random(42)
    n_trials = 20
    all_pass2 = True
    for _ in range(n_trials):
        size = rng.randint(10, 200)
        arr  = [rng.randint(-100, 100) for _ in range(size)]
        k    = rng.randint(0, size - 1)
        expected = _brute(arr, k)
        rs  = randomized_select(arr, k)
        mom = median_of_medians(arr, k)
        if rs != expected or mom != expected:
            print(f"  FAIL: size={size} k={k} expected={expected} rs={rs} mom={mom}")
            all_pass2 = False

    print(f"  ran {n_trials} random trials, all correct: {all_pass2}\n")

    
    # Test 3: edge cases for duplicates
    print("=== Test 3: Duplicate-heavy arrays ===\n")

    dup_cases = [
        ([1] * 100,           50, "100 identical elements"),
        ([1, 2] * 50,         50, "alternating 1,2 x50"),
        ([3, 1, 2] * 33 + [3], 49, "cycling 3 values"),
    ]
    for arr, k, label in dup_cases:
        expected = _brute(arr, k)
        rs  = randomized_select(arr, k)
        mom = median_of_medians(arr, k)
        ok  = (rs == expected == mom)
        print(f"  {label:<30} k={k}  expected={expected}  ok={ok}")
    print()

    ###### Benchmark #######
    print("=== Benchmark: Randomized Select vs Median of Medians ===\n")
    print("finding the median (k = n//2) for each distribution\n")

    sizes       = [100, 500, 1000, 5000, 10000]
    distributions = {
        "random":         lambda n: [random.randint(0, n) for _ in range(n)],
        "sorted":         lambda n: list(range(n)),
        "reverse sorted": lambda n: list(range(n, 0, -1)),
        "all same":       lambda n: [42] * n,
        "few distinct":   lambda n: [random.randint(0, 4) for _ in range(n)],
    }
    REPEATS = 5

    for dist_name, gen in distributions.items():
        print(f"  distribution: {dist_name}")
        print(f"  {'n':>7}  {'rand (ms)':>12}  {'mom (ms)':>12}  {'ratio mom/rand':>14}")
        print(f"  {'-'*7}  {'-'*12}  {'-'*12}  {'-'*14}")

        for n in sizes:
            arr = gen(n)
            k   = n // 2

            # time randomized_select
            t_rs = 0.0
            for _ in range(REPEATS):
                t0 = time.perf_counter()
                randomized_select(arr, k)
                t_rs += time.perf_counter() - t0
            t_rs /= REPEATS

            # time median_of_medians
            t_mom = 0.0
            for _ in range(REPEATS):
                t0 = time.perf_counter()
                median_of_medians(arr, k)
                t_mom += time.perf_counter() - t0
            t_mom /= REPEATS

            ratio = t_mom / t_rs if t_rs > 0 else float('inf')
            print(f"  {n:>7}  {t_rs*1000:>10.3f}ms  {t_mom*1000:>10.3f}ms  {ratio:>13.1f}x")

        print()
