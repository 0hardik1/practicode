import json
import os
from collections import defaultdict


def solve(strs: list[str]) -> list[list[str]]:
    buckets: dict[str, list[str]] = defaultdict(list)
    for word in strs:
        key = "".join(sorted(word))
        buckets[key].append(word)
    groups = [sorted(group) for group in buckets.values()]
    groups.sort(key=lambda group: group[0])
    return groups


def main() -> None:
    payload = json.loads(os.environ.get("TEST_INPUT", "{}"))
    result = solve(payload["strs"])
    print(json.dumps(result))


if __name__ == "__main__":
    main()
