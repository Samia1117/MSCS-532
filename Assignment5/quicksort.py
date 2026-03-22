import random
import time
import sys


##### 
# Lomuto partition scheme
#
# Rearranges arr[low..high] around a pivot, returning the pivot's final
# index. After partition returns, everything to the left of the pivot is
# <= pivot and everything to the right is > pivot. The pivot itself is
# in its correct sorted position.
#
# How it works:
#   - pick a pivot (the element at arr[high])
#   - i starts just before the subarray (low - 1)
#   - j walks from low to high-1
#   - whenever arr[j] <= pivot, advance i and swap arr[i] with arr[j]
#     (this grows the "small" section by one)
#   - after the loop, swap the pivot (arr[high]) into position i+1
#   - return i+1 as the pivot's final index

def _partition(arr, low, high):
    pivot = arr[high]   # deterministic: always use the last element
    i = low - 1         # boundary between "small" and "large" sections

    for j in range(low, high):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]

    # place pivot in its correct position
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1


def _random_partition(arr, low, high):
    # pick a random index in [low, high], swap it to the end,
    # then run the same Lomuto partition as above.
    # by making the pivot random we avoid the worst-case on sorted input.
    pivot_idx = random.randint(low, high)
    arr[pivot_idx], arr[high] = arr[high], arr[pivot_idx]
    return _partition(arr, low, high)


# Deterministic Quicksort
#
# Always picks the last element as the pivot.
# This is simple and works well on random input, but on already-sorted
# or reverse-sorted input it always picks the min or max as pivot.
# That produces one empty subproblem and one of size n-1 every time,
# giving O(n^2) comparisons and O(n) recursion depth.
# -----------------------------------------------------------------------

def deterministic_quicksort(arr, low=None, high=None):
    # allow calling as deterministic_quicksort(arr) without index args
    if low is None:
        low = 0
    if high is None:
        high = len(arr) - 1

    if low < high:
        pi = _partition(arr, low, high)
        deterministic_quicksort(arr, low, pi - 1)
        deterministic_quicksort(arr, pi + 1, high)


# Randomized Quicksort
#
# Same structure as the deterministic version, but the pivot is chosen
# uniformly at random from arr[low..high] before each partition.
# This means no fixed input can reliably trigger the worst case.
# The expected number of comparisons is O(n log n) for any input.
# -----------------------------------------------------------------------

def randomized_quicksort(arr, low=None, high=None):
    if low is None:
        low = 0
    if high is None:
        high = len(arr) - 1

    if low < high:
        pi = _random_partition(arr, low, high)
        randomized_quicksort(arr, low, pi - 1)
        randomized_quicksort(arr, pi + 1, high)


# #######
# Benchmarking
# #######

def time_sort(sort_fn, data):
    arr = data[:]   # work on a copy so the original is reusable
    t0 = time.perf_counter()
    sort_fn(arr)
    return time.perf_counter() - t0


def run_comparison():
    sizes = [100, 500, 1000, 5000]

    print("deterministic vs randomized quicksort")
    print("times in milliseconds\n")

    for n in sizes:
        datasets = {
            "random":   [random.randint(0, 10000) for _ in range(n)],
            "sorted":   list(range(n)),
            "reverse":  list(range(n, 0, -1)),
            "repeated": [random.choice([1, 2, 3, 4, 5]) for _ in range(n)],
        }

        for label, data in datasets.items():
            t_rand = time_sort(randomized_quicksort, data) * 1000

            # deterministic can hit recursion limit on sorted/reverse for large n
            try:
                t_det = time_sort(deterministic_quicksort, data) * 1000
                det_str = f"{t_det:.3f}ms"
            except RecursionError:
                det_str = "recursion error"

            print(f"n={n:<5} | {label:<8} | det={det_str:<25} | rand={t_rand:.3f}ms")

        print()

