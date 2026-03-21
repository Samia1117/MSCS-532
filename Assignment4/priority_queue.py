import random


# Priority queue backed by a max-heap.
# "max priority" means the task with the highest priority number gets served first.
#
# The heap is stored as a plain list. For a node at index i:
#   left child  -> 2*i + 1
#   right child -> 2*i + 2
#   parent      -> (i - 1) // 2
#
# We also keep an index_map (dict: task_id -> position in heap list) so that
# increase_key and decrease_key can find a task in O(1) instead of scanning
# through the whole heap. Without the map, those operations would be O(n).


class Task:
    # Represents a single task in the scheduler.
    # priority is the number we sort by - higher = served sooner.

    def __init__(self, task_id, priority, arrival_time=0, deadline=None, description=""):
        self.task_id      = task_id
        self.priority     = priority
        self.arrival_time = arrival_time
        self.deadline     = deadline
        self.description  = description

    def __repr__(self):
        return f"Task(id={self.task_id}, priority={self.priority})"


class MaxHeapPriorityQueue:

    def __init__(self):
        self.heap      = []   # list of Task objects
        self.index_map = {}   # task_id -> current index in self.heap

    # --- internal helpers ---

    def _parent(self, i):
        return (i - 1) // 2

    def _left(self, i):
        return 2 * i + 1

    def _right(self, i):
        return 2 * i + 2

    def _swap(self, i, j):
        # swap the two tasks and keep index_map in sync
        self.index_map[self.heap[i].task_id] = j
        self.index_map[self.heap[j].task_id] = i
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]

    def _sift_up(self, i):
        # bubble node at i upward until the heap property holds
        # (parent is >= node, or we reach the root)
        while i > 0:
            p = self._parent(i)
            if self.heap[i].priority > self.heap[p].priority:
                self._swap(i, p)
                i = p
            else:
                break   # already in the right place

    def _sift_down(self, i):
        # push node at i downward until the heap property holds
        # (node is >= both children, or we reach a leaf)
        n = len(self.heap)
        while True:
            largest = i
            l = self._left(i)
            r = self._right(i)

            if l < n and self.heap[l].priority > self.heap[largest].priority:
                largest = l
            if r < n and self.heap[r].priority > self.heap[largest].priority:
                largest = r

            if largest != i:
                self._swap(i, largest)
                i = largest
            else:
                break   # heap property holds here, done

    # --- public operations ---

    def is_empty(self):
        # O(1)
        return len(self.heap) == 0

    def insert(self, task):
        # Add a new task. Put it at the end, then bubble it up.
        # O(log n) because sift_up traverses at most one root-to-leaf path.
        if task.task_id in self.index_map:
            raise ValueError(f"task_id '{task.task_id}' is already in the queue")

        self.heap.append(task)
        idx = len(self.heap) - 1
        self.index_map[task.task_id] = idx
        self._sift_up(idx)

    def extract_max(self):
        # Remove and return the highest-priority task.
        # Swap root with the last element, pop the last element,
        # then push the new root down to restore the heap property.
        # O(log n).
        if self.is_empty():
            return None

        # swap root (max) with the last element
        self._swap(0, len(self.heap) - 1)

        # remove the max (it is now at the end)
        task = self.heap.pop()
        del self.index_map[task.task_id]

        # fix the heap (only if something is left)
        if not self.is_empty():
            self._sift_down(0)

        return task

    def peek(self):
        # Look at the highest-priority task without removing it.
        # O(1).
        if self.is_empty():
            return None
        return self.heap[0]

    def increase_key(self, task_id, new_priority):
        # Raise the priority of an existing task.
        # After raising it, sift it up because it might now be larger
        # than its parent.
        # O(log n).
        if task_id not in self.index_map:
            raise KeyError(f"task_id '{task_id}' not found in queue")

        idx = self.index_map[task_id]

        if new_priority < self.heap[idx].priority:
            raise ValueError(
                f"increase_key requires new_priority >= current priority "
                f"({new_priority} < {self.heap[idx].priority})"
            )

        self.heap[idx].priority = new_priority
        self._sift_up(idx)

    def decrease_key(self, task_id, new_priority):
        # Lower the priority of an existing task.
        # After lowering it, sift it down because it might now be smaller
        # than one of its children.
        # O(log n).
        if task_id not in self.index_map:
            raise KeyError(f"task_id '{task_id}' not found in queue")

        idx = self.index_map[task_id]

        if new_priority > self.heap[idx].priority:
            raise ValueError(
                f"decrease_key requires new_priority <= current priority "
                f"({new_priority} > {self.heap[idx].priority})"
            )

        self.heap[idx].priority = new_priority
        self._sift_down(idx)

    def __len__(self):
        return len(self.heap)


# --- Tests ---

