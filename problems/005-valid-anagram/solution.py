import json
import os
from collections import Counter


def solve(s: str, t: str) -> bool:
    return Counter(s) == Counter(t)


def main() -> None:
    payload = json.loads(os.environ.get("TEST_INPUT", "{}"))
    result = solve(payload["s"], payload["t"])
    print(json.dumps(result))


if __name__ == "__main__":
    main()