if __name__ == "__main__":

    ########## Testsss ###########
    print("------ correctness tests - deterministic ------\n")

    a = [5, 3, 8, 1, 9, 2, 7]
    deterministic_quicksort(a)
    print("sort [5,3,8,1,9,2,7]:", a)
    print("  expected: [1, 2, 3, 5, 7, 8, 9]")
    print("  correct:", a == [1, 2, 3, 5, 7, 8, 9])

    print()

    b = [1, 2, 3, 4, 5]
    deterministic_quicksort(b)
    print("already sorted [1,2,3,4,5]:", b)
    print("  correct:", b == [1, 2, 3, 4, 5])

    print()

    c = [5, 4, 3, 2, 1]
    deterministic_quicksort(c)
    print("reverse sorted [5,4,3,2,1]:", c)
    print("  correct:", c == [1, 2, 3, 4, 5])

    print()

    d = [4, 4, 4, 4]
    deterministic_quicksort(d)
    print("all same [4,4,4,4]:", d)
    print("  correct:", d == [4, 4, 4, 4])

    print()

    e = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3]
    deterministic_quicksort(e)
    print("duplicates [3,1,4,1,5,9,2,6,5,3]:", e)
    print("  expected: [1, 1, 2, 3, 3, 4, 5, 5, 6, 9]")
    print("  correct:", e == [1, 1, 2, 3, 3, 4, 5, 5, 6, 9])

    print()

    f = [42]
    deterministic_quicksort(f)
    print("single element [42]:", f)
    print("  correct:", f == [42])

    print()

    g = []
    deterministic_quicksort(g)
    print("empty []:", g)
    print("  correct:", g == [])

    print()

    print("------ correctness tests - randomized ------\n")

    # run the same checks on the randomized version
    tests = [
        ([5, 3, 8, 1, 9, 2, 7], [1, 2, 3, 5, 7, 8, 9]),
        ([1, 2, 3, 4, 5],        [1, 2, 3, 4, 5]),
        ([5, 4, 3, 2, 1],        [1, 2, 3, 4, 5]),
        ([4, 4, 4, 4],           [4, 4, 4, 4]),
        ([42],                   [42]),
        ([],                     []),
    ]

    all_ok = True
    for arr, expected in tests:
        randomized_quicksort(arr)
        if arr != expected:
            print(f"  FAIL: got {arr}, expected {expected}")
            all_ok = False

    print("all randomized correctness tests passed:", all_ok)

    print()

    # verify both versions against Python's sorted() on random data
    print("------ both versions vs sorted() on 50 random arrays ------\n")

    det_ok = True
    rand_ok = True

    for _ in range(50):
        arr = [random.randint(0, 500) for _ in range(random.randint(0, 60))]
        expected = sorted(arr)

        det_arr = arr[:]
        deterministic_quicksort(det_arr)
        if det_arr != expected:
            det_ok = False

        rand_arr = arr[:]
        randomized_quicksort(rand_arr)
        if rand_arr != expected:
            rand_ok = False

    print("deterministic matches sorted() on all 50 trials:", det_ok)
    print("randomized   matches sorted() on all 50 trials:", rand_ok)

    print()

    # show worst-case behavior of deterministic on sorted input
    print("------ worst-case demo: sorted input ------\n")
    print("deterministic quicksort on sorted arrays of increasing size:")
    print("(pivot is always the last element = the max = one subproblem is always empty)")
    print()

    for n in [100, 500, 1000, 2000]:
        arr = list(range(n))
        t0 = time.perf_counter()
        try:
            deterministic_quicksort(arr)
            elapsed = (time.perf_counter() - t0) * 1000
            print(f"  n={n}: {elapsed:.3f}ms")
        except RecursionError:
            print(f"  n={n}: recursion error (hit sys.setrecursionlimit)")

    print()
    print("randomized quicksort on the same sorted arrays:")
    for n in [100, 500, 1000, 2000]:
        arr = list(range(n))
        t0 = time.perf_counter()
        randomized_quicksort(arr)
        elapsed = (time.perf_counter() - t0) * 1000
        print(f"  n={n}: {elapsed:.3f}ms")

    print()

    # full benchmark
    print("------ full benchmark ------\n")
    run_comparison()
