####### Part 2 - Elementary Data Structures ###########
#
# Implements four fundamental data structures from scratch using
# Python lists as the underlying storage (no collections module,
# no numpy, etc.):
#
#   1. DynamicArray  - resizable array with O(1) amortized append,
#                      O(n) insertion/deletion at arbitrary index
#   2. Matrix        - 2D array backed by a list of lists
#   3. Stack         - LIFO, array-backed, all operations O(1)
#   4. Queue         - FIFO, array-backed with a front pointer so
#                      dequeue is O(1) amortized (no shifting)
#   5. SinglyLinkedList - O(1) front insert, O(n) back insert,
#                         O(n) search and delete
#   6. RootedTree    - n-ary tree using a parent/children linked
#                      structure (optional, included as bonus)
#
# Each class is followed by the relevant time complexity summary
# in the comments. Tests are at the bottom.



####### DynamicArray ######
#
# Wraps a Python list but exposes the conceptual operations
# explicitly and documents their costs.
#
# Time complexity:
#   get(i)          O(1)  - direct index
#   set(i, v)       O(1)  - direct index
#   append(v)       O(1) amortized - Python list doubles capacity
#                          when full (doubling strategy)
#   insert_at(i, v) O(n)  - must shift elements right of i
#   delete_at(i)    O(n)  - must shift elements left of i
#
# Space: O(n). The backing list may be up to 2x the used size
# due to the doubling strategy, but that is a constant factor.

class DynamicArray:

    def __init__(self):
        self._data = []

    def get(self, index):
        # O(1)
        if index < 0 or index >= len(self._data):
            raise IndexError(f"index {index} out of range")
        return self._data[index]

    def set(self, index, value):
        # O(1)
        if index < 0 or index >= len(self._data):
            raise IndexError(f"index {index} out of range")
        self._data[index] = value

    def append(self, value):
        # O(1) amortized
        self._data.append(value)

    def insert_at(self, index, value):
        # O(n) - shifts everything at and after index one position right
        if index < 0 or index > len(self._data):
            raise IndexError(f"index {index} out of range")
        self._data.insert(index, value)

    def delete_at(self, index):
        # O(n) - shifts everything after index one position left
        if index < 0 or index >= len(self._data):
            raise IndexError(f"index {index} out of range")
        return self._data.pop(index)

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return f"DynamicArray({self._data})"


######## Matrix ##########
#
# A rows x cols 2D array stored as a list of lists.
# Indices are (row, col), both 0-based.
#
# Time complexity:
#   get(r, c)       O(1)
#   set(r, c, v)    O(1)
#   add(other)      O(rows * cols)  - element-wise addition
#   multiply(other) O(rows * cols * inner_dim)  - standard matmul
#
# Space: O(rows * cols)

class Matrix:

    def __init__(self, rows, cols, default=0):
        self._rows = rows
        self._cols = cols
        self._data = [[default] * cols for _ in range(rows)]

    def get(self, row, col):
        return self._data[row][col]

    def set(self, row, col, value):
        self._data[row][col] = value

    def add(self, other):
        # Element-wise addition. Both matrices must have the same dimensions.
        if self._rows != other._rows or self._cols != other._cols:
            raise ValueError("matrix dimensions must match for addition")
        result = Matrix(self._rows, self._cols)
        for i in range(self._rows):
            for j in range(self._cols):
                result._data[i][j] = self._data[i][j] + other._data[i][j]
        return result

    def multiply(self, other):
        # Standard O(n^3) matrix multiplication.
        # self is (rows x cols), other must be (cols x other_cols).
        if self._cols != other._rows:
            raise ValueError(
                f"dimension mismatch: {self._rows}x{self._cols} * {other._rows}x{other._cols}"
            )
        result = Matrix(self._rows, other._cols)
        for i in range(self._rows):
            for j in range(other._cols):
                s = 0
                for k in range(self._cols):
                    s += self._data[i][k] * other._data[k][j]
                result._data[i][j] = s
        return result

    def __repr__(self):
        rows_str = "\n  ".join(str(row) for row in self._data)
        return f"Matrix(\n  {rows_str}\n)"



