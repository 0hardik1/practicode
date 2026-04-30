# Longest Substring Without Repeating Characters

Given a string `s`, find the length of the **longest substring** without repeating characters.

## Input

`TEST_INPUT` is a JSON object:

```json
{
  "s": "abcabcbb"
}
```

## Output

Print a single JSON integer — the length of the longest substring with all distinct characters.

## Example

Input: `s = "abcabcbb"` → Output: `3` (the answer is `"abc"`)

Input: `s = "bbbbb"` → Output: `1` (the answer is `"b"`)

Input: `s = "pwwkew"` → Output: `3` (the answer is `"wke"`)

## Constraints

- `0 <= len(s) <= 5 * 10^4`
- `s` consists of English letters, digits, symbols, and spaces.
