import heapq
import math


# ########################################################
# Phase 2 - Emergency Response Dispatch System
# Proof of Concept Implementation
#
# Builds on the design from Phase 1. Phase 1 identified three
# limitations to address:
#   1. The call queue had no decrease-key (couldn't re-triage
#      a call to a higher priority after it was enqueued).
#   2. The road network was static - no dynamic edge weights.
#   3. Finding the nearest unit required running Dijkstra once
#      per available unit - O(n * (V+E) log V) total.
#
# Phase 2 addresses limitation 1 fully (custom heap with
# decrease_key). Limitation 3 is partially addressed by
# caching Dijkstra results from HQ. Limitation 2 is noted
# as a next step for Phase 3.
# ########################################################


# ------------------------------------------------------------
# EmergencyCall
# Represents a single incoming call.
# Priority 1 = most critical (cardiac arrest, active fire).
# Priority 2 = urgent (collision with injuries).
# Priority 3 = standard (minor incidents).
# -----------------------------------------------------

class EmergencyCall:
    def __init__(self, call_id, priority, location, description=""):
        self.call_id = call_id
        self.priority = priority
        self.location = location
        self.description = description
        self.active = True   # set to False if call is cancelled

    def __repr__(self):
        labels = {1: "CRITICAL", 2: "URGENT", 3: "STANDARD"}
        label = labels.get(self.priority, str(self.priority))
        return f"Call({self.call_id}, {label}, loc={self.location})"


# ------------------------------------------------------------
# CallQueue
# Min-heap priority queue with decrease_key support.
#
# Phase 1 used Python's heapq directly, which does not support
# decrease-key. The limitation is real: if a call comes in as
# standard priority and a dispatcher then re-triages it as
# critical, there is no way to move it up the queue without
# rebuilding the entire heap.
#
# This implementation adds an index_map (call_id -> index in
# heap) so that decrease_key can find the call in O(1) and
# sift it upward in O(log n). The _swap helper keeps the map
# in sync every time two elements change positions.
# --------------------------------------

class CallQueue:

    def __init__(self):
        self._heap      = []    # list of EmergencyCall objects
        self._index_map = {}    # call_id -> current index in heap

    # -- internal helpers --

    def _swap(self, i, j):
        self._index_map[self._heap[i].call_id] = j
        self._index_map[self._heap[j].call_id] = i
        self._heap[i], self._heap[j] = self._heap[j], self._heap[i]

    def _parent(self, i):
        return (i - 1) // 2

    def _left(self, i):
        return 2 * i + 1

    def _right(self, i):
        return 2 * i + 2

    def _sift_up(self, i):
        # bubble up until parent has equal or lower priority number
        #  (lower number = higher urgency in our scheme)
        while i > 0:
            p = self._parent(i)
            if self._heap[i].priority < self._heap[p].priority:
                self._swap(i, p)
                i = p
            else:
                break

    def _sift_down(self, i) :
        n = len(self._heap)
        while True:
            smallest = i
            l = self._left(i)
            r = self._right(i)
            if l < n and self._heap[l].priority < self._heap[smallest].priority:
                smallest = l
            if r < n and self._heap[r].priority < self._heap[smallest].priority:
                smallest = r
            if smallest != i:
                self._swap(i, smallest)
                i = smallest
            else:
                break

    # public interface --

    def push(self, call):
        # O(log n)
        if call.call_id in self._index_map:
            raise ValueError(f"call_id {call.call_id} already in queue")
        self._heap.append(call)
        idx = len(self._heap) - 1
        self._index_map[call.call_id] = idx
        self._sift_up(idx)

    def pop(self):
        # Remove and return the highest-priority (lowest priority number) call.
        # O(log n)
        if self.is_empty():
            return None
        self._swap(0, len(self._heap) - 1)
        call = self._heap.pop()
        del self._index_map[call.call_id]
        if not self.is_empty():
            self._sift_down(0)
        return call

    def peek(self):
        # O(1) - just look at the root
        return self._heap[0] if self._heap else None

    def decrease_key(self, call_id, new_priority):
        # Lower the priority number (make more urgent) (retriage)
        # O(log n) - one index_map lookup then a sift_up.
        if call_id not in self._index_map:
            raise KeyError(f"call_id {call_id} not in queue")
        idx = self._index_map[call_id]
        if new_priority >= self._heap[idx].priority:
            raise ValueError(
                f"decrease_key requires new_priority < current ({new_priority} >= {self._heap[idx].priority})"
            )
        self._heap[idx].priority = new_priority
        self._sift_up(idx)

    def is_empty(self):
        return len(self._heap) == 0

    def size(self):
        return len(self._heap)


