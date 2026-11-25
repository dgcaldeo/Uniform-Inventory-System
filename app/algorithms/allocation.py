"""Shelf allocation for one section. Pure functions: no Flask, no database.

items = [{"id", "weight", "value", "min", "max"}]  (weight = shelf slots per piece)
Each returns {item_id: pieces}; total value = sum(value x pieces).
"""


def dp_allocate(items, capacity):
    """Bounded knapsack DP with minimum quantities. Raises ValueError if minimums don't fit."""
    base = sum(i["weight"] * i["min"] for i in items)
    if base > capacity:
        raise ValueError("Minimum quantities exceed the section capacity. Raise the capacity or lower the minimums.")
    rem = capacity - base
    n = len(items)
    dp = [[0] * (rem + 1) for _ in range(n + 1)]
    pick = [[0] * (rem + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        it = items[i - 1]
        for c in range(rem + 1):
            best, best_k = dp[i - 1][c], 0
            for k in range(1, it["max"] - it["min"] + 1):
                if k * it["weight"] > c:
                    break
                v = dp[i - 1][c - k * it["weight"]] + k * it["value"]
                if v > best:
                    best, best_k = v, k
            dp[i][c], pick[i][c] = best, best_k
    alloc, c = {}, rem
    for i in range(n, 0, -1):  # backtrack
        it = items[i - 1]
        k = pick[i][c]
        alloc[it["id"]] = it["min"] + k
        c -= k * it["weight"]
    return alloc


def greedy_allocate(items, capacity):
    """Baseline: minimums first, then highest value-per-slot first."""
    alloc = {i["id"]: i["min"] for i in items}
    rem = capacity - sum(i["weight"] * i["min"] for i in items)
    if rem < 0:
        raise ValueError("Minimum quantities exceed the section capacity.")
    for it in sorted(items, key=lambda x: x["value"] / x["weight"], reverse=True):
        k = min(it["max"] - it["min"], rem // it["weight"])
        alloc[it["id"]] += k
        rem -= k * it["weight"]
    return alloc


def equal_split_allocate(items, capacity):
    """Baseline: ignore sales, hand out pieces round-robin (a manual 'one of each' refill)."""
    alloc = {i["id"]: i["min"] for i in items}
    rem = capacity - sum(i["weight"] * i["min"] for i in items)
    if rem < 0:
        raise ValueError("Minimum quantities exceed the section capacity.")
    progress = True
    while progress and rem > 0:
        progress = False
        for it in items:
            if alloc[it["id"]] < it["max"] and it["weight"] <= rem:
                alloc[it["id"]] += 1
                rem -= it["weight"]
                progress = True
    return alloc


def total_value(items, alloc):
    return sum(i["value"] * alloc[i["id"]] for i in items)
