# interfaces.py — Shared contract between all 3 members
# Written on Day 1. Member 2 and Member 3 code against these examples.

# ─── TOKEN (Member 1 produces) ───────────────────────────────────────────────
# A token is a tuple: (token_type: str, value: str, line: int)
token_example = ("INT_LITERAL", "42", 3)

# ─── PARSE TREE (Member 1 produces →