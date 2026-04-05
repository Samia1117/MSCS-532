import heapq
import math
import random
import time


# ########################################################
# Phase 3 - Emergency Response Dispatch System
# Optimization, Scaling, and Benchmarking
#
# Phase 2 left three items deferred:
#   1. Nearest-unit lookup was O(n * Dijkstra) - one full
#      Dijkstra run per available unit. Unacceptable at scale.
#   2. Road network was static - no way to update edge weights
#      for traffic or road closures.
#   3. No performance benchmarking at scale.
#
# Phase 3 addresses all three:
#   1. KDTree class - 2D spatial index. Each road network node
#      gets (x, y) coordinates. Available units are indexed by
#      their location's coordinates. Nearest-unit lookup queries
#      the k-d tree for the k Euclidean-nearest candidates
#      (O(log n)), then runs Dijkstra for those k only.
#      Total: O(n log n) rebuild + O(log n + k * Dijkstra)
#      vs Phase 2's O(n * Dijkstra).
#
#   2. RoadNetwork.update_weight(u, v, new_weight) - updates
#      edge weights in both directions. Dijkstra is re-run
#      on-demand per dispatch, so updated weights are always
#      reflected. A full incremental shortest-path algorithm
#      is out of scope but noted as a Phase 4 option.
#
#   3. Benchmarks on a 20x20 grid (400 nodes) with fleet sizes
#      10 to 200 units. Results show speedup of Phase 3 vs Phase 2
#      as fleet grows. Stress tests run 100+ dispatches.
#
# All Phase 2 classes are carried forward unchanged except
# RoadNetwork, which gains coordinate support and update_weight.
# ########################################################


# ------------------------------------------------------------
# EmergencyCall - unchanged from Phase 2
# ------------------------------------------------------------

class EmergencyCall:
    def __init__(self, call_id, priority, location, description=""):
        self.call_id     = call_id
        self.priority    = priority
        self.location    = location
        self.description = description
        self.active      = True

    def __repr__(self):
        labels = {1: "CRITICAL", 2: "URGENT", 3: "STANDARD"}
        label = labels.get(self.priority, str(self.priority))
        return f"Call({self.call_id}, {label}, loc={self.location})"


# ------------------------------------------------------------
# CallQueue - unchanged from Phase 2
# Custom min-heap with decrease_key via index_map.
# push/pop/decrease_key all O(log n).
# ------------------------------------------------------------

class CallQueue:

    def __init__(self):
        self._heap      = []
        self._index_map = {}

    def _swap(self, i, j):
        self._index_map[self._heap[i].call_id] = j
        self._index_map[self._heap[j].call_id] = i
        self._heap[i], self._heap[j] = self._heap[j], self._heap[i]

    def _parent(self, i): return (i - 1) // 2
    def _left(self, i):   return 2 * i + 1
    def _right(self, i):  return 2 * i + 2

    def _sift_up(self, i):
        while i > 0:
            p = self._parent(i)
            if self._heap[i].priority < self._heap[p].priority:
                self._swap(i, p)
                i = p
            else:
                break

    def _sift_down(self, i):
        n = len(self._heap)
        while True:
            smallest = i
            l, r = self._left(i), self._right(i)
            if l < n and self._heap[l].priority < self._heap[smallest].priority:
                smallest = l
            if r < n and self._heap[r].priority < self._heap[smallest].priority:
                smallest = r
            if smallest != i:
                self._swap(i, smallest)
                i = smallest
            else:
                break

    def push(self, call):
        if call.call_id in self._index_map:
            raise ValueError(f"call_id {call.call_id} already in queue")
        self._heap.append(call)
        idx = len(self._heap) - 1
        self._index_map[call.call_id] = idx
        self._sift_up(idx)

    def pop(self):
        if self.is_empty():
            return None
        self._swap(0, len(self._heap) - 1)
        call = self._heap.pop()
        del self._index_map[call.call_id]
        if not self.is_empty():
            self._sift_down(0)
        return call

    def peek(self):
        return self._heap[0] if self._heap else None

    def decrease_key(self, call_id, new_priority):
        if call_id not in self._index_map:
            raise KeyError(f"call_id {call_id} not in queue")
        idx = self._index_map[call_id]
        if new_priority >= self._heap[idx].priority:
            raise ValueError("decrease_key requires new_priority < current")
        self._heap[idx].priority = new_priority
        self._sift_up(idx)

    def is_empty(self): return len(self._heap) == 0
    def size(self):     return len(self._heap)


