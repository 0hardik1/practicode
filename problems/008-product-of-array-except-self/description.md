# Product of Array Except Self

Given an integer array `nums`, return an array `answer` such that `answer[i]` is equal to the product of all the elements of `nums` except `nums[i]`.

You **must not** use the division operator. Aim for `O(n)` time.

## Input

`TEST_INPUT` is a JSON object:

```json
{
  "nums": [1, 2, 3, 4]
}
```

## Output

Print a JSON array of the same length as `nums`.

## Example

Input: `nums = [1, 2, 3, 4]` → Output: `[24, 12, 8, 6]`

Input: `nums = [-1, 1, 0, -3, 3]` → Output: `[0, 0, 9, 0, 0]`

## Constraints

- `2 <= len(nums) <= 10^5`
- `-30 <= nums[i] <= 30`
- The product of any prefix or suffix of `nums` fits in a 32-bit integer.