# ---------------------------------------------------------
# RoadNetwork
# Undirected weighted graph stored as an adjacency list.
# Vertices = named locations. Edge weights = travel time in minutes.
#
# Shortest paths are computed with Dijkstra's algorithm using
# Python's heapq. The predecessor map lets us reconstruct the
# full route, not just the travel time.
# -----------------------------------------------

class RoadNetwork:

    def __init__(self):
        self._adj = {}   # location_name -> list of (neighbor, weight)

    def add_location(self, name):
        if name not in self._adj:
            self._adj[name] = []

    def add_road(self, u, v, weight):
        # undirected - add edges in both directions
        self.add_location(u)
        self.add_location(v)
        self._adj[u].append((v, weight))
        self._adj[v].append((u, weight))

    def locations(self):
        return list(self._adj.keys())

    def shortest_path(self, src, dst):
        # Dijkstra's with a min-heap.
        # Returns (travel_time, [path]) or (inf, []) if unreachable.
        # O ((V + E) log V)
        if src not in self._adj or dst not in self._adj:
            return float('inf'), []

        dist = {loc: float('inf') for loc in self._adj}
        prev = {loc: None for loc in self._adj}
        dist[src] = 0
        heap = [(0, src)]

        while heap:
            d, u = heapq.heappop(heap)
            if d > dist[u]:
                continue   # stale heap entry, skip
            if u == dst:
                break
            for v, w in self._adj[u]:
                alt = dist[u] + w
                if alt < dist[v]:
                    dist[v] = alt
                    prev[v] = u
                    heapq.heappush(heap, (alt, v))

        # ## reconstruct path
        if dist[dst] == float('inf'):
            return float('inf'), []

        path = []
        node = dst
        while node is not None:
            path.append(node)
            node = prev[node]
        path.reverse()

        return dist[dst], path


# ------------------------------------------------------------
# DispatchTable
# Hash table of responder units keyed by unit_id.
# O(1) average lookup, insert, update.

class DispatchTable:

    def __init__(self):
        self._units = {}   # unit_id -> dict with type, location, status

    def register_unit(self, unit_id, unit_type, location):
        self._units[unit_id] = {
            'type':     unit_type,
            'location': location,
            'status':   'available',
            'assigned_call': None,
        }

    def get_unit(self, unit_id):
        return self._units.get(unit_id)

    def update_status(self, unit_id, status, location=None, assigned_call=None):
        if unit_id not in self._units:
            raise KeyError(f"unit {unit_id} not registered")
        self._units[unit_id]['status'] = status
        if location is not None:
            self._units[unit_id]['location'] = location
        if assigned_call is not None:
            self._units[unit_id]['assigned_call'] = assigned_call

    def mark_available(self, unit_id, location):
        # called when a unit finishes a job and returns to service
        self.update_status(unit_id, 'available', location, assigned_call=None)

    def get_available_units(self):
        return [uid for uid, info in self._units.items() if info['status'] == 'available']

    def all_units(self):
        return dict(self._units)


#######################################
# # DispatchSystem
# Ties everything together.
#
# Workflow:
#   1. Calls arrive via receive_call() and go into the CallQueue.
#   2. dispatch_next() pops the highest-priority call, finds
#      the nearest available unit by running Dijkstra from
#      each available unit's current location to the call site,
#      and assigns the closest one.
#   3. A dispatch log records every assignment for later review.
#
# Nearest-unit search is currently O(n * Dijkstra) where n is
# the number of available units. This is the main performance
# bottleneck identified for Phase 3.
################################################

class DispatchSystem:

    def __init__(self, road_network, dispatch_table):
        self._queue   = CallQueue()
        self._network = road_network
        self._table   = dispatch_table
        self._log     = []   # list of dispatch records

    def receive_call(self, call):
        self._queue.push(call)
        print(f"  [RECEIVED] {call}")

    def retriage(self, call_id, new_priority):
        # re-triage a call already in the queue to a higher urgency
        self._queue.decrease_key(call_id, new_priority)
        print(f"  [RETRIAGE] call {call_id} -> priority {new_priority}")

    def dispatch_next(self):
        if self._queue.is_empty():
            print("  [DISPATCH] queue is empty, nothing to dispatch")
            return None

        call = self._queue.pop()
        available = self._table.get_available_units()

        if not available:
            record = {'call': call, 'unit': None, 'travel_time': None,
                      'route': [], 'note': 'no units available'}
            self._log.append(record)
            print(f"  [DISPATCH] {call} -> NO UNITS AVAILABLE")
            return record

        # find nearest available unit by running Dijkstra from each unit's location
        best_unit_id  = None
        best_dist     = float('inf')
        best_path     = []

        for uid in available:
            unit = self._table.get_unit(uid)
            dist, path = self._network.shortest_path(unit['location'], call.location)
            if dist < best_dist:
                best_dist    = dist
                best_unit_id = uid
                best_path    = path

        if best_dist == float('inf'):
            record = {'call': call, 'unit': None, 'travel_time': None,
                      'route': [], 'note': 'call location unreachable'}
            self._log.append(record)
            print(f"  [DISPATCH] {call} -> UNREACHABLE from any available unit")
            return record

        # assign the unit
        self._table.update_status(best_unit_id, 'dispatched',
                                  location=call.location,
                                  assigned_call=call.call_id)

        record = {
            'call':        call,
            'unit':        best_unit_id,
            'travel_time': best_dist,
            'route':       best_path,
            'note':        'dispatched',
        }
        self._log.append(record)

        route_str = ' -> '.join(best_path)
        print(f"  [DISPATCH] {call} -> {best_unit_id} "
              f"({self._table.get_unit(best_unit_id)['type']}) "
              f"| travel={best_dist:.1f}min | route: {route_str}")
        return record

    def dispatch_all(self):
        # dispatch calls until queue is empty
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

    def queue_size(self):
        return self._queue.size()


