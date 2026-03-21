# Assignment 4 - Heap Data Structures

Implements Heapsort and a priority queue using a max-heap, with comparisons against Quicksort and Merge Sort.

## Environment

- Python 3.x, no extra packages needed
- Tested on macOS, should work anywhere

## Files

- `heapsort.py` - Heapsort implementation + benchmark vs Quicksort and Merge Sort
- `priority_queue.py` - Max-heap priority queue with a Task class

---

## How to run

```bash
python3 heapsort.py
python3 priority_queue.py
```

Each file runs its own tests when executed directly.

---

## What heapsort.py tests

- Sorting a normal unsorted array
- Already-sorted input
- Reverse-sorted input
- Array with duplicates
- All elements the same
- Single element and empty array
- Checks that build_max_heap gives a valid heap (verifies the heap property at every node)
- Runs heapsort on 20 random arrays and compares against Python's built-in sorted()
- Benchmarks heapsort vs quicksort vs merge sort on random, sorted, reverse-sorted, and repeated-element inputs at sizes 100, 500, 1000, 5000

## What priority_queue.py tests

- Basic insert and extract_max with 5 tasks (checks order is correct)
- is_empty on fresh queue, after insert, after extract
- extract_max on an empty queue (should return None, not crash)
- increase_key: bumps a low-priority task up to become the top
- decrease_key: drops the top-priority task so it comes out last
- Drains a 10-task queue and checks priorities come out in descending order
- Stress test with 500 tasks including increase_key and decrease_key mid-flight, then checks all 500 come out in the right order

---

## Summary of findings

### Heapsort

Heapsort is O(n log n) in all cases - worst, average, and best. It does not have a bad input distribution the way deterministic Quicksort does on sorted input. The build_max_heap step is O(n) (not O(n log n) as it might first appear), and the extraction phase is O(n log n), so the total is O(n log n). It also sorts in place, so it only needs O(1) extra memory.

In practice though, heapsort was the slowest of the three on every input in my benchmarks. At n=5000 on random data it took about 0.013s vs 0.009s for quicksort and 0.011s for merge sort. The reason is cache behavior - heapsort jumps around the array a lot when accessing parent/child nodes, which is slow. Quicksort and merge sort tend to work on contiguous sections of memory.

The clearest difference was on repeated elements. Quicksort's three-way partition collapses all duplicates into one bucket so it barely does any work. At n=5000 with only 5 distinct values, quicksort finished in under 0.001s while heapsort still took 0.010s.

Heapsort's consistent O(n log n) across all inputs is its main advantage - it is predictable. But for general use, quicksort and merge sort are faster in practice.

### Priority Queue

All core operations (insert, extract_max, increase_key, decrease_key) are O(log n). This comes from the heap height being floor(log2(n)), so any sift_up or sift_down path is at most O(log n) steps.

The key design decision was adding an index_map dictionary (task_id -> position in the heap). Without it, increase_key and decrease_key would need to scan the whole heap to find the task, making them O(n). With the map, finding the task is O(1) and the rest is just a sift, so both operations are O(log n). The tradeoff is that every swap has to update the map, and it uses O(n) extra memory. For a priority queue that needs these operations, it is worth it.

The stress test (500 tasks, with increase_key and decrease_key mid-flight) confirmed everything works correctly - all tasks came out in descending priority order after the modifications.
