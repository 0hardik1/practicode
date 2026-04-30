import json
import os


def solve(s: str) -> bool:
    pass


def main() -> None:
    payload = json.loads(os.environ.get("TEST_INPUT", "{}"))
    result = solve(payload["s"])
    print(json.dumps(result))


if __name__ == "__main__":
    main()