# ------------------------------------------------------------
# RoadNetwork - Phase 3 changes:
#   - Each location can have (x, y) coordinates (used by KDTree)
#   - Edges stored as mutable [neighbor, weight] lists so that
#     update_weight() can change them in-place without rebuilding
#     the entire adjacency list.
#   - update_weight(u, v, new_weight): O(degree(u) + degree(v))
#
# Dijkstra is still run on-demand per dispatch, so any weight
# update is reflected in the next shortest-path call automatically.
# This is simpler than maintaining an incremental shortest-path
# tree, and feasible as long as dispatches are not more frequent
# than weight updates (which is true in practice).
# ------------------------------------------------------------

class RoadNetwork:

    def __init__(self):
        self._adj    = {}   # location -> list of [neighbor, weight]  (mutable lists)
        self._coords = {}   # location -> (x, y)

    def add_location(self, name, coords=None):
        if name not in self._adj:
            self._adj[name] = []
        if coords is not None:
            self._coords[name] = coords

    def add_road(self, u, v, weight, u_coords=None, v_coords=None):
        self.add_location(u, u_coords)
        self.add_location(v, v_coords)
        self._adj[u].append([v, weight])
        self._adj[v].append([u, weight])

    def update_weight(self, u, v, new_weight):
        # Update edge weight in both directions. O(degree(u) + degree(v)).
        found = 0
        for edge in self._adj.get(u, []):
            if edge[0] == v:
                edge[1] = new_weight
                found += 1
        for edge in self._adj.get(v, []):
            if edge[0] == u:
                edge[1] = new_weight
                found += 1
        if found == 0:
            raise KeyError(f"no edge between {u} and {v}")

    def get_coords(self, name):
        return self._coords.get(name)

    def locations(self):
        return list(self._adj.keys())

    def shortest_path(self, src, dst):
        # Dijkstra's. O((V + E) log V).
        if src not in self._adj or dst not in self._adj:
            return float('inf'), []
        dist = {loc: float('inf') for loc in self._adj}
        prev = {loc: None         for loc in self._adj}
        dist[src] = 0
        heap = [(0, src)]
        while heap:
            d, u = heapq.heappop(heap)
            if d > dist[u]:
                continue
            if u == dst:
                break
            for v, w in self._adj[u]:
                alt = dist[u] + w
                if alt < dist[v]:
                    dist[v] = alt
                    prev[v] = u
                    heapq.heappush(heap, (alt, v))
        if dist[dst] == float('inf'):
            return float('inf'), []
        path, node = [], dst
        while node is not None:
            path.append(node)
            node = prev[node]
        path.reverse()
        return dist[dst], path


# ------------------------------------------------------------
# DispatchTable - unchanged from Phase 2
# ------------------------------------------------------------

class DispatchTable:

    def __init__(self):
        self._units = {}

    def register_unit(self, unit_id, unit_type, location):
        self._units[unit_id] = {
            'type':          unit_type,
            'location':      location,
            'status':        'available',
            'assigned_call': None,
        }

    def get_unit(self, unit_id):
        return self._units.get(unit_id)

    def update_status(self, unit_id, status, location=None, assigned_call=None):
        if unit_id not in self._units:
            raise KeyError(f"unit {unit_id} not registered")
        self._units[unit_id]['status'] = status
        if location      is not None: self._units[unit_id]['location']      = location
        if assigned_call is not None: self._units[unit_id]['assigned_call'] = assigned_call

    def mark_available(self, unit_id, location):
        self.update_status(unit_id, 'available', location, assigned_call=None)

    def get_available_units(self):
        return [uid for uid, info in self._units.items() if info['status'] == 'available']

    def all_units(self):
        return dict(self._units)