# Stack
#
# LIFO structure backed by a Python list.
# The top of the stack is the end of the list, so push and pop
# never touch any element except the last - both are O(1).
#
# Time complexity:
#   push(v)   O(1) amortized (same as list.append)
#   pop()     O(1)
#   peek()    O(1)
#   is_empty  O(1)
#
# Space: O(n)
#
# vs linked-list stack: both give O(1) push/pop. Array-backed is
# faster in practice due to cache locality and no allocation per
# element. Linked list avoids over-allocation but pays a pointer
# per node. For most use cases, array-backed is the better choice.

class Stack:

    def __init__(self):
        self._data = []

    def push(self, value):
        self._data.append(value)

    def pop(self):
        if self.is_empty():
            raise IndexError("pop from empty stack")
        return self._data.pop()

    def peek(self):
        # look at top without removing it
        if self.is_empty():
            return None
        return self._data[-1]

    def is_empty(self):
        return len(self._data) == 0

    def size(self):
        return len(self._data)

    def __repr__(self):
        return f"Stack(top -> {self._data[::-1]})"


# ================================================================
# Queue
#
# FIFO structure backed by a Python list with a front pointer.
#
# Naive approach: use list.pop(0) for dequeue - that's O(n)
# because every element shifts left. Unacceptable for large queues.
#
# This implementation keeps a _front pointer that advances on each
# dequeue instead of shifting elements. Dequeue becomes O(1).
# The backing list grows on enqueues and is only compacted when
# _front has passed more than half the list (so the wasted prefix
# is never larger than the used portion). Compaction is O(n) but
# happens at most every n/2 dequeues, making it O(1) amortized.
#
# Time complexity:
#   enqueue(v)  O(1) amortized
#   dequeue()   O(1) amortized
#   peek()      O(1)
#   is_empty    O(1)
#
# Space: O(n), with at most 2x overhead from the wasted prefix.
#
# vs linked-list queue: linked list gives O(1) guaranteed enqueue
# and dequeue with no compaction, but each element costs a node
# allocation and a pointer. For queues where throughput matters,
# a ring buffer (circular array) is usually the fastest choice
# in practice (Aho et al., 1983, ch. 2).
# ================================================================

class Queue:

    def __init__(self):
        self._data  = []
        self._front = 0

    def enqueue(self, value):
        self._data.append(value)

    def dequeue(self):
        if self.is_empty():
            raise IndexError("dequeue from empty queue")
        value = self._data[self._front]
        self._front += 1
        # compact once the wasted prefix exceeds half the backing list
        if self._front > len(self._data) // 2:
            self._data  = self._data[self._front:]
            self._front = 0
        return value

    def peek(self):
        if self.is_empty():
            return None
        return self._data[self._front]

    def is_empty(self):
        return self._front >= len(self._data)

    def size(self):
        return len(self._data) - self._front

    def __repr__(self):
        return f"Queue(front -> {self._data[self._front:]})"


# ================================================================
# SinglyLinkedList
#
# Chain of _Node objects where each node holds a value and a
# pointer to the next node. Head is tracked; no tail pointer
# (so insert_back requires traversal).
#
# Time complexity:
#   insert_front(v)   O(1)  - new node just points to old head
#   insert_back(v)    O(n)  - must walk to the last node
#   insert_at(i, v)   O(n)  - walk to position i
#   delete(value)     O(n)  - search then unlink
#   search(value)     O(n)  - linear scan
#   traverse()        O(n)
#
# Space: O(n), one node per element. Each node uses extra space
# for the .next pointer vs an array element. This is the main
# disadvantage versus arrays: higher memory overhead and poor
# cache locality since nodes may be scattered across the heap.
#
# The key advantage over arrays: O(1) front insertion and deletion
# (no shifting). This makes linked lists the right choice for
# stacks or queues with frequent front operations, and for cases
# where the total size is unknown and resizing would be costly.
# ================================================================

class _Node:
    __slots__ = ('value', 'next')
    def __init__(self, value):
        self.value = value
        self.next  = None


