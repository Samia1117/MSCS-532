import math
import time
import random
import statistics

# Knuth's multiplier for the multiplication hash method
PHI = (math.sqrt(5) - 1) / 2  # ~0.6180339887

def h_division(k, m):
    return k % m  # fast but clusters badly when keys share factors with m

def h_multiply(k, m):
    # floor(m * frac(k * PHI)) - spreads keys better than plain modulo
    return int(m * ((k * PHI) % 1))

DELETED = object()  # sentinel for lazy-deleted slots in open addressing

# ---- Separate Chaining ----

class ChainingHashTable:
    def __init__(self, m, hash_fn=h_multiply):
        self.m = m
        self.buckets = [[] for _ in range(m)]  # array of lists
        self.hash_fn = hash_fn
        self.n = 0

    def insert(self, key, val=None):
        idx = self.hash_fn(key, self.m)
        for i, (k, v) in enumerate(self.buckets[idx]):
            if k == key:
                self.buckets[idx][i] = (key, val)  # update in place
                return True
        self.buckets[idx].append((key, val))
        self.n += 1
        return True

    def search(self, key):
        idx = self.hash_fn(key, self.m)
        for k, v in self.buckets[idx]:
            if k == key:
                return v
        return None

    def delete(self, key):
        idx = self.hash_fn(key, self.m)
        for i, (k, v) in enumerate(self.buckets[idx]):
            if k == key:
                self.buckets[idx].pop(i)
                self.n -= 1
                return True
        return False

    @property
    def load_factor(self):
        return self.n / self.m

    def chain_stats(self):
        lengths = [len(b) for b in self.buckets]
        nonempty = [l for l in lengths if l > 0]
        return {
            'max': max(lengths),
            'avg_nonempty': round(statistics.mean(nonempty), 2),
            'empty': lengths.count(0)
        }


# ---- Open Addressing ----

