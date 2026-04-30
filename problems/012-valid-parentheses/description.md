# Valid Parentheses

Given a string `s` containing only the characters `'('`, `')'`, `'{'`, `'}'`, `'['` and `']'`, determine if the input string is **valid**.

A string is valid if:

1. Open brackets are closed by the **same type** of bracket.
2. Open brackets are closed in the **correct order**.
3. Every close bracket has a corresponding open bracket of the same type.

## Input

`TEST_INPUT` is a JSON object:

```json
{
  "s": "()[]{}"
}
```

## Output

Print a single JSON boolean: `true` or `false`.

## Example

Input: `s = "()[]{}"` → Output: `true`

Input: `s = "(]"` → Output: `false`

Input: `s = "([)]"` → Output: `false`

## Constraints

- `0 <= len(s) <= 10^4`
- `s` consists of parentheses only: `()[]{}`.
