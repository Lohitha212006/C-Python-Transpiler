"""
interfaces.py — Shared Contract (Day 1 agreement)
All members code against these data structure definitions.
Members 2 & 3 use the mock examples to start immediately without waiting.
"""

# ─────────────────────────────────────────────
# PARSE TREE FORMAT  (Member 1 produces → Member 2 consumes)
# ─────────────────────────────────────────────
# Example: int x = 5 + 3;
parse_tree_example = {
    "type": "VarDecl",
    "var_type": "int",
    "name": "x",
    "value": {
        "type": "BinaryOp",
        "op": "+",
        "left":  {"type": "Literal", "value": 5},
        "right": {"type": "Literal", "value": 3},
    },
}

# Example: while (x < 10) { x = x + 1; }
parse_tree_while_example = {
    "type": "WhileStmt",
    "condition": {
        "type": "BinaryOp", "op": "<",
        "left":  {"type": "Identifier", "name": "x"},
        "right": {"type": "Literal", "value": 10},
    },
    "body": {
        "type": "Block",
        "statements": [
            {
                "type": "Assign",
                "name": "x",
                "value": {
                    "type": "BinaryOp", "op": "+",
                    "left":  {"type": "Identifier", "name": "x"},
                    "right": {"type": "Literal", "value": 1},
                },
            }
        ],
    },
}

# Example: int add(int a, int b) { return a + b; }
parse_tree_func_example = {
    "type": "FunctionDecl",
    "return_type": "int",
    "name": "add",
    "params": [
        {"name": "a", "var_type": "int"},
        {"name": "b", "var_type": "int"},
    ],
    "body": {
        "type": "Block",
        "statements": [
            {
                "type": "ReturnStmt",
                "value": {
                    "type": "BinaryOp", "op": "+",
                    "left":  {"type": "Identifier", "name": "a"},
                    "right": {"type": "Identifier", "name": "b"},
                },
            }
        ],
    },
}

# ─────────────────────────────────────────────
# ANNOTATED AST FORMAT  (Member 2 produces → Member 3 consumes)
# Same nodes, but every node gains "inferred_type"
# ─────────────────────────────────────────────
ast_example = {
    "type": "VarDecl",
    "var_type": "int",
    "name": "x",
    "inferred_type": "int",          # ← added by Member 2
    "value": {
        "type": "BinaryOp", "op": "+",
        "inferred_type": "int",
        "left":  {"type": "Literal", "value": 5,  "inferred_type": "int"},
        "right": {"type": "Literal", "value": 3,  "inferred_type": "int"},
    },
}

ast_func_example = {
    "type": "FunctionDecl",
    "return_type": "int",
    "name": "add",
    "inferred_type": "int",
    "params": [
        {"name": "a", "var_type": "int", "inferred_type": "int"},
        {"name": "b", "var_type": "int", "inferred_type": "int"},
    ],
    "body": {
        "type": "Block",
        "inferred_type": "void",
        "statements": [
            {
                "type": "ReturnStmt",
                "inferred_type": "int",
                "value": {
                    "type": "BinaryOp", "op": "+",
                    "inferred_type": "int",
                    "left":  {"type": "Identifier", "name": "a", "inferred_type": "int"},
                    "right": {"type": "Identifier", "name": "b", "inferred_type": "int"},
                },
            }
        ],
    },
}