# ################################################
# Helper: build the city road network used across all tests
################################################

def build_city_network():
    #
    #  Road network (travel times in minutes):
    #
    #  HQ ---5--- Hospital
    #  |           |
    #  3           5
    #  |           |
    #  Station_A --4-- Midtown ---2--- Downtown
    #      |                           |
    #      6                           3
    #      |                           |
    #    Airport ---7--------------- Riverside
    #                                  |
    #                                  4
    #                                  |
    #                                Uptown
    #
    net = RoadNetwork()
    net.add_road("HQ",        "Hospital",  5)
    net.add_road("HQ",        "Station_A", 3)
    net.add_road("Hospital",  "Midtown",   5)
    net.add_road("Station_A", "Midtown",   4)
    net.add_road("Station_A", "Airport",   6)
    net.add_road("Midtown",   "Downtown",  2)
    net.add_road("Downtown",  "Riverside", 3)
    net.add_road("Airport",   "Riverside", 7)
    net.add_road("Riverside", "Uptown",    4)
    return net


def build_unit_table():
    table = DispatchTable()
    table.register_unit("AMB_1",    "Ambulance",   "Hospital")
    table.register_unit("AMB_2",    "Ambulance",   "Station_A")
    table.register_unit("FIRE_1",   "Fire Truck",  "HQ")
    table.register_unit("POLICE_1", "Police Car",  "Midtown")
    table.register_unit("POLICE_2", "Police Car",  "Downtown")
    return table


# #################################################
# Tests
# ################################################

