# Assignment 3 - Algorithm Efficiency and Scalability

Implements and benchmarks two algorithms: Randomized Quicksort and a Hash Table with chaining.

## Environment

- Python 3.x (no third-party packages required)
- Tested on macOS; should work on any standard Python 3 environment
- No virtual environment needed

## Files

- `randomized_quicksort.py` - Randomized and deterministic quicksort with benchmark
- `hash_table.py` - Hash table using chaining with a universal hash function

---

## Running the code

### Randomized Quicksort

```bash
python3 randomized_quicksort.py
```

This runs a sanity check on a small array, then benchmarks both variants across four input distributions and four array sizes.

**Example output:**

```
original: [5, 3, 8, 1, 9, 2, 7]
randomized: [1, 2, 3, 5, 7, 8, 9]
deterministic: [1, 2, 3, 5, 7, 8, 9]

comparing randomized vs deterministic quicksort

n=100   | random   | rand=0.000051s | det=0.000041s
n=100   | sorted   | rand=0.000034s | det=0.000039s
...
n=1000  | sorted   | rand=0.000271s | det=recursion error
n=5000  | sorted   | rand=0.002807s | det=timeout (recursion depth)
```

### Hash Table

```bash
python3 hash_table.py
```

Runs through a series of manual test cases covering all operations.

---

## Test cases

### randomized_quicksort.py

| Test | What it checks |
|------|---------------|
| Sanity check on `[5, 3, 8, 1, 9, 2, 7]` | Both variants produce correctly sorted output |
| Random input, n in {100, 500, 1000, 5000} | Average-case performance, both should be O(n log n) |
| Sorted input, n in {100, 500, 1000, 5000} | Deterministic hits O(n^2) / RecursionError; randomized handles it fine |
| Reverse-sorted input, same sizes | Same pathological case for deterministic version |
| Repeated elements (only 5 distinct values), same sizes | Three-way partition collapses duplicates; both variants finish quickly |

For sorted/reverse-sorted at n > 1000, the deterministic version is skipped and reported as "timeout (recursion depth)" to avoid hanging.

### hash_table.py

| Test | What it checks |
|------|---------------|
| Insert + search (`alice`, `bob`, `carol`) | Basic insert and lookup work correctly |
| Search for missing key (`dave`) | Returns `None` when key not present |
| Update existing key (`alice` re-inserted with new value) | Insert on an existing key updates the value rather than duplicating |
| Delete (`bob`) | Key is removed; subsequent search returns `None` |
| Delete missing key | Returns `False` without error |
| Insert 20 items into a table starting at size 4 | Triggers multiple resizes; verifies all keys still findable after rehashing |
| Integer keys (0-9 mapped to their squares) | Hash function works on integers, not just strings |
