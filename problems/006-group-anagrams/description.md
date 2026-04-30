# Group Anagrams

Given an array of strings `strs`, group the anagrams together.

## Input

`TEST_INPUT` is a JSON object:

```json
{
  "strs": ["eat", "tea", "tan", "ate", "nat", "bat"]
}
```

## Output

Print a JSON array of groups. To make the answer deterministic:

1. **Each inner group must be sorted lexicographically** (ascending).
2. **The outer list must be sorted by each group's first element** (ascending).

For the example above, the expected output is:

```json
[["ate", "eat", "tea"], ["bat"], ["nat", "tan"]]
```

## Example

Input: `strs = [""]` → Output: `[[""]]`

Input: `strs = ["a"]` → Output: `[["a"]]`

## Constraints

- `1 <= len(strs) <= 10^4`
- `0 <= len(strs[i]) <= 100`
- `strs[i]` consists of lowercase English letters.