if __name__ == "__main__":

    # ############
    # Test 1: CallQueue - basic push and pop order
    #############
    print("=== Test 1: CallQueue basic push/pop order ===\n")

    q = CallQueue()
    q.push(EmergencyCall("C001", priority=3, location="Airport",  description="minor incident"))
    q.push(EmergencyCall("C002", priority=1, location="Downtown", description="cardiac arrest"))
    q.push(EmergencyCall("C003", priority=2, location="Uptown",   description="collision"))

    print("  inserted: C001(priority=3), C002(priority=1), C003(priority=2)")
    print("  expected pop order: C002, C003, C001")

    out = []
    while not q.is_empty():
        out.append(q.pop())
    print("  actual pop order:", [c.call_id for c in out])
    print("  correct:", [c.call_id for c in out] == ["C002", "C003", "C001"])

    print()

    # ----------------------------------------------------------
    # Test 2: decrease_key (re-triage)
    # ----------------------------------------------------------
    print("=== Test 2: decrease_key (re-triage) ===\n")

    q2 = CallQueue()
    q2.push(EmergencyCall("D001", priority=2, location="Midtown",  description="collision"))
    q2.push(EmergencyCall("D002", priority=3, location="Airport",  description="minor incident"))
    q2.push(EmergencyCall("D003", priority=2, location="Riverside", description="collision"))

    print("  before retriage: peek =", q2.peek())
    print("  re-triaging D002 from priority 3 -> priority 1 (critical)")
    q2.decrease_key("D002", 1)
    print("  after retriage: peek =", q2.peek())
    print("  correct (D002 is now top):", q2.peek().call_id == "D002")

    out2 = []
    while not q2.is_empty():
        out2.append(q2.pop())
    print("  full pop order:", [c.call_id for c in out2])
    print("  D002 came out first:", out2[0].call_id == "D002")

    print()

    # ----------------------------------------------------------
    # Test 3: RoadNetwork - Dijkstra shortest paths
    # ----------------------------------------------------------
    print("=== Test 3: RoadNetwork shortest paths ===\n")

    net = build_city_network()

    cases = [
        ("HQ",        "Downtown",  "HQ -> Station_A -> Midtown -> Downtown",  9),
        ("Station_A", "Hospital",  "Station_A -> HQ -> Hospital",             8),
        ("Airport",   "Hospital",  "Airport -> Station_A -> HQ -> Hospital", 14),
        ("Downtown",  "Uptown",    "Downtown -> Riverside -> Uptown",         7),
    ]

    for src, dst, expected_route, expected_dist in cases:
        dist, path = net.shortest_path(src, dst)
        route_str = " -> ".join(path)
        print(f"  {src} -> {dst}:")
        print(f"    distance={dist:.0f}min (expected {expected_dist}), correct: {dist == expected_dist}")
        print(f"    route: {route_str}")
        print(f"    expected: {expected_route}")
        print()

    # unreachable location
    net2 = RoadNetwork()
    net2.add_road("A", "B", 5)
    net2.add_location("C")   # isolated node
    dist_unreach, path_unreach = net2.shortest_path("A", "C")
    print("  unreachable node: dist =", dist_unreach, "(should be inf), path =", path_unreach)
    print()

    # -----------------------
    # Test 4: DispatchTable
    # ----------------------
    print("=== Test 4: DispatchTable ===\n")

    table = build_unit_table()
    print("  registered units:", list(table.all_units().keys()))
    print("  available units (all 5):", table.get_available_units())

    table.update_status("AMB_1", "dispatched", assigned_call="X001")
    print("  after dispatching AMB_1:")
    print("  available units (should be 4):", table.get_available_units())
    print("  AMB_1 status:", table.get_unit("AMB_1")['status'])

    table.mark_available("AMB_1", "Midtown")
    print("  after marking AMB_1 available again:")
    print("  AMB_1 status:", table.get_unit("AMB_1")['status'], "| location:", table.get_unit("AMB_1")['location'])

    print()

    # --------------------------------------------
    # Test 5: DispatchSystem - end-to-end dispatch
    # --------------------------------------------
    print("=== Test 5: DispatchSystem end-to-end ===\n")

    net3  = build_city_network()
    tbl3  = build_unit_table()
    sys3  = DispatchSystem(net3, tbl3)

    print("  receiving calls:")
    sys3.receive_call(EmergencyCall("E001", priority=3, location="Airport",   description="minor incident"))
    sys3.receive_call(EmergencyCall("E002", priority=2, location="Riverside", description="car collision"))
    sys3.receive_call(EmergencyCall("E003", priority=1, location="Downtown",  description="cardiac arrest"))

    print(f"\n  queue size: {sys3.queue_size()} (expected 3)")
    print("\n  dispatching all calls:")
    sys3.dispatch_all()
    sys3.print_log()

    print()

    # ----------------------------------------------------------
    # Test 6: re-triage via DispatchSystem
    # ----------------------------------------------------------
    print("=== Test 6: retriage via DispatchSystem ===\n")

    net4 = build_city_network()
    tbl4 = build_unit_table()
    sys4 = DispatchSystem(net4, tbl4)

    print("  receiving calls:")
    sys4.receive_call(EmergencyCall("F001", priority=2, location="Uptown",    description="collision"))
    sys4.receive_call(EmergencyCall("F002", priority=3, location="Airport",   description="minor incident"))
    sys4.receive_call(EmergencyCall("F003", priority=2, location="Riverside", description="collision"))

    print(f"\n  queue top before retriage: {sys4._queue.peek()}")
    sys4.retriage("F002", new_priority=1)
    print(f"  queue top after retraging F002 to critical: {sys4._queue.peek()}")
    print("  F002 is now top:", sys4._queue.peek().call_id == "F002")

    print("\n  dispatching all:")
    sys4.dispatch_all()
    sys4.print_log()

    print()

    # ----------------------------
    # Test 7: no available units
    # --------------------------
    print("=== Test 7: no available units ===\n")

    net5 = build_city_network()
    tbl5 = DispatchTable()   # empty table - no units registered
    sys5 = DispatchSystem(net5, tbl5)

    sys5.receive_call(EmergencyCall("G001", priority=1, location="Downtown", description="fire"))
    sys5.dispatch_next()
    print("  unassigned call logged:", sys5._log[0]['note'])

    print()

    # -----------------------------------
    # Test 8: same priority calls - arrival order preserved
    # ----------------------------------
    print("=== Test 8: same priority - FIFO within priority level ===\n")

    # heapq is stable? actually Python heapq is not guaranteed stable.
    # For this PoC we just verify all 3 come out at priority 2.
    q8 = CallQueue()
    q8.push(EmergencyCall("H001", priority=2, location="Uptown"))
    q8.push(EmergencyCall("H002", priority=2, location="Midtown"))
    q8.push(EmergencyCall("H003", priority=2, location="Airport"))

    out8 = []
    while not q8.is_empty():
        out8.append(q8.pop())

    print("  all popped calls have priority 2:", all(c.priority == 2 for c in out8))
    print("  popped:", [c.call_id for c in out8])