if __name__ == "__main__":

    # --- basic insert and extract_max ---
    print("--- basic insert and extract_max ---\n")

    pq = MaxHeapPriorityQueue()
    pq.insert(Task("t1", priority=5))
    pq.insert(Task("t2", priority=2))
    pq.insert(Task("t3", priority=8))
    pq.insert(Task("t4", priority=1))
    pq.insert(Task("t5", priority=6))

    print("queue size:", len(pq))
    print("peek (should be t3, priority 8):", pq.peek())

    out1 = pq.extract_max()
    print("1st extract (should be t3, priority 8):", out1)
    print("  correct:", out1.task_id == "t3" and out1.priority == 8)

    out2 = pq.extract_max()
    print("2nd extract (should be t5, priority 6):", out2)
    print("  correct:", out2.task_id == "t5" and out2.priority == 6)

    out3 = pq.extract_max()
    print("3rd extract (should be t1, priority 5):", out3)
    print("  correct:", out3.task_id == "t1" and out3.priority == 5)

    print()

    # --- is_empty ---
    print("--- is_empty ---\n")

    pq2 = MaxHeapPriorityQueue()
    print("fresh queue is_empty:", pq2.is_empty())   # should be True

    pq2.insert(Task("a", priority=10))
    print("after one insert, is_empty:", pq2.is_empty())   # should be False

    pq2.extract_max()
    print("after extracting it, is_empty:", pq2.is_empty())   # should be True

    print()

    # --- extract from empty queue returns None, not an error ---
    print("--- extract from empty queue ---\n")

    pq3 = MaxHeapPriorityQueue()
    result = pq3.extract_max()
    print("extract_max on empty queue:", result)   # should be None
    print("  correct:", result is None)

    print()

    # --- increase_key ---
    print("--- increase_key ---\n")

    pq4 = MaxHeapPriorityQueue()
    pq4.insert(Task("x", priority=3))
    pq4.insert(Task("y", priority=7))
    pq4.insert(Task("z", priority=1))

    print("before increase_key: peek =", pq4.peek())   # y with priority 7

    # bump z from priority 1 up to 10 - it should become the new root
    pq4.increase_key("z", 10)
    print("after increase_key('z', 10): peek =", pq4.peek())   # z with priority 10
    print("  correct:", pq4.peek().task_id == "z" and pq4.peek().priority == 10)

    # extract them all in order
    e1 = pq4.extract_max()
    e2 = pq4.extract_max()
    e3 = pq4.extract_max()
    print("extraction order (should be z=10, y=7, x=3):", e1, e2, e3)
    print("  correct:", e1.priority == 10 and e2.priority == 7 and e3.priority == 3)

    print()

    # --- decrease_key ---
    print("--- decrease_key ---\n")

    pq5 = MaxHeapPriorityQueue()
    pq5.insert(Task("p", priority=9))
    pq5.insert(Task("q", priority=4))
    pq5.insert(Task("r", priority=6))

    print("before decrease_key: peek =", pq5.peek())   # p with priority 9

    # drop p from 9 down to 2 - it should sink below r(6) and q(4)
    pq5.decrease_key("p", 2)
    print("after decrease_key('p', 2): peek =", pq5.peek())   # r with priority 6
    print("  correct:", pq5.peek().task_id == "r")

    print("extraction order (should be r=6, q=4, p=2):")
    d1 = pq5.extract_max()
    d2 = pq5.extract_max()
    d3 = pq5.extract_max()
    print(" ", d1, d2, d3)
    print("  correct:", d1.priority == 6 and d2.priority == 4 and d3.priority == 2)

    print()

    # --- drain a queue and check the order is always descending ---
    print("--- drain queue, verify descending order ---\n")

    pq6 = MaxHeapPriorityQueue()
    random.seed(42)
    for i in range(10):
        pq6.insert(Task(f"task{i}", priority=random.randint(1, 100)))

    print("extracting all tasks:")
    prev = float("inf")
    order_ok = True
    while not pq6.is_empty():
        t = pq6.extract_max()
        print(f"  {t}")
        if t.priority > prev:
            order_ok = False
        prev = t.priority

    print("order was descending throughout:", order_ok)

    print()

    # --- stress test ---
    print("--- stress test (500 tasks, random priorities) ---\n")

    pq7 = MaxHeapPriorityQueue()
    for i in range(500):
        pq7.insert(Task(f"s{i}", priority=random.randint(0, 10000)))

    # do some random increase/decrease_key operations mid-flight
    # (pick a few tasks that are still in the queue and modify them)
    # we know s0..s499 are in there; just bump a few
    pq7.increase_key("s10",  9999)
    pq7.decrease_key("s20",  0)
    pq7.increase_key("s100", 9998)

    extracted = []
    while not pq7.is_empty():
        extracted.append(pq7.extract_max().priority)

    is_sorted_desc = all(extracted[i] >= extracted[i+1] for i in range(len(extracted) - 1))
    print("500 tasks extracted in descending priority order:", is_sorted_desc)
    print("s10 (set to 9999) came out first:", extracted[0] == 9999)
    print("s20 (set to 0) came out last:", extracted[-1] == 0)

    print()

    # --- Task with arrival_time and deadline fields ---
    print("--- Task metadata (arrival_time, deadline, description) ---\n")

    pq8 = MaxHeapPriorityQueue()
    pq8.insert(Task("job1", priority=3,  arrival_time=0, deadline=10, description="backup job"))
    pq8.insert(Task("job2", priority=10, arrival_time=1, deadline=5,  description="urgent report"))
    pq8.insert(Task("job3", priority=7,  arrival_time=2, deadline=8,  description="data sync"))

    print("processing jobs in priority order:")
    while not pq8.is_empty():
        t = pq8.extract_max()
        print(f"  serving {t.task_id} | priority={t.priority} | deadline={t.deadline} | '{t.description}'")
