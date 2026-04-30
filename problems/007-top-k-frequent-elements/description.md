# Top K Frequent Elements

Given an integer array `nums` and an integer `k`, return the `k` most frequent elements.

## Input

`TEST_INPUT` is a JSON object:

```json
{
  "nums": [1, 1, 1, 2, 2, 3],
  "k": 2
}
```

## Output

Print a JSON array of the `k` most frequent elements, **sorted in ascending order** so the answer is deterministic.

## Example

Input: `nums = [1, 1, 1, 2, 2, 3]`, `k = 2`
- Frequencies: `{1: 3, 2: 2, 3: 1}`
- Top 2: `1` and `2`
- Output (sorted ascending): `[1, 2]`

Input: `nums = [1]`, `k = 1` → Output: `[1]`

## Constraints

- `1 <= len(nums) <= 10^5`
- `1 <= k <= number of distinct elements in nums`
- `-10^4 <= nums[i] <= 10^4`
- The answer is guaranteed to be unique (when ties are broken arbitrarily); sorting the final list ensures a single valid output.