class SinglyLinkedList:

    def __init__(self):
        self._head = None
        self._size = 0

    def insert_front(self, value):
        # O(1)
        node      = _Node(value)
        node.next = self._head
        self._head = node
        self._size += 1

    def insert_back(self, value):
        # O(n) - walks to the tail
        node = _Node(value)
        if self._head is None:
            self._head = node
        else:
            current = self._head
            while current.next:
                current = current.next
            current.next = node
        self._size += 1

    def insert_at(self, index, value):
        # O(n) - walks to position index then inserts
        if index < 0 or index > self._size:
            raise IndexError(f"index {index} out of range")
        if index == 0:
            self.insert_front(value)
            return
        node    = _Node(value)
        current = self._head
        for _ in range(index - 1):
            current = current.next
        node.next    = current.next
        current.next = node
        self._size  += 1

    def delete(self, value):
        # Remove the first occurrence of value. Returns True if found.
        # O(n)
        if self._head is None:
            return False
        if self._head.value == value:
            self._head  = self._head.next
            self._size -= 1
            return True
        current = self._head
        while current.next:
            if current.next.value == value:
                current.next = current.next.next
                self._size  -= 1
                return True
            current = current.next
        return False

    def search(self, value):
        # Returns True if value is in the list. O(n)
        current = self._head
        while current:
            if current.value == value:
                return True
            current = current.next
        return False

    def to_list(self):
        # Returns the list as a Python list for easy inspection. O(n)
        result  = []
        current = self._head
        while current:
            result.append(current.value)
            current = current.next
        return result

    def size(self):
        return self._size

    def __repr__(self):
        return " -> ".join(str(x) for x in self.to_list()) + " -> None"


# ================================================================
# RootedTree (bonus)
#
# General n-ary tree. Each node has a value, a parent pointer,
# and a list of children. Implemented using a linked-list-like
# structure: the children list is a Python list of TreeNode
# references, not an array of values.
#
# This "left-child right-sibling" idea (Knuth, 1968) generalises
# to any branching factor and is the standard way to represent
# arbitrary rooted trees in memory.
#
# Time complexity:
#   add_child(parent, v)   O(1) - append to parent.children list
#   find(value)            O(n) - BFS/DFS over all nodes
#   preorder()             O(n) - visits every node once
#   level_order()          O(n) - BFS, visits every node once
#
# Space: O(n)
# ================================================================

class TreeNode:
    def __init__(self, value):
        self.value    = value
        self.children = []   # list of TreeNode
        self.parent   = None


class RootedTree:

    def __init__(self, root_value):
        self.root = TreeNode(root_value)

    def add_child(self, parent_node, value):
        child         = TreeNode(value)
        child.parent  = parent_node
        parent_node.children.append(child)
        return child

    def preorder(self, node=None):
        # Root first, then children left to right. O(n).
        if node is None:
            node = self.root
        result = [node.value]
        for child in node.children:
            result.extend(self.preorder(child))
        return result

    def level_order(self):
        # BFS. Returns list of (depth, value) pairs. O(n).
        result  = []
        queue   = [(self.root, 0)]
        while queue:
            node, depth = queue.pop(0)
            result.append((depth, node.value))
            for child in node.children:
                queue.append((child, depth + 1))
        return result

    def find(self, value):
        # DFS to locate a node by value. Returns the node or None. O(n).
        return self._find(self.root, value)

    def _find(self, node, value):
        if node.value == value:
            return node
        for child in node.children:
            result = self._find(child, value)
            if result:
                return result
        return None


# ================================================================
# Tests
# ================================================================

