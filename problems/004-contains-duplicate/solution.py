import json
import os


def solve(nums: list[int]) -> bool:
    return len(set(nums)) != len(nums)


def main() -> None:
    payload = json.loads(os.environ.get("TEST_INPUT", "{}"))
    result = solve(payload["nums"])
    print(json.dumps(result))


if __name__ == "__main__":
    main()
