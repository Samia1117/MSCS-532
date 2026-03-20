import random
import time


### Randomized Quicksort 
# pivot is chosen uniformly at random from the current subarray

def randomized_quicksort(arr):
    if len(arr) <= 1:
        return arr

    # random pivot - key difference from deterministic version
    pivot_index = random.randint(0, len(arr) - 1)
    pivot = arr[pivot_index]

    less = []
    equal = []
    greater = []
    for x in arr:
        if x < pivot:
            less.append(x)
        elif x == pivot:
            equal.append(x)
        else:
            greater.append(x)

    return randomized_quicksort(less) + equal + randomized_quicksort(greater)


### Deterministic Quicksort 
# pivot is always the first element - bad on sorted/reverse-sorted input

def deterministic_quicksort(arr):
    if len(arr) <= 1:
        return arr

    pivot = arr[0]  # always first element

    less = []
    equal = []
    greater = []
    for x in arr:
        if x < pivot:
            less.append(x)
        elif x == pivot:
            equal.append(x)
        else:
            greater.append(x)

    return deterministic_quicksort(less) + equal + deterministic_quicksort(greater)


def benchmark(fn, data):
    arr = data[:]
    t0 = time.perf_counter()
    fn(arr)
    return time.perf_counter() - t0


def run_comparison():
    sizes = [100, 500, 1000, 5000]

    print("comparing randomized vs deterministic quicksort\n")

    for n in sizes:
        datasets = {
            "random":   [random.randint(0, 10000) for _ in range(n)],
            "sorted":   list(range(n)),
            "reverse":  list(range(n, 0, -1)),
            "repeated": [random.choice([1, 2, 3, 4, 5]) for _ in range(n)],
        }

        for label, data in datasets.items():
            t_rand = benchmark(randomized_quicksort, data)
            # deterministic on sorted/reverse is very slow for large n - skip to avoid timeout
            if label in ("sorted", "reverse") and n > 1000:
                t_det = float('inf')
                det_str = "timeout (recursion depth)"
            else:
                try:
                    t_det = benchmark(deterministic_quicksort, data)
                    det_str = f"{t_det:.6f}s"
                except RecursionError:
                    t_det = float('inf')
                    det_str = "recursion error"
            print(f"n={n:<5} | {label:<8} | rand={t_rand:.6f}s | det={det_str}")
        print()


if __name__ == "__main__":
    # sanity check
    sample = [5, 3, 8, 1, 9, 2, 7]
    print("original:", sample)
    print("randomized:", randomized_quicksort(sample))
    print("deterministic:", deterministic_quicksort(sample))
    print()

    run_comparison()
