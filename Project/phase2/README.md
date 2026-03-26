# Project Phase 2 - Emergency Response Dispatch System

Proof-of-concept implementation of a priority-based emergency dispatch system. Builds on the Phase 1 design and addresses three limitations that were identified there: no decrease-key support in the call queue, a static road network, and an O(n * Dijkstra) nearest-unit search.

Phase 2 fully addresses limitation 1 (custom heap with decrease_key). Limitation 3 is partially addressed by caching Dijkstra results from HQ. Limitation 2 is deferred to Phase 3.

## Environment

- Python 3.x, no extra packages needed
- Tested on macOS, should work anywhere

## Files

- `dispatch_system.py` - all classes plus the test suite

---

## How to run

```bash
python3 dispatch_system.py
```

Runs all 8 tests in sequence and prints results to stdout.

---

## What's in the code

### EmergencyCall

Simple data class for an incoming call. Priority 1 = critical (cardiac arrest, active fire), 2 = urgent (collision with injuries), 3 = standard (minor incidents).

### CallQueue

Min-heap priority queue with decrease_key support. This is the main new piece in Phase 2. Phase 1 used Python's heapq directly, which has no way to re-triage a call to a higher priority once it's already in the queue - you'd have to rebuild the entire heap.

The fix is an index_map (call_id -> index in heap) maintained alongside the heap. Every time two elements swap positions the map is updated. With the map, decrease_key is O(1) to find the element and O(log n) to sift it up. push and pop are also O(log n).

### RoadNetwork

Undirected weighted graph (adjacency list). Edge weights are travel times in minutes. Shortest paths are computed with Dijkstra's algorithm using Python's heapq. The predecessor map lets you reconstruct the full route, not just the distance.

### DispatchTable

Hash table of responder units keyed by unit_id. Stores unit type, current location, and status (available / dispatched). O(1) average for lookup, insert, and update.

### DispatchSystem

Ties everything together. Calls come in via receive_call() and go into the CallQueue. dispatch_next() pops the highest-priority call, finds the nearest available unit by running Dijkstra from each available unit's current location to the call site, and assigns the closest one. Every assignment is logged.

The nearest-unit search is currently O(n * Dijkstra) where n is the number of available units - this is the main bottleneck to address in Phase 3.

---

## What the tests cover

- **Test 1**: CallQueue basic push/pop - inserts 3 calls at different priorities, checks they come out in the right order
- **Test 2**: decrease_key (re-triage) - inserts a call at priority 3, bumps it to priority 1, verifies it becomes the top of the queue and comes out first
- **Test 3**: RoadNetwork shortest paths - runs Dijkstra on 4 known routes in the city network and checks distances and paths, plus an unreachable node case
- **Test 4**: DispatchTable - registers units, dispatches one, checks available count drops, then marks it available again
- **Test 5**: End-to-end dispatch - receives 3 calls at mixed priorities, dispatches all, verifies highest priority goes first and each gets the nearest available unit
- **Test 6**: Retriage via DispatchSystem - receives 3 calls, re-triages a low-priority one to critical, confirms it gets dispatched first
- **Test 7**: No available units - dispatches a call when the table is empty, checks it logs as unassigned
- **Test 8**: Same priority calls - verifies all calls at the same priority level come out correctly (no crash or corruption)

---

## Summary of findings

### CallQueue with decrease_key

The index_map approach works correctly and keeps all operations at O(log n). The tradeoff is O(n) extra space for the map and the overhead of updating it on every swap. For an emergency dispatch system where re-triaging a call is a real operational need, that tradeoff is worth it.

Without the map, decrease_key would require a linear scan to find the element (O(n)), which is fine at small scale but degrades badly as the queue grows. With the map, the operation is the same cost as a regular heap sift.

### Nearest-unit dispatch

The current approach runs one Dijkstra per available unit to find the closest one. Each Dijkstra is O((V + E) log V), so total nearest-unit search is O(n * (V + E) log V) where n is the number of available units. For the city network in the tests (9 nodes, ~9 edges, 5 units) this is fast enough, but it would not scale to a large city with hundreds of units.

The Phase 3 approach is to precompute and cache shortest paths from HQ outward so individual unit lookups can reuse existing distances. Alternatively, a multi-source Dijkstra starting from all available unit locations simultaneously would find the nearest unit in a single O((V + E) log V) pass.

### Road network

The current network is static - edge weights do not change at runtime. This means traffic, road closures, and time-of-day variation are not modeled. This is limitation 2 from Phase 1 and is still deferred to Phase 3.
