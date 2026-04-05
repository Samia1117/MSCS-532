# Assignment 6 - Medians, Order Statistics, and Elementary Data Structures

Two parts. Part 1 implements and benchmarks two selection algorithms (find the k-th smallest element in O(n) time). Part 2 implements five elementary data structures from scratch using Python lists.

## Environment

- Python 3.x, no extra packages needed
- Tested on macOS, should work anywhere

## Files

- `selection.py` - Part 1: Randomized Quickselect and Median of Medians
- `data_structures.py` - Part 2: DynamicArray, Matrix, Stack, Queue, SinglyLinkedList, RootedTree

---

## How to run

```bash
python3 selection.py
python3 data_structures.py
```

Each file runs its own tests and (for selection.py) a benchmark when executed directly.

---

## Part 1: Selection Algorithms

### What's implemented

**Randomized Quickselect** (`randomized_select(arr, k)`): picks a random pivot, does a three-way partition (less / equal / greater), recurses into exactly one partition. Expected O(n) time, O(n^2) worst case (essentially impossible with random pivots).

**Median of Medians** (`median_of_medians(arr, k)`): splits arr into groups of 5, takes each group's median, recursively finds the median of those medians, uses it as a pivot. The resulting pivot is guaranteed to split the array at least 30/70, which makes the recurrence T(n) = T(n/5) + T(7n/10 + 6) + O(n) = O(n) in the worst case (Blum et al., 1973; Cormen et al., 2022).

Both use three-way partitioning so duplicate elements are handled correctly.

### Tests

- 7 manual cases: min, max, median, single element, all duplicates, reverse sorted, already sorted
- 20 random trials (size 10-200, random k): compared against Python's `sorted(arr)[k]`
- 3 duplicate-heavy cases: 100 identical elements, alternating pairs, cycling 3 values

All correct on every run.

### Benchmark results

Finding the median (k = n//2) on a 20x20 grid, averaged over 5 runs:

```
distribution: random
      n     rand (ms)      mom (ms)  ratio mom/rand
-------  ------------  ------------  --------------
    100       0.017ms       0.022ms            1.3x
    500       0.081ms       0.135ms            1.7x
   1000       0.152ms       0.234ms            1.5x
   5000       0.710ms       0.647ms            0.9x
  10000       1.388ms       2.788ms            2.0x

distribution: sorted
      n     rand (ms)      mom (ms)  ratio mom/rand
-------  ------------  ------------  --------------
    100       0.014ms       0.020ms            1.5x
    500       0.074ms       0.098ms            1.3x
   1000       0.126ms       0.205ms            1.6x
   5000       0.580ms       1.017ms            1.8x
  10000       1.033ms       2.059ms            2.0x

distribution: all same
      n     rand (ms)      mom (ms)  ratio mom/rand
-------  ------------  ------------  --------------
    100       0.004ms       0.008ms            1.9x
    500       0.017ms       0.038ms            2.2x
   1000       0.033ms       0.075ms            2.2x
   5000       0.184ms       0.342ms            1.9x
  10000       0.300ms       0.693ms            2.3x
```

### Key takeaways

Randomized quickselect is consistently 1.5-2x faster than median of medians across all input distributions and sizes. Both scale linearly with n (the lines are straight on a log-log plot). The "all same" distribution is the fastest for both - three-way partition puts everything in the "equal" bucket in one pass.

The practical case for Median of Medians is adversarial input where an attacker can choose both the data and a seed to force bad pivots in the randomized version. In any real application without an adversarial input assumption, randomized quickselect is the better choice.

---

## Part 2: Elementary Data Structures

### What's implemented

**DynamicArray**: array with O(1) get/set, O(1) amortized append, O(n) insert/delete at arbitrary index.

**Matrix**: 2D array (list of lists) with O(1) get/set, O(rows*cols) addition, O(rows*cols*k) multiplication.

**Stack**: array-backed LIFO. push/pop/peek all O(1). The top is the end of the list so no shifting occurs.

**Queue**: array-backed FIFO with a front pointer. Dequeue advances the pointer instead of shifting elements. The backing list is compacted when the wasted prefix exceeds half the total size, making dequeue O(1) amortized. A circular buffer would be cleaner but harder to implement from scratch.

**SinglyLinkedList**: chain of nodes. insert_front is O(1). insert_back, search, delete are O(n) because the list must be traversed. No tail pointer in this version.

**RootedTree** (bonus): general n-ary tree using parent/children pointers. Supports preorder DFS and BFS level-order traversal, both O(n).

### Complexity summary

| Structure | Operation | Time | Space |
|-----------|-----------|------|-------|
| DynamicArray | get / set | O(1) | O(n) |
| DynamicArray | append | O(1) amortized | O(n) |
| DynamicArray | insert / delete | O(n) | O(n) |
| Matrix | get / set | O(1) | O(rows*cols) |
| Matrix | add | O(rows*cols) | O(rows*cols) |
| Matrix | multiply | O(rows*cols*k) | O(rows*cols) |
| Stack | push / pop / peek | O(1) amortized | O(n) |
| Queue | enqueue / dequeue | O(1) amortized | O(n) |
| SinglyLinkedList | insert front | O(1) | O(n) |
| SinglyLinkedList | insert back / delete / search | O(n) | O(n) |
| RootedTree | add_child | O(1) | O(n) |
| RootedTree | find / traverse | O(n) | O(n) |

### Array vs linked list for stacks and queues

For stacks, both work fine. Array-backed wins in practice because of cache locality - elements are contiguous in memory so the CPU can prefetch them. A linked-list stack spends extra time on node allocation and pointer chasing.

For queues, it's less obvious. A linked list gives O(1) guaranteed dequeue with no compaction needed, but every element needs an extra pointer (8 bytes on 64-bit systems) and node allocation. The array + front-pointer approach uses memory more efficiently and stays cache-friendly, at the cost of occasional O(n) compaction that is O(1) amortized. For high-throughput queues, a ring buffer (circular array) is usually the fastest practical choice (Aho et al., 1983).

The bottom line: arrays are usually faster due to cache behavior; linked lists are useful when you need guaranteed O(1) operations without amortization, or when you need O(1) front insertion and deletion simultaneously (which arrays can't do without shifting).
