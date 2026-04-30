import json
import os


def solve(s: str) -> bool:
    cleaned = [ch.lower() for ch in s if ch.isalnum()]
    left, right = 0, len(cleaned) - 1
    while left < right:
        if cleaned[left] != cleaned[right]:
            return False
        left += 1
        right -= 1
    return True


def main() -> None:
    payload = json.loads(os.environ.get("TEST_INPUT", "{}"))
    result = solve(payload["s"])
    print(json.dumps(result))


if __name__ == "__main__":
    main()
