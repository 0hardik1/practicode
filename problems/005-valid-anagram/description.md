# Valid Anagram

Given two strings `s` and `t`, return `true` if `t` is an anagram of `s`, and `false` otherwise.

An **anagram** is a word formed by rearranging the letters of another, using all original letters exactly once.

## Input

`TEST_INPUT` is a JSON object:

```json
{
  "s": "anagram",
  "t": "nagaram"
}
```

## Output

Print a single JSON boolean: `true` or `false`.

## Example

Input: `s = "anagram"`, `t = "nagaram"` → Output: `true`

Input: `s = "rat"`, `t = "car"` → Output: `false`

## Constraints

- `0 <= len(s), len(t) <= 5 * 10^4`
- `s` and `t` consist of lowercase English letters.
