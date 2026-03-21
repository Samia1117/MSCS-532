import random
import time


# --- Max-Heap helpers ---
#
# We represent the heap as a plain Python list.
# For a node at index i:
#   left child  -> 2*i + 1
#   right child -> 2*i + 2
#   parent      -> (i - 1) // 2
#
# In a max-heap, every parent is >= both of its children.


def heapify(arr, n, i):
    # Fix the heap rooted at index i, assuming the left and right
    # subtrees below i are already valid max-heaps.
    # n is the "active" heap size (not always len(arr), because
    # during heapsort we shrink the heap from the right as we
    # move sorted elements into place).

    largest = i
    left = 2 * i + 1
    right = 2 * i + 2

    # is the left child bigger than what we currently think is largest?
    if left < n and arr[left] > arr[largest]:
        largest = left

    # is the right child bigger?
    if right < n and arr[right] > arr[largest]:
        largest = right

    # if i wasn't already the largest, swap and keep fixing downward
    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        heapify(arr, n, largest)


def build_max_heap(arr):
    # Turn an unsorted list into a max-heap in place.
    # We only need to run heapify on the non-leaf nodes.
    # Leaf nodes (index n//2 onward) are trivially valid 1-element heaps.
    # We go from the last non-leaf up to the root (index 0).
    #
    # This runs in O(n) total even though it looks like O(n log n) at first -
    # the math works out because nodes near the bottom have very short
    # sift paths and there are many more of them than nodes near the root.

    n = len(arr)
    last_non_leaf = n // 2 - 1

    for i in range(last_non_leaf, -1, -1):
        heapify(arr, n, i)


def heapsort(arr):
    # Sort arr in place in ascending order using a max-heap.
    #
    # Step 1: rearrange the array into a max-heap  -> O(n)
    # Step 2: repeatedly pull the max element out:
    #   - the max is always at arr[0] (the root)
    #   - swap it to the end of the unsorted portion
    #   - shrink the heap by 1 and fix the root with heapify -> O(log n) each
    #   - do this n-1 times -> O(n log n) total
    #
    # Total: O(n log n), in place (no extra array needed).

    n = len(arr)
    build_max_heap(arr)

    for i in range(n - 1, 0, -1):
        # arr[0] is the current max - move it to position i
        arr[0], arr[i] = arr[i], arr[0]
        # the heap now has one fewer element (size = i), fix the root
        heapify(arr, i, 0)


# --- Quicksort (randomized, for comparison) ---

def quicksort(arr):
    if len(arr) <= 1:
        return arr

    # pick a random pivot so we don't get O(n^2) on sorted input
    pivot = arr[random.randint(0, len(arr) - 1)]

    less    = [x for x in arr if x < pivot]
    equal   = [x for x in arr if x == pivot]
    greater = [x for x in arr if x > pivot]

    return quicksort(less) + equal + quicksort(greater)


# --- Merge Sort (for comparison) ---

def merge_sort(arr):
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2
    left  = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])

    return _merge(left, right)


def _merge(left, right):
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

    # one of the two halves still has elements left - append them
    result.extend(left[i:])
    result.extend(right[j:])
    return result


###### Benchmarking #######

def time_sort(sort_fn, data, in_place=False):
    # for in-place sorts (heapsort), pass in_place=True
    # for sorts that return a new list (quicksort, merge sort), in_place=False
    arr = data[:]   # always work on a copy so the original stays intact
    t0 = time.perf_counter()
    if in_place:
        sort_fn(arr)
    else:
        sort_fn(arr)
    return time.perf_counter() - t0


def run_comparison():
    sizes = [100, 500, 1000, 5000]

    print("comparing heapsort vs quicksort vs merge sort")
    print("(times in seconds)\n")

    for n in sizes:
        datasets = {
            "random":   [random.randint(0, 10000) for _ in range(n)],
            "sorted":   list(range(n)),
            "reverse":  list(range(n, 0, -1)),
            "repeated": [random.choice([1, 2, 3, 4, 5]) for _ in range(n)],
        }

        for label, data in datasets.items():
            # heapsort is in-place
            arr = data[:]
            t0 = time.perf_counter()
            heapsort(arr)
            t_heap = time.perf_counter() - t0

            t_quick = time_sort(quicksort, data)
            t_merge = time_sort(merge_sort, data)

            print(f"n={n:<5} | {label:<8} | heap={t_heap:.6f}s | quick={t_quick:.6f}s | merge={t_merge:.6f}s")
        print()


# Tests

if __name__ == "__main__":

    print("------ basic correctness tests ------")
    print("\n")

    # normal case
    a = [5, 3, 8, 1, 9, 2, 7]
    heapsort(a)
    print("heapsort [5,3,8,1,9,2,7]:", a)
    print("  expected: [1, 2, 3, 5, 7, 8, 9]")
    print("  correct:", a == [1, 2, 3, 5, 7, 8, 9])

    print()

    # already sorted - should still work
    b = [1, 2, 3, 4, 5]
    heapsort(b)
    print("already sorted [1,2,3,4,5]:", b)
    print("  correct:", b == [1, 2, 3, 4, 5])

    print()

    # reverse sorted
    c = [9, 8, 7, 6, 5, 4]
    heapsort(c)
    print("reverse sorted [9,8,7,6,5,4]:", c)
    print("  correct:", c == [4, 5, 6, 7, 8, 9])

    print()

    # duplicates
    d = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3]
    heapsort(d)
    print("with duplicates [3,1,4,1,5,9,2,6,5,3]:", d)
    print("  expected: [1, 1, 2, 3, 3, 4, 5, 5, 6, 9]")
    print("  correct:", d == [1, 1, 2, 3, 3, 4, 5, 5, 6, 9])

    print()

    # all same
    e = [4, 4, 4, 4, 4]
    heapsort(e)
    print("all same [4,4,4,4,4]:", e)
    print("  correct:", e == [4, 4, 4, 4, 4])

    print()

    # single element
    f = [42]
    heapsort(f)
    print("single element [42]:", f)
    print("  correct:", f == [42])

    print()

    # empty array
    g = []
    heapsort(g)
    print("empty []:", g)
    print("  correct:", g == [])

    print()

    # check build_max_heap separately
    print("----- build_max_heap check -----\n")

    h = [3, 1, 4, 1, 5, 9, 2, 6]
    build_max_heap(h)
    print("max-heap from [3,1,4,1,5,9,2,6]:", h)
    print("  root (h[0]) should be 9:", h[0] == 9)

    # check the heap property holds for every node
    n = len(h)
    heap_ok = True
    for i in range(n):
        left  = 2 * i + 1
        right = 2 * i + 2
        if left < n and h[left] > h[i]:
            heap_ok = False
        if right < n and h[right] > h[i]:
            heap_ok = False
    print("  heap property holds for all nodes:", heap_ok)

    print()

    # verify against Python's sorted() on random data ---
    print("--- heapsort vs sorted() on random data ---\n")

    all_match = True
    for trial in range(20):
        arr = [random.randint(0, 1000) for _ in range(random.randint(0, 50))]
        expected = sorted(arr)
        heapsort(arr)
        if arr != expected:
            print(f"  MISMATCH on trial {trial}!")
            all_match = False

    print("20 random trials all match Python sorted():", all_match)

    print()

    # empirical comparison
    print("------ empirical comparison ------\n")
    run_comparison()
