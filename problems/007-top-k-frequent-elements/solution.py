import json
import os
from collections import Counter
import heapq


def solve(nums: list[int], k: int) -> list[int]:
    counts = Counter(nums)
    top = heapq.nlargest(k, counts.items(), key=lambda item: item[1])
    return sorted(value for value, _ in top)


def main() -> None:
    payload = json.loads(os.environ.get("TEST_INPUT", "{}"))
    result = solve(payload["nums"], payload["k"])
    print(json.dumps(result))


if __name__ == "__main__":
    main()