if __name__ == "__main__":

    # ----------------------------------------
    # Test 1: DynamicArray
    # ----------------------------------------
    print("=== Test 1: DynamicArray ===\n")

    da = DynamicArray()
    for v in [10, 20, 30, 40]:
        da.append(v)
    print(f"  after appending 10,20,30,40: {da}")
    print(f"  get(2) = {da.get(2)}  (expected 30)")

    da.insert_at(1, 15)
    print(f"  after insert_at(1, 15): {da}")    # [10,15,20,30,40]

    deleted = da.delete_at(3)
    print(f"  after delete_at(3): {da}  (deleted {deleted})")  # [10,15,20,40]

    da.set(0, 99)
    print(f"  after set(0, 99): {da}")

    try:
        da.get(100)
    except IndexError as e:
        print(f"  get(100) raises IndexError: correct")

    print()

    # ----------------------------------------
    # Test 2: Matrix
    # ----------------------------------------
    print("=== Test 2: Matrix ===\n")

    A = Matrix(2, 3)
    for i in range(2):
        for j in range(3):
            A.set(i, j, i * 3 + j + 1)   # [[1,2,3],[4,5,6]]

    B = Matrix(2, 3)
    for i in range(2):
        for j in range(3):
            B.set(i, j, 10)               # [[10,10,10],[10,10,10]]

    C = A.add(B)
    print(f"  A = {A}")
    print(f"  B = {B}")
    print(f"  A + B = {C}")
    print(f"  C[1][2] = {C.get(1, 2)}  (expected 16)")

    # 2x3 * 3x2 = 2x2
    D = Matrix(3, 2)
    vals = [1, 2, 3, 4, 5, 6]
    for idx, v in enumerate(vals):
        D.set(idx // 2, idx % 2, v)   # [[1,2],[3,4],[5,6]]
    E = A.multiply(D)   # 2x3 * 3x2 = 2x2
    print(f"  A * D = {E}")
    print(f"  E[0][0] = {E.get(0, 0)}  (expected 22: 1*1+2*3+3*5)")

    try:
        A.multiply(A)   # 2x3 * 2x3 -> dimension mismatch
    except ValueError as e:
        print(f"  mismatched multiply raises ValueError: correct")
    print()

    # ----------------------------------------
    # Test 3: Stack
    # ----------------------------------------
    print("=== Test 3: Stack ===\n")

    s = Stack()
    print(f"  is_empty: {s.is_empty()}  (expected True)")

    for v in [1, 2, 3, 4]:
        s.push(v)
    print(f"  after pushing 1,2,3,4: {s}")
    print(f"  peek: {s.peek()}  (expected 4)")
    print(f"  size: {s.size()}  (expected 4)")

    print(f"  pop: {s.pop()}  (expected 4)")
    print(f"  pop: {s.pop()}  (expected 3)")
    print(f"  after two pops: {s}")

    # drain and try to pop empty
    s.pop(); s.pop()
    try:
        s.pop()
    except IndexError:
        print(f"  pop on empty raises IndexError: correct")
    print()

    # ----------------------------------------
    # Test 4: Queue
    # ----------------------------------------
    print("=== Test 4: Queue ===\n")

    q = Queue()
    print(f"  is_empty: {q.is_empty()}  (expected True)")

    for v in [10, 20, 30, 40, 50]:
        q.enqueue(v)
    print(f"  after enqueueing 10..50: {q}")
    print(f"  peek: {q.peek()}  (expected 10)")
    print(f"  size: {q.size()}  (expected 5)")

    print(f"  dequeue: {q.dequeue()}  (expected 10)")
    print(f"  dequeue: {q.dequeue()}  (expected 20)")
    print(f"  after two dequeues: {q}")

    # check FIFO ordering completely
    out = []
    while not q.is_empty():
        out.append(q.dequeue())
    print(f"  remaining in FIFO order: {out}  (expected [30, 40, 50])")

    # test compaction: enqueue many then dequeue many
    q2 = Queue()
    for i in range(50):
        q2.enqueue(i)
    for i in range(48):
        q2.dequeue()
    print(f"  after 50 enqueues and 48 dequeues: size={q2.size()} peek={q2.peek()}"
          f"  (expected size=2, peek=48)")

    try:
        q2.dequeue(); q2.dequeue(); q2.dequeue()
    except IndexError:
        print(f"  dequeue on empty raises IndexError: correct")
    print()

    # ----------------------------------------
    # Test 5: SinglyLinkedList
    # ----------------------------------------
    print("=== Test 5: SinglyLinkedList ===\n")

    ll = SinglyLinkedList()
    print(f"  empty list: {ll}")

    ll.insert_front(3)
    ll.insert_front(2)
    ll.insert_front(1)
    print(f"  after insert_front 3,2,1: {ll}")    # 1 -> 2 -> 3 -> None

    ll.insert_back(4)
    ll.insert_back(5)
    print(f"  after insert_back 4,5: {ll}")        # 1 -> 2 -> 3 -> 4 -> 5 -> None

    ll.insert_at(2, 99)
    print(f"  after insert_at(2, 99): {ll}")       # 1->2->99->3->4->5

    print(f"  search(99): {ll.search(99)}  (expected True)")
    print(f"  search(77): {ll.search(77)}  (expected False)")

    deleted = ll.delete(99)
    print(f"  delete(99) returned {deleted}, list: {ll}")

    deleted2 = ll.delete(77)
    print(f"  delete(77) returned {deleted2}  (expected False)")

    # delete head
    ll.delete(1)
    print(f"  after delete(1): {ll}")

    print(f"  size: {ll.size()}  (expected 4)")
    print()

    # ----------------------------------------
    # Test 6: RootedTree
    # ----------------------------------------
    print("=== Test 6: RootedTree ===\n")

    #        A
    #       /|\
    #      B  C  D
    #     / \    |
    #    E   F   G

    t = RootedTree("A")
    b = t.add_child(t.root, "B")
    c = t.add_child(t.root, "C")
    d = t.add_child(t.root, "D")
    e = t.add_child(b, "E")
    f = t.add_child(b, "F")
    g = t.add_child(d, "G")

    print(f"  preorder:    {t.preorder()}")
    print(f"  expected:    ['A', 'B', 'E', 'F', 'C', 'D', 'G']")
    print(f"  correct: {t.preorder() == ['A', 'B', 'E', 'F', 'C', 'D', 'G']}")

    lo = t.level_order()
    print(f"  level_order: {lo}")
    print(f"  level 0: {[v for d,v in lo if d==0]}")
    print(f"  level 1: {[v for d,v in lo if d==1]}")
    print(f"  level 2: {[v for d,v in lo if d==2]}")

    found = t.find("F")
    print(f"  find('F'): found={found is not None}  parent={found.parent.value}  (expected parent B)")

    not_found = t.find("Z")
    print(f"  find('Z'): {not_found}  (expected None)")
    print()

    # ----------------------------------------
    # Performance summary (printed, not timed)
    # ----------------------------------------
    print("=== Complexity summary ===\n")
    rows = [
        ("DynamicArray", "get / set",      "O(1)",    "O(n)"),
        ("DynamicArray", "append",         "O(1)*",   "O(n)"),
        ("DynamicArray", "insert/delete",  "O(n)",    "O(n)"),
        ("Matrix",       "get / set",      "O(1)",    "O(rows*cols)"),
        ("Matrix",       "add",            "O(r*c)",  "O(rows*cols)"),
        ("Matrix",       "multiply",       "O(r*c*k)","O(rows*cols)"),
        ("Stack",        "push / pop",     "O(1)*",   "O(n)"),
        ("Queue",        "enqueue/dequeue","O(1)*",   "O(n)"),
        ("LinkedList",   "insert front",   "O(1)",    "O(n)"),
        ("LinkedList",   "insert back",    "O(n)",    "O(n)"),
        ("LinkedList",   "delete/search",  "O(n)",    "O(n)"),
        ("RootedTree",   "add_child",      "O(1)",    "O(n)"),
        ("RootedTree",   "find/traversal", "O(n)",    "O(n)"),
    ]
    print(f"  {'Structure':<16} {'Operation':<20} {'Time':>10}  {'Space':>10}")
    print(f"  {'-'*16} {'-'*20} {'-'*10}  {'-'*10}")
    for struct, op, time_c, space_c in rows:
        print(f"  {struct:<16} {op:<20} {time_c:>10}  {space_c:>10}")
    print("\n  * amortized")
