import time
import random
import tracemalloc


def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)


def merge(left, right):
    result = []
    i = 0
    j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    # append whatever is left
    while i < len(left):
        result.append(left[i])
        i += 1
    while j < len(right):
        result.append(right[j])
        j += 1
    return result


def get_pivot(arr):
    # median of first, middle, last
    first = arr[0]
    mid = arr[len(arr) // 2]
    last = arr[-1]
    if first <= mid <= last or last <= mid <= first:
        return mid
    elif mid <= first <= last or last <= first <= mid:
        return first
    else:
        return last


def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = get_pivot(arr)
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
    return quick_sort(less) + equal + quick_sort(greater)


def run_comparison():
    sizes = [100, 1000, 5000, 10000]

    print("testing merge sort and quick sort on different datasets\n")

    for n in sizes:
        # random data
        data = [random.randint(0, 10000) for _ in range(n)]

        tracemalloc.start()
        t0 = time.perf_counter()
        merge_sort(data[:])
        t1 = time.perf_counter()
        _, mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"merge sort | random      | n={n} | time={t1-t0:.6f}s | mem={mem/1024:.2f}KB")

        tracemalloc.start()
        t0 = time.perf_counter()
        quick_sort(data[:])
        t1 = time.perf_counter()
        _, mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"quick sort | random      | n={n} | time={t1-t0:.6f}s | mem={mem/1024:.2f}KB")

        # sorted data
        data_sorted = list(range(n))

        tracemalloc.start()
        t0 = time.perf_counter()
        merge_sort(data_sorted[:])
        t1 = time.perf_counter()
        _, mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"merge sort | sorted      | n={n} | time={t1-t0:.6f}s | mem={mem/1024:.2f}KB")

        tracemalloc.start()
        t0 = time.perf_counter()
        quick_sort(data_sorted[:])
        t1 = time.perf_counter()
        _, mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"quick sort | sorted      | n={n} | time={t1-t0:.6f}s | mem={mem/1024:.2f}KB")

        # reverse sorted
        data_rev = list(range(n, 0, -1))

        tracemalloc.start()
        t0 = time.perf_counter()
        merge_sort(data_rev[:])
        t1 = time.perf_counter()
        _, mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"merge sort | reverse     | n={n} | time={t1-t0:.6f}s | mem={mem/1024:.2f}KB")

        tracemalloc.start()
        t0 = time.perf_counter()
        quick_sort(data_rev[:])
        t1 = time.perf_counter()
        _, mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"quick sort | reverse     | n={n} | time={t1-t0:.6f}s | mem={mem/1024:.2f}KB")

        print()


if __name__ == "__main__":
    sample = [38, 27, 43, 3, 9, 82, 10]
    print("original:", sample)
    print("merge sort:", merge_sort(sample))
    print("quick sort:", quick_sort(sample))
    print()

    run_comparison()
