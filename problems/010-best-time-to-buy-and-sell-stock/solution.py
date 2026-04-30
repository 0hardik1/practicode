import json
import os


def solve(prices: list[int]) -> int:
    if not prices:
        return 0
    min_price = prices[0]
    best = 0
    for price in prices[1:]:
        if price < min_price:
            min_price = price
        elif price - min_price > best:
            best = price - min_price
    return best


def main() -> None:
    payload = json.loads(os.environ.get("TEST_INPUT", "{}"))
    result = solve(payload["prices"])
    print(json.dumps(result))


if __name__ == "__main__":
    main()
