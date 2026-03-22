# Assignment 5 - Quicksort: Deterministic vs Randomized

Implements both versions of Quicksort using the Lomuto in-place partition scheme, with correctness tests and a benchmark comparing them across different input distributions.

## Environment

- Python 3.x, no extra packages needed
- Tested on macOS, should work anywhere

## Files

- `quicksort.py` - both versions of Quicksort plus all tests and the benchmark

---

## How to run

```bash
python3 quicksort.py
```

This runs the correctness tests first, then a worst-case demo, then the full benchmark.

---

## What the tests cover

- Basic sort on a mixed array
- Already sorted input
- Reverse sorted input
- All elements the same
- Array with duplicates
- Single element and empty array
- Both versions verified against Python's built-in sorted() on 50 random arrays
- Worst-case demo: shows how deterministic Quicksort slows down (or hits the recursion limit) on sorted input as n grows, while randomized handles it fine

---

## Summary of findings

### Random input

On random data the deterministic version is actually slightly faster - 2.5ms vs 3.2ms at n=5000. Both are getting similar quality splits so the only difference is the extra random.randint call and swap in the randomized version. Neither version has an advantage here.

### Sorted and reverse-sorted input - where it really matters

This is where the difference is obvious. At n=5000:
- sorted:  deterministic = 447.8ms, randomized = 2.8ms  (~160x slower)
- reverse: deterministic = 308.8ms, randomized = 2.8ms  (~110x slower)

The randomized version runs in about the same time as it does on random data. The deterministic version blows up because the last element is always the max, so every partition produces one empty subproblem and one of size n-1 - O(n^2) total work.

The O(n^2) growth is confirmed by the numbers: from n=1000 (17.3ms) to n=5000 (447.8ms) is a ~26x increase for a 5x increase in n, and 5^2 = 25. It tracks almost exactly.

The worst-case demo section shows the same thing more starkly:

```
deterministic on sorted input:
  n=100:  0.191ms
  n=500:  5.213ms
  n=1000: 21.520ms
  n=2000: 72.090ms

randomized on the same input:
  n=100:  0.062ms
  n=500:  0.266ms
  n=1000: 0.485ms
  n=2000: 1.011ms
```

### Repeated elements

Both versions are slow here - 82.3ms vs 84.5ms at n=5000. The Lomuto partition scheme doesn't handle duplicates specially, so with only 5 distinct values the splits can still be very unbalanced. Neither version has an advantage on this input.

### Bottom line

Randomization costs almost nothing on random input and is ~160x faster on sorted input at n=5000. For any real use case where the input might be sorted or structured, the randomized version is the right choice.
