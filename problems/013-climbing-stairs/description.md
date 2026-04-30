# Climbing Stairs

You are climbing a staircase. It takes `n` steps to reach the top.

Each time you can either climb `1` or `2` steps. In how many distinct ways can you climb to the top?

## Input

`TEST_INPUT` is a JSON object:

```json
{
  "n": 2
}
```

## Output

Print a single JSON integer — the number of distinct ways to reach step `n`.

## Example

Input: `n = 2` → Output: `2` (`1+1` or `2`)

Input: `n = 3` → Output: `3` (`1+1+1`, `1+2`, `2+1`)

## Constraints

- `1 <= n <= 45`
