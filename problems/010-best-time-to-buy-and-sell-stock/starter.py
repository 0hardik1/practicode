import json
import os


def solve(prices: list[int]) -> int:
    pass


def main() -> None:
    payload = json.loads(os.environ.get("TEST_INPUT", "{}"))
    result = solve(payload["prices"])
    print(json.dumps(result))


if __name__ == "__main__":
    main()
