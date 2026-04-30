# Valid Palindrome

A phrase is a **palindrome** if, after converting all uppercase letters into lowercase letters and removing all non-alphanumeric characters, it reads the same forward and backward.

Given a string `s`, return `true` if it is a palindrome, or `false` otherwise.

## Input

`TEST_INPUT` is a JSON object:

```json
{
  "s": "A man, a plan, a canal: Panama"
}
```

## Output

Print a single JSON boolean: `true` or `false`.

## Example

Input: `s = "A man, a plan, a canal: Panama"` → Output: `true` (after cleaning: `"amanaplanacanalpanama"`)

Input: `s = "race a car"` → Output: `false` (cleaned: `"raceacar"`)

## Constraints

- `1 <= len(s) <= 2 * 10^5`
- `s` consists of printable ASCII characters.
