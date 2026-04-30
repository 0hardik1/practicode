import json
import os


def solve(s: str, t: str) -> bool:
    pass


def main() -> None:
    payload = json.loads(os.environ.get("TEST_INPUT", "{}"))
    result = solve(payload["s"], payload["t"])
    print(json.dumps(result))


if __name__ == "__main__":
    main()
