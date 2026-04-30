# Best Time to Buy and Sell Stock

You are given an array `prices` where `prices[i]` is the price of a given stock on day `i`.

You want to maximize your profit by choosing a **single day** to buy one stock and choosing a **different day in the future** to sell that stock.

Return the maximum profit you can achieve from this transaction. If you cannot achieve any profit, return `0`.

## Input

`TEST_INPUT` is a JSON object:

```json
{
  "prices": [7, 1, 5, 3, 6, 4]
}
```

## Output

Print a single JSON integer.

## Example

Input: `prices = [7, 1, 5, 3, 6, 4]` → Output: `5` (buy on day 2 at price 1, sell on day 5 at price 6)

Input: `prices = [7, 6, 4, 3, 1]` → Output: `0` (no profitable transaction)

## Constraints

- `1 <= len(prices) <= 10^5`
- `0 <= prices[i] <= 10^4`