# ============================================================
# KDTree - NEW IN PHASE 3
#
# 2D spatial index over available unit positions.
#
# Why Euclidean nearest is a useful proxy for graph nearest:
# In a road network with roughly uniform edge density, the
# Euclidean nearest node is almost always the graph-nearest
# node too. Using k > 1 (defaulting to k=3) lets us check
# a small neighborhood that guards against cases where a
# river, highway, or road closure makes the Euclidean nearest
# unit unreachable or expensive in graph distance.
#
# Tree structure: standard axis-aligned 2D k-d tree, built
# by recursive median splitting. No balancing after build.
#
# Operations:
#   build(points): O(n log n) - points is list of ((x,y), unit_id)
#   nearest(query): O(log n) average, O(n) worst case
#   k_nearest(query, k): O(k log n) average
#
# Updates: rebuild from scratch after each dispatch (O(n log n)).
# For v1 this is simple and correct. A lazy-deletion approach
# could avoid rebuilds but adds complexity; deferred to v2.
# ============================================================

class _KDNode:
    __slots__ = ('point', 'unit_id', 'left', 'right')
    def __init__(self, point, unit_id, left=None, right=None):
        self.point   = point    # (x, y)
        self.unit_id = unit_id
        self.left    = left
        self.right   = right


def _euclid(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


class KDTree:

    def __init__(self):
        self._root = None
        self._n    = 0

    def build(self, points):
        # points: list of ((x, y), unit_id)
        self._root = self._build(list(points), depth=0)
        self._n    = len(points)

    def _build(self, points, depth):
        if not points:
            return None
        axis = depth % 2
        points.sort(key=lambda p: p[0][axis])
        mid = len(points) // 2
        return _KDNode(
            point   = points[mid][0],
            unit_id = points[mid][1],
            left    = self._build(points[:mid],   depth + 1),
            right   = self._build(points[mid+1:], depth + 1),
        )

    # 1-nearest neighbor
    def nearest(self, query):
        # Returns (unit_id, dist). O(log n) average.
        if self._root is None:
            return None, float('inf')
        best = [None, float('inf')]   # [unit_id, dist]
        self._nearest(self._root, query, 0, best)
        return best[0], best[1]

    def _nearest(self, node, query, depth, best):
        if node is None:
            return
        d = _euclid(node.point, query)
        if d < best[1]:
            best[0] = node.unit_id
            best[1] = d
        axis = depth % 2
        diff = query[axis] - node.point[axis]
        near, far = (node.left, node.right) if diff <= 0 else (node.right, node.left)
        self._nearest(near, query, depth + 1, best)
        # only visit far side if splitting plane is closer than current best
        if abs(diff) < best[1]:
            self._nearest(far, query, depth + 1, best)

    # k-nearest neighbors
    def k_nearest(self, query, k):
        # Returns list of (dist, unit_id) sorted by dist ascending, up to k entries.
        # Uses a max-heap of size k (stored as min-heap over negated distances).
        # O(k log n) average.
        if self._root is None:
            return []
        best = []   # heap entries: (-dist, unit_id)
        self._k_nearest(self._root, query, 0, best, k)
        # sort ascending by distance: entries are (-dist, uid), so sort descending
        # by the heap key (most negative = largest dist) to get closest first.
        best.sort(key=lambda x: x[0], reverse=True)
        return [(-neg_d, uid) for neg_d, uid in best]

    def _k_nearest(self, node, query, depth, best, k):
        if node is None:
            return
        d = _euclid(node.point, query)
        if len(best) < k:
            heapq.heappush(best, (-d, node.unit_id))
        elif d < -best[0][0]:   # closer than the current worst in the heap
            heapq.heapreplace(best, (-d, node.unit_id))
        axis = depth % 2
        diff = query[axis] - node.point[axis]
        near, far = (node.left, node.right) if diff <= 0 else (node.right, node.left)
        self._k_nearest(near, query, depth + 1, best, k)
        worst = -best[0][0] if best else float('inf')
        # visit far side if splitting plane is within worst distance, or heap not full
        if abs(diff) < worst or len(best) < k:
            self._k_nearest(far, query, depth + 1, best, k)

    def is_empty(self): return self._root is None
    def size(self):     return self._n


# ============================================================
# DispatchSystem - Phase 2 version, kept here for benchmarking.
# nearest-unit: Dijkstra for every available unit. O(n * Dijkstra).
# ============================================================

class DispatchSystem:

    def __init__(self, road_network, dispatch_table):
        self._queue   = CallQueue()
        self._network = road_network
        self._table   = dispatch_table
        self._log     = []

    def receive_call(self, call):
        self._queue.push(call)

    def dispatch_next(self):
        if self._queue.is_empty():
            return None
        call      = self._queue.pop()
        available = self._table.get_available_units()
        if not available:
            self._log.append({'call': call, 'unit': None,
                              'travel_time': None, 'note': 'no units available'})
            return None
        best_unit_id = None
        best_dist    = float('inf')
        best_path    = []
        for uid in available:
            unit = self._table.get_unit(uid)
            dist, path = self._network.shortest_path(unit['location'], call.location)
            if dist < best_dist:
                best_dist, best_unit_id, best_path = dist, uid, path
        if best_dist == float('inf'):
            self._log.append({'call': call, 'unit': None,
                              'travel_time': None, 'note': 'unreachable'})
            return None
        self._table.update_status(best_unit_id, 'dispatched',
                                  location=call.location, assigned_call=call.call_id)
        record = {'call': call, 'unit': best_unit_id,
                  'travel_time': best_dist, 'route': best_path, 'note': 'dispatched'}
        self._log.append(record)
        return record


# ============================================================
# OptimizedDispatchSystem - Phase 3 version
#
# Nearest-unit lookup uses KDTree to narrow candidates:
#   1. Pop highest-priority call.
#   2. Get call site coordinates.
#   3. Query KDTree for k Euclidean-nearest available units.
#   4. Run Dijkstra only for those k candidates.
#   5. Assign the unit with shortest graph distance.
#   6. Rebuild KDTree from remaining available units.
#
# Fallback: if no coordinates are set for a node, or the tree
# is empty, falls back to Phase 2 brute-force behavior.
#
# k is configurable (default 3). Larger k means more Dijkstra
# runs per dispatch but reduces the risk of missing the true
# graph-nearest unit when Euclidean and graph distances differ.
# ============================================================

class OptimizedDispatchSystem:

    def __init__(self, road_network, dispatch_table, k=3, verbose=True):
        self._queue   = CallQueue()
        self._network = road_network
        self._table   = dispatch_table
        self._log     = []
        self._k       = k
        self._verbose = verbose
        self._kdtree  = KDTree()
        self._rebuild_tree()

    def _rebuild_tree(self):
        # Rebuild from all currently available units. O(n log n).
        points = []
        for uid in self._table.get_available_units():
            loc    = self._table.get_unit(uid)['location']
            coords = self._network.get_coords(loc)
            if coords is not None:
                points.append((coords, uid))
        self._kdtree.build(points)

    def receive_call(self, call):
        self._queue.push(call)
        if self._verbose:
            print(f"  [RECEIVED] {call}")

    def retriage(self, call_id, new_priority):
        self._queue.decrease_key(call_id, new_priority)
        if self._verbose:
            print(f"  [RETRIAGE] call {call_id} -> priority {new_priority}")

    def dispatch_next(self):
        if self._queue.is_empty():
            if self._verbose:
                print("  [DISPATCH] queue empty")
            return None

        call      = self._queue.pop()
        available = self._table.get_available_units()

        if not available:
            record = {'call': call, 'unit': None, 'travel_time': None,
                      'route': [], 'note': 'no units available'}
            self._log.append(record)
            if self._verbose:
                print(f"  [DISPATCH] {call} -> NO UNITS AVAILABLE")
            return record

        call_coords = self._network.get_coords(call.location)
        use_kdtree  = (call_coords is not None and not self._kdtree.is_empty())

        if use_kdtree:
            # get top-k Euclidean candidates, then Dijkstra for those only
            raw        = self._kdtree.k_nearest(call_coords, self._k)
            candidates = [uid for _, uid in raw]   # k_nearest returns (dist, uid)
            if not candidates:
                candidates = available
        else:
            candidates = available   # fallback to Phase 2 behavior

        best_unit_id = None
        best_dist    = float('inf')
        best_path    = []

        for uid in candidates:
            unit = self._table.get_unit(uid)
            dist, path = self._network.shortest_path(unit['location'], call.location)
            if dist < best_dist:
                best_dist, best_unit_id, best_path = dist, uid, path

        if best_dist == float('inf'):
            record = {'call': call, 'unit': None, 'travel_time': None,
                      'route': [], 'note': 'call location unreachable'}
            self._log.append(record)
            if self._verbose:
                print(f"  [DISPATCH] {call} -> UNREACHABLE")
            return record

        self._table.update_status(best_unit_id, 'dispatched',
                                  location=call.location, assigned_call=call.call_id)
        self._rebuild_tree()

        record = {'call': call, 'unit': best_unit_id, 'travel_time': best_dist,
                  'route': best_path, 'note': 'dispatched'}
        self._log.append(record)

        if self._verbose:
            route_str = ' -> '.join(best_path)
            print(f"  [DISPATCH] {call} -> {best_unit_id} "
                  f"({self._table.get_unit(best_unit_id)['type']}) "
                  f"| travel={best_dist:.1f}min | route: {route_str}")
        return record

    def dispatch_all(self):
        while not self._queue.is_empty():
            self.dispatch_next()

    def print_log(self):
        print("\n  --- dispatch log ---")
        for i, r in enumerate(self._log):
            if r['unit']:
                print(f"  {i+1}. {r['call']} -> {r['unit']} "
                      f"({r['travel_time']:.1f}min) [{r['note']}]")
            else:
                print(f"  {i+1}. {r['call']} -> UNASSIGNED [{r['note']}]")

    def queue_size(self): return self._queue.size()


# ########################################################
# Helpers
# ########################################################

def build_city_network():
    # Same topology as Phase 2 with (x, y) coordinates added.
    # Coordinates are rough screen-space positions for the k-d tree.
    #
    #  HQ(0,2) ----5---- Hospital(2,3)
    #    |                    |
    #    3                    5
    #    |                    |
    #  Station_A(0,0) --4-- Midtown(2,1) --2-- Downtown(4,1)
    #      |                                       |
    #      6                                       3
    #      |                                       |
    #  Airport(-2,-2) --------7-------------- Riverside(4,-1)
    #                                              |
    #                                              4
    #                                              |
    #                                          Uptown(4,-3)
    #
    net = RoadNetwork()
    net.add_road("HQ",        "Hospital",  5, (0, 2),   (2, 3))
    net.add_road("HQ",        "Station_A", 3, (0, 2),   (0, 0))
    net.add_road("Hospital",  "Midtown",   5, (2, 3),   (2, 1))
    net.add_road("Station_A", "Midtown",   4, (0, 0),   (2, 1))
    net.add_road("Station_A", "Airport",   6, (0, 0),   (-2, -2))
    net.add_road("Midtown",   "Downtown",  2, (2, 1),   (4, 1))
    net.add_road("Downtown",  "Riverside", 3, (4, 1),   (4, -1))
    net.add_road("Airport",   "Riverside", 7, (-2, -2), (4, -1))
    net.add_road("Riverside", "Uptown",    4, (4, -1),  (4, -3))
    return net


def build_unit_table():
    table = DispatchTable()
    table.register_unit("AMB_1",    "Ambulance",  "Hospital")
    table.register_unit("AMB_2",    "Ambulance",  "Station_A")
    table.register_unit("FIRE_1",   "Fire Truck", "HQ")
    table.register_unit("POLICE_1", "Police Car", "Midtown")
    table.register_unit("POLICE_2", "Police Car", "Downtown")
    return table


def build_grid_network(rows, cols, weight_seed=42):
    # rows x cols grid. Node names: "r{i}c{j}". Coordinates: (j, rows-1-i).
    # Horizontal and vertical edges with random weights 1-10.
    rng = random.Random(weight_seed)
    net = RoadNetwork()
    for i in range(rows):
        for j in range(cols):
            net.add_location(f"r{i}c{j}", coords=(j, rows - 1 - i))
    for i in range(rows):
        for j in range(cols):
            if j + 1 < cols:
                net.add_road(f"r{i}c{j}", f"r{i}c{j+1}", rng.randint(1, 10))
            if i + 1 < rows:
                net.add_road(f"r{i}c{j}", f"r{i+1}c{j}", rng.randint(1, 10))
    return net


def build_random_unit_table(network, n_units, seed=0):
    rng   = random.Random(seed)
    locs  = network.locations()
    table = DispatchTable()
    for i in range(n_units):
        table.register_unit(f"U{i:03d}", "Unit", rng.choice(locs))
    return table


# ########################################################
# Tests
# ########################################################

if __name__ == "__main__":

    # ============================================
    # Test 1: KDTree - 1-nearest and k-nearest correctness
    # ============================================
    print("=== Test 1: KDTree nearest-neighbor ===\n")

    kd = KDTree()
    pts = [
        ((0.0, 0.0), "A"),
        ((3.0, 1.0), "B"),
        ((1.0, 4.0), "C"),
        ((5.0, 2.0), "D"),
        ((2.0, 2.0), "E"),
    ]
    kd.build(pts)

    # 1-nearest
    uid, dist = kd.nearest((2.1, 2.1))
    print(f"  1-nearest to (2.1, 2.1): {uid} dist={dist:.3f}  (expected E at ~0.14)")
    print(f"  correct: {uid == 'E'}")

    uid2, dist2 = kd.nearest((5.5, 2.5))
    print(f"  1-nearest to (5.5, 2.5): {uid2} dist={dist2:.3f}  (expected D at ~0.71)")
    print(f"  correct: {uid2 == 'D'}")

    # k-nearest returns [(dist, uid), ...] sorted ascending by dist
    k2 = kd.k_nearest((2.1, 2.1), 2)
    print(f"  2-nearest to (2.1, 2.1): {[(uid, round(d,3)) for d,uid in k2]}")
    print(f"  first is E (closest): {k2[0][1] == 'E'}")

    # boundary: k > number of points
    k10 = kd.k_nearest((2.0, 2.0), 10)
    print(f"  k=10 on 5-point tree returns {len(k10)} results (expected 5)")

    # empty tree
    kd_empty = KDTree()
    uid_e, dist_e = kd_empty.nearest((0.0, 0.0))
    print(f"  empty tree nearest: uid={uid_e}, dist={dist_e}  (expected None, inf)")
    print()

    # ============================================
    # Test 2: Dynamic edge weight update (RoadNetwork.update_weight)
    # ============================================
    print("=== Test 2: Dynamic edge weight update ===\n")

    net2 = build_city_network()

    dist_before, path_before = net2.shortest_path("HQ", "Downtown")
    print(f"  HQ->Downtown before: {dist_before:.0f}min  {' -> '.join(path_before)}")
    # expected: HQ -> Station_A -> Midtown -> Downtown  = 3+4+2 = 9

    # simulate rush-hour traffic: HQ-Station_A and Station_A-Midtown slow way down
    net2.update_weight("HQ", "Station_A",  9)   # was 3
    net2.update_weight("Station_A", "Midtown", 12)  # was 4

    dist_after, path_after = net2.shortest_path("HQ", "Downtown")
    print(f"  HQ->Downtown after traffic: {dist_after:.0f}min  {' -> '.join(path_after)}")
    # now HQ -> Hospital -> Midtown -> Downtown = 5+5+2 = 12, vs congested 9+12+2=23
    print(f"  route changed: {path_before != path_after}")

    # restore and verify
    net2.update_weight("HQ", "Station_A", 3)
    net2.update_weight("Station_A", "Midtown", 4)
    dist_restored, _ = net2.shortest_path("HQ", "Downtown")
    print(f"  restored: {dist_restored:.0f}min  (expected 9)")
    print(f"  correct: {dist_restored == 9}")

    # error on nonexistent edge
    try:
        net2.update_weight("HQ", "Downtown", 1)
        print("  ERROR: should have raised KeyError")
    except KeyError as e:
        print(f"  nonexistent edge raises KeyError: correct")
    print()

    # ============================================
    # Test 3: OptimizedDispatchSystem end-to-end on city network
    # ============================================
    print("=== Test 3: OptimizedDispatchSystem end-to-end ===\n")

    net3 = build_city_network()
    tbl3 = build_unit_table()
    sys3 = OptimizedDispatchSystem(net3, tbl3, k=3)

    print("  receiving calls:")
    sys3.receive_call(EmergencyCall("E001", 3, "Airport",   "minor incident"))
    sys3.receive_call(EmergencyCall("E002", 2, "Riverside", "car collision"))
    sys3.receive_call(EmergencyCall("E003", 1, "Downtown",  "cardiac arrest"))

    print(f"\n  queue size: {sys3.queue_size()}  (expected 3)")
    print("\n  dispatching all:")
    sys3.dispatch_all()
    sys3.print_log()

    # E003 (critical) should be dispatched first
    first = sys3._log[0]
    print(f"\n  first dispatched call: {first['call'].call_id}  (expected E003)")
    print(f"  correct: {first['call'].call_id == 'E003'}")
    print()

    # ============================================
    # Test 4: k-d tree vs brute-force - dispatch decisions match
    # ============================================
    print("=== Test 4: k-d tree accuracy vs brute-force ===\n")

    net4 = build_city_network()
    tbl4 = build_unit_table()

    # build k-d tree from all available units
    available4 = tbl4.get_available_units()
    kd4 = KDTree()
    kd4.build([(net4.get_coords(tbl4.get_unit(u)['location']), u) for u in available4])

    call_locs = ["Airport", "Uptown", "Downtown", "Hospital", "Midtown", "Riverside"]
    all_match = True

    for call_loc in call_locs:
        # brute-force: min Dijkstra over ALL units
        bf_best  = min(available4,
                       key=lambda u: net4.shortest_path(tbl4.get_unit(u)['location'], call_loc)[0])
        bf_dist, _ = net4.shortest_path(tbl4.get_unit(bf_best)['location'], call_loc)

        # k-d tree: top-3 candidates + Dijkstra
        ccoords = net4.get_coords(call_loc)
        cands   = [uid for _, uid in kd4.k_nearest(ccoords, 3)]
        kd_best = min(cands,
                      key=lambda u: net4.shortest_path(tbl4.get_unit(u)['location'], call_loc)[0])
        kd_dist, _ = net4.shortest_path(tbl4.get_unit(kd_best)['location'], call_loc)

        match     = (bf_dist == kd_dist)
        all_match = all_match and match
        print(f"  call@{call_loc:<12}: bf={bf_best}({bf_dist:.1f}min)  kd={kd_best}({kd_dist:.1f}min)  match={match}")

    print(f"\n  all decisions match brute-force: {all_match}")
    print()

    # ============================================
    # Test 5: Stress test - 100 dispatches on grid, no crashes
    # ============================================
    print("=== Test 5: Stress test - 100 dispatches on 10x10 grid ===\n")

    stress_net   = build_grid_network(10, 10, weight_seed=1)
    stress_locs  = stress_net.locations()
    stress_tbl   = build_random_unit_table(stress_net, 30, seed=5)
    stress_sys   = OptimizedDispatchSystem(stress_net, stress_tbl, k=3, verbose=False)

    rng_stress = random.Random(77)
    dispatched = returned = 0

    # queue 100 calls
    for i in range(100):
        loc  = rng_stress.choice(stress_locs)
        pri  = rng_stress.randint(1, 3)
        stress_sys.receive_call(EmergencyCall(f"S{i:03d}", pri, loc))

    # dispatch until queue empty, periodically free units
    call_idx = 0
    while not stress_sys._queue.is_empty():
        r = stress_sys.dispatch_next()
        if r and r['unit']:
            dispatched += 1
            # return the unit to a random location after every 5 dispatches
            if dispatched % 5 == 0:
                uid = r['unit']
                new_loc = rng_stress.choice(stress_locs)
                stress_sys._table.mark_available(uid, new_loc)
                stress_sys._rebuild_tree()
                returned += 1

    total_logged = len(stress_sys._log)
    print(f"  calls logged: {total_logged}  (expected 100)")
    print(f"  dispatched: {dispatched}, returned to service: {returned}")
    print(f"  no crashes: True")
    print()

    # ============================================
    # Test 6: Benchmark - Phase 2 vs Phase 3 at scale
    # ============================================
    print("=== Test 6: Benchmark - Phase 2 vs Phase 3 ===\n")

    GRID_ROWS   = 20
    GRID_COLS   = 20
    FLEET_SIZES = [10, 25, 50, 100, 200]
    N_CALLS     = 15
    REPEATS     = 3

    bench_net = build_grid_network(GRID_ROWS, GRID_COLS, weight_seed=42)
    all_locs  = bench_net.locations()
    rng_bench = random.Random(13)

    # pregenerate call locations (same for all trials)
    call_locs_bench = [rng_bench.choice(all_locs) for _ in range(N_CALLS)]

    print(f"  grid: {GRID_ROWS}x{GRID_COLS} = {GRID_ROWS*GRID_COLS} nodes, "
          f"~{GRID_ROWS*(GRID_COLS-1)*2} edges")
    print(f"  calls per trial: {N_CALLS}, repeats: {REPEATS}")
    print()
    print(f"  {'Fleet':>6}  {'Phase2 ms/call':>16}  {'Phase3 ms/call':>16}  {'Speedup':>8}")
    print(f"  {'-'*6}  {'-'*16}  {'-'*16}  {'-'*8}")

    for fleet_size in FLEET_SIZES:
        t2_total = 0.0
        t3_total = 0.0

        for rep in range(REPEATS):
            # fresh tables each repeat (same seed = same unit positions)
            tbl2 = build_random_unit_table(bench_net, fleet_size, seed=rep*100)
            tbl3 = build_random_unit_table(bench_net, fleet_size, seed=rep*100)

            # Phase 2
            sys2 = DispatchSystem(bench_net, tbl2)
            for i, loc in enumerate(call_locs_bench):
                sys2.receive_call(EmergencyCall(f"B{rep}_{i}", 2, loc))
            t2_s = time.perf_counter()
            while not sys2._queue.is_empty():
                sys2.dispatch_next()
            t2_total += time.perf_counter() - t2_s

            # Phase 3
            sys3b = OptimizedDispatchSystem(bench_net, tbl3, k=3, verbose=False)
            for i, loc in enumerate(call_locs_bench):
                sys3b.receive_call(EmergencyCall(f"B{rep}_{i}", 2, loc))
            t3_s = time.perf_counter()
            while not sys3b._queue.is_empty():
                sys3b.dispatch_next()
            t3_total += time.perf_counter() - t3_s

        actual_calls = REPEATS * N_CALLS
        t2_per  = t2_total / actual_calls * 1000
        t3_per  = t3_total / actual_calls * 1000
        speedup = t2_per / t3_per if t3_per > 0 else float('inf')
        print(f"  {fleet_size:>6}  {t2_per:>14.3f}ms  {t3_per:>14.3f}ms  {speedup:>7.1f}x")

    print()
    print("  Note: Phase 3 time includes k-d tree rebuild after each dispatch.")
    print("  Speedup grows with fleet size because Phase 2 scales as O(n*Dijkstra)")
    print("  while Phase 3 scales as O(n log n rebuild + k*Dijkstra), k=3.")
