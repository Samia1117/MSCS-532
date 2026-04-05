# Project Phase 3 - Emergency Response Dispatch System (Optimization)

Extends the Phase 2 proof-of-concept with three improvements that were deferred from Phase 2: a spatial index for nearest-unit lookup, dynamic edge weight updates on the road network, and performance benchmarking at scale.

## Environment

- Python 3.x, no extra packages needed
- Tested on macOS, should work anywhere

## Files

- `dispatch_system.py` - all classes, tests, and the benchmark

---

## How to run

```bash
python3 dispatch_system.py
```

Runs all 6 tests in sequence. Tests 1-5 produce normal verbose output. Test 6 (benchmark) runs silently and prints only the results table at the end.

---

## What changed from Phase 2

### RoadNetwork - coordinate support and update_weight

Each location can now have (x, y) coordinates. These are used by the k-d tree. Edges are stored as mutable lists (`[neighbor, weight]`) instead of tuples so that `update_weight(u, v, new_weight)` can modify them in-place without rebuilding the adjacency list. Cost: O(degree(u) + degree(v)) - just a scan of two adjacency lists.

Dijkstra is still run on-demand, so any weight change is automatically reflected in the next dispatch.

### KDTree - spatial index for available units

2D k-d tree built from scratch (no external libraries). Each available unit is indexed by the (x, y) coordinates of its current location. On each dispatch, the system queries the tree for the k Euclidean-nearest unit candidates (k=3 default), then runs Dijkstra for only those k units instead of all n available units.

Build: O(n log n). Nearest-neighbor query: O(log n) average. After each dispatch the tree is rebuilt from the remaining available units - O(n log n). For v1 this is simpler than lazy deletion and correct.

Euclidean distance is a proxy for graph distance, not the same thing. Using k > 1 guards against cases where a physical obstacle (river, highway) makes the Euclidean nearest unit more expensive to reach by road. k=3 was enough for all test cases on the city network.

### OptimizedDispatchSystem

Replaces the Phase 2 nearest-unit loop (n Dijkstras) with the KDTree approach (k Dijkstras after an O(log n) tree query). Falls back to brute-force Phase 2 behavior if a node has no coordinates set.

---

## What the tests cover

- **Test 1**: KDTree correctness - 1-nearest on a 5-point set, 2-nearest, k > n (should return all points), empty tree
- **Test 2**: Dynamic edge weight update - simulates rush-hour traffic on two edges, verifies the shortest path reroutes; then restores weights and verifies the original path comes back; also checks that updating a nonexistent edge raises KeyError
- **Test 3**: OptimizedDispatchSystem end-to-end - same scenario as Phase 2 Test 5 (3 calls at mixed priorities, 5 units on the city network), verifies critical call is dispatched first
- **Test 4**: k-d tree accuracy vs brute-force - for all 6 locations in the city network, compares the unit chosen by k-d tree (k=3) + Dijkstra against the unit chosen by brute-force Dijkstra over all 5 units; all 6 match
- **Test 5**: Stress test - 100 calls on a 10x10 grid (100 nodes) with 30 units, periodically returning dispatched units to service; checks no crashes and all 100 calls are logged
- **Test 6**: Benchmark - Phase 2 vs Phase 3 on a 20x20 grid (400 nodes) at fleet sizes 10, 25, 50, 100, 200

---

## Benchmark results

Grid: 20x20 = 400 nodes, ~760 edges. 15 calls per trial, 3 repeats, averaged.

```
 Fleet    Phase2 ms/call    Phase3 ms/call   Speedup
------  ----------------  ----------------  --------
    10           0.588ms           0.224ms      2.6x
    25           2.762ms           0.209ms     13.2x
    50           6.562ms           0.160ms     40.9x
   100          14.368ms           0.188ms     76.4x
   200          29.089ms           0.276ms    105.5x
```

Phase 2 scales linearly with fleet size (each dispatch runs n Dijkstras). Phase 3 stays roughly flat because each dispatch runs only 3 Dijkstras + one O(n log n) tree rebuild. The rebuild cost is visible at small fleet sizes (small n means rebuild is cheap but Dijkstra savings are also small), but at n=200 the speedup is ~105x.

Phase 3 timing includes the full cost of `dispatch_next()`: tree query, k Dijkstras, and tree rebuild. Nothing is excluded.

---

## Limitations and next steps

- **Same-priority FIFO**: noted in Phase 2 as a limitation (no stable ordering within a priority level) - still not fixed. Would need a sequence-number tiebreaker in the heap tuple.
- **Tree rebuild after each dispatch**: v1 rebuilds the full tree. v2 could use lazy deletion (mark nodes as deleted, skip them during queries) to avoid O(n log n) rebuilds. Would reduce Phase 3 time further.
- **k selection**: k=3 worked for all test cases on the city network. On a real road network with physical barriers (rivers, rail lines), a higher k might be needed to ensure the true graph-nearest unit is always in the candidate set.
- **Dynamic weights under load**: update_weight() is O(degree), which is fine. But re-running Dijkstra from scratch on every dispatch with frequently changing weights is expensive for large graphs. An incremental shortest-path algorithm (e.g., LPA*) would be more efficient if edge weights change on every dispatch cycle.
