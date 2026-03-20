import random


# Hash table using chaining for collision resolution.
# Uses a universal hash function: h(k) = ((a*k + b) % p) % m
# where p is a prime larger than the key space, and a, b are random.

PRIME = 10007  # prime larger than expected key range


class HashTable:
    def __init__(self, initial_size=8):
        self.size = initial_size
        self.count = 0
        self.buckets = [[] for _ in range(self.size)]

        # pick random a, b for universal hashing
        self.a = random.randint(1, PRIME - 1)
        self.b = random.randint(0, PRIME - 1)

    def _hash(self, key):
        # universal hash function
        return ((self.a * hash(key) + self.b) % PRIME) % self.size

    def _load_factor(self):
        return self.count / self.size

    def _resize(self):
        # double the table when load factor exceeds 0.75
        old_buckets = self.buckets
        self.size = self.size * 2
        self.buckets = [[] for _ in range(self.size)]
        self.count = 0

        # re-hash everything into new buckets
        self.a = random.randint(1, PRIME - 1)
        self.b = random.randint(0, PRIME - 1)
        for bucket in old_buckets:
            for key, val in bucket:
                self.insert(key, val)

    def insert(self, key, value):
        idx = self._hash(key)
        # check if key already exists, update if so
        for i, (k, v) in enumerate(self.buckets[idx]):
            if k == key:
                self.buckets[idx][i] = (key, value)
                return
        self.buckets[idx].append((key, value))
        self.count += 1

        if self._load_factor() > 0.75:
            self._resize()

    def search(self, key):
        idx = self._hash(key)
        for k, v in self.buckets[idx]:
            if k == key:
                return v
        return None  # not found

    def delete(self, key):
        idx = self._hash(key)
        for i, (k, v) in enumerate(self.buckets[idx]):
            if k == key:
                self.buckets[idx].pop(i)
                self.count -= 1
                return True
        return False  # key not found

    def __len__(self):
        return self.count


if __name__ == "__main__":
    ht = HashTable()

    # basic insert and search
    print("--- basic operations ---")
    ht.insert("alice", 42)
    ht.insert("bob", 17)
    ht.insert("carol", 99)
    print("search alice:", ht.search("alice"))
    print("search bob:", ht.search("bob"))
    print("search missing:", ht.search("dave"))

    # update existing key
    print("\n")
    print("--- update ---")
    ht.insert("alice", 100)
    print("alice after update = ", ht.search("alice"))

    # delete
    print("\n")
    print("--- delete ---")
    print("delete bob :", ht.delete("bob"))
    print("search bob after delete:", ht.search("bob"))
    print("delete missing=", ht.delete("bob"))

    # test resizing by inserting many keys
    print("\n")
    print("-- resize test ---")
    ht2 = HashTable(initial_size=4)
    for i in range(20):
        ht2.insert(f"key{i}", i * 10)
    print(f"inserted 20 items, table size={ht2.size}, count={ht2.count}, load={ht2._load_factor():.2f}")
    print("search key10:", ht2.search("key10"))
    print("search key19 :", ht2.search("key19"))

    # test with integer keys
    print("\n")
    print("--\- integer keys ---")
    ht3 = HashTable()
    for i in range(10):
        ht3.insert(i, i ** 2)
    for i in range(10):
        print(f"  {i} -> {ht3.search(i)}")