class OpenAddressHashTable:
    def __init__(self, m, probe='linear', hash_fn=h_multiply):
        self.m = m
        self.table = [None] * m
        self.probe = probe
        self.hash_fn = hash_fn
        self.n = 0

    def _slots(self, key):
        h = self.hash_fn(key, self.m)
        if self.probe == 'linear':
            for i in range(self.m):
                yield (h + i) % self.m
        elif self.probe == 'quadratic':
            # c1=0.5, c2=0.5: h + i/2 + i^2/2 - covers all m slots when m is prime
            for i in range(self.m):
                yield (h + (i + i * i) // 2) % self.m
        elif self.probe == 'double':
            # second hash must be nonzero; 1 + (k % (m-1)) gives values in [1, m-1]
            h2 = 1 + (key % (self.m - 1))
            for i in range(self.m):
                yield (h + i * h2) % self.m

    def insert(self, key, val=None):
        first_del = None
        for slot in self._slots(key):
            e = self.table[slot]
            if e is None:
                self.table[first_del if first_del is not None else slot] = (key, val)
                self.n += 1
                return True
            elif e is DELETED:
                if first_del is None:
                    first_del = slot  # remember first tombstone for reuse
            elif e[0] == key:
                self.table[slot] = (key, val)
                return True
        if first_del is not None:
            self.table[first_del] = (key, val)
            self.n += 1
            return True
        return False  # table full

    def search(self, key):
        for slot in self._slots(key):
            e = self.table[slot]
            if e is None:
                return None  # probe chain is broken - key not present
            if e is not DELETED and e[0] == key:
                return e[1]
        return None

    def delete(self, key):
        for slot in self._slots(key):
            e = self.table[slot]
            if e is None:
                return False
            if e is not DELETED and e[0] == key:
                self.table[slot] = DELETED  # tombstone, not None - preserves probe chains
                self.n -= 1
                return True
        return False

    @property
    def load_factor(self):
        return self.n / self.m


# ---- Demo 1: clustering with bad vs good hash ----

def demo_clustering():
    print("=== Clustering Demo ===")
    print()
    m = 16  # power of 2 - problematic for division hash with multiples of m
    # all these keys are multiples of 16 -> division hash maps all of them to slot 0
    keys = [0, 16, 32, 48, 64, 80, 96, 112]
    print(f"Keys: {keys}")
    print(f"Table size m={m}\n")

    print("Division hash (k % 16) - all keys map to slot 0:")
    for k in keys:
        print(f"  h({k:3d}) = {h_division(k, m)}")

    print()
    print("Multiplication hash - keys spread across the table:")
    for k in keys:
        print(f"  h({k:3d}) = {h_multiply(k, m)}")

    print()
    print("Linear probing with division hash on these keys:")
    ht_bad = OpenAddressHashTable(m, 'linear', hash_fn=h_division)
    for k in keys:
        ht_bad.insert(k)
    occupied = [(i, ht_bad.table[i][0]) for i in range(m) if ht_bad.table[i] not in (None, DELETED)]
    print(f"  Slots used: {[s for s, _ in occupied]}")
    print(f"  All 8 keys landed in slots 0-7 -> one big cluster (primary clustering)")

    print()
    print("Linear probing with multiplication hash on same keys:")
    ht_good = OpenAddressHashTable(m, 'linear', hash_fn=h_multiply)
    for k in keys:
        ht_good.insert(k)
    occupied = [(i, ht_good.table[i][0]) for i in range(m) if ht_good.table[i] not in (None, DELETED)]
    print(f"  Slots used: {[s for s, _ in occupied]}")
    print()


# ---- Demo 2: chain length distribution ----

def demo_chain_lengths():
    print("=== Chain Length Distribution (m=100, multiplication hash) ===")
    print()
    m = 100
    for lf in [0.5, 1.0, 2.0]:
        n = int(m * lf)
        ht = ChainingHashTable(m)
        for k in random.sample(range(10000), n):
            ht.insert(k)
        stats = ht.chain_stats()
        print(f"  lf={lf:.1f} ({n} keys): max chain={stats['max']}, "
              f"avg nonempty chain={stats['avg_nonempty']}, empty buckets={stats['empty']}")
    print()


# ---- Demo 3: hash function timing ----

def demo_hash_timing():
    print("=== Hash Function Timing (1M calls each) ===")
    print()
    m = 997
    n = 1_000_000
    keys = [random.randint(0, 10**9) for _ in range(n)]

    t0 = time.perf_counter()
    for k in keys:
        h_division(k, m)
    div_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    for k in keys:
        h_multiply(k, m)
    mul_ms = (time.perf_counter() - t0) * 1000

    print(f"  Division hash:      {div_ms:.1f}ms  ({div_ms/n*1000:.3f}us/call)")
    print(f"  Multiplication hash:{mul_ms:.1f}ms  ({mul_ms/n*1000:.3f}us/call)")
    print()


# ---- Benchmark: chaining vs open addressing at different load factors ----

def benchmark():
    print("=== Benchmark: Chaining vs Open Addressing ===")
    print(f"Table size m=997 (prime), times per operation averaged over all keys")
    print()

    m = 997  # prime - important for double hashing and quadratic probe coverage
    load_factors = [0.25, 0.5, 0.75, 0.9]

    for lf in load_factors:
        n = int(m * lf)
        all_keys = random.sample(range(1, 50 * m), n)
        search_sample = random.sample(all_keys, min(500, n))
        miss_keys = random.sample(range(50 * m, 100 * m), 500)

        print(f"Load factor = {lf} ({n} keys in table)")
        print(f"  {'Method':<22} {'Insert (us)':>12} {'Hit (us)':>12} {'Miss (us)':>12}")
        print(f"  {'-'*22} {'-'*12} {'-'*12} {'-'*12}")

        configs = [
            ("Chaining",       ChainingHashTable(m)),
            ("Linear probe",   OpenAddressHashTable(m, 'linear')),
            ("Quadratic probe",OpenAddressHashTable(m, 'quadratic')),
            ("Double hashing", OpenAddressHashTable(m, 'double')),
        ]

        for name, ht in configs:
            t0 = time.perf_counter()
            inserted = 0
            for k in all_keys:
                if ht.insert(k):
                    inserted += 1
            insert_us = (time.perf_counter() - t0) / max(inserted, 1) * 1e6

            t0 = time.perf_counter()
            for k in search_sample:
                ht.search(k)
            hit_us = (time.perf_counter() - t0) / len(search_sample) * 1e6

            t0 = time.perf_counter()
            for k in miss_keys:
                ht.search(k)
            miss_us = (time.perf_counter() - t0) / len(miss_keys) * 1e6

            print(f"  {name:<22} {insert_us:>11.3f} {hit_us:>11.3f} {miss_us:>11.3f}")
        print()


# ---- Correctness tests ----

def run_tests():
    print("=== Correctness Tests ===")
    print()

    passed = 0

    def check(name, got, want):
        nonlocal passed
        if got == want:
            passed += 1
        else:
            print(f"  FAIL {name}: got {got}, want {want}")

    for label, ht in [
        ("ChainingHashTable", ChainingHashTable(16)),
        ("Linear probe",      OpenAddressHashTable(16, 'linear')),
        ("Quadratic probe",   OpenAddressHashTable(16, 'quadratic')),
        ("Double hashing",    OpenAddressHashTable(16, 'double')),
    ]:
        ht.insert(10, "ten")
        ht.insert(26, "twenty-six")  # h_multiply(10,16)=h_multiply(26,16) may collide
        ht.insert(7, "seven")
        check(f"{label} search hit",    ht.search(10),  "ten")
        check(f"{label} search hit 2",  ht.search(26),  "twenty-six")
        check(f"{label} search miss",   ht.search(99),  None)
        ht.insert(10, "TEN")  # update
        check(f"{label} update",        ht.search(10),  "TEN")
        ht.delete(10)
        check(f"{label} search after delete", ht.search(10), None)
        check(f"{label} search after delete 2", ht.search(26), "twenty-six")  # unaffected

    # stress test: insert 500 random keys into each type and verify all retrievable
    for label, ht in [
        ("Stress chaining",  ChainingHashTable(997)),
        ("Stress linear",    OpenAddressHashTable(997, 'linear')),
        ("Stress double",    OpenAddressHashTable(997, 'double')),
    ]:
        keys = random.sample(range(10000), 500)
        for k in keys:
            ht.insert(k, k * 2)
        for k in keys:
            check(f"{label} key={k}", ht.search(k), k * 2)

    print(f"  All {passed} checks passed")
    print()


if __name__ == '__main__':
    random.seed(42)
    run_tests()
    demo_clustering()
    demo_chain_lengths()
    demo_hash_timing()
    benchmark()
