import json
import os


def solve(strs: list[str]) -> list[list[str]]:
    pass


def main() -> None:
    payload = json.loads(os.environ.get("TEST_INPUT", "{}"))
    result = solve(payload["strs"])
    print(json.dumps(result))


if __name__ == "__main__":
    main()
