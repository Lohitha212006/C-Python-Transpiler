<<<<<<< HEAD
"""
interfaces.py  —  Shared contract file (written on Day 1 by all 3 members).

Defines:
  - Parse tree format  (Member 1 produces, Member 2 consumes)
  - Annotated AST format (Member 2 produces, Member 3 consumes)
  - Shared error classes
  - Abstract base classes for each pipeline stage

Member 2 uses the MOCK examples at the bottom to develop and test
ast_builder.py and semantic_checker.py without waiting for Member 1.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

ParseTree    = Dict[str, Any]   # raw parse tree dict  (Member 1 output)
AnnotatedAST = Dict[str, Any]   # annotated AST dict   (Member 2 output)


# ---------------------------------------------------------------------------
# Token  (produced by Member 1's lexer)
# ---------------------------------------------------------------------------

class Token:
    __slots__ = ("type", "value", "line")

    def __init__(self, type_: str, value: str, line: int) -> None:
        self.type  = type_
        self.value = value
        self.line  = line

    def __repr__(self) -> str:
        return f"Token({self.type!r}, {self.value!r}, line={self.line})"


# ---------------------------------------------------------------------------
# Error hierarchy
# ---------------------------------------------------------------------------

class CompilerError(Exception):
    def __init__(self, message: str, line: Optional[int] = None) -> None:
        self.line = line
        loc = f" [line {line}]" if line is not None else ""
        super().__init__(f"{type(self).__name__}{loc}: {message}")

class LexerError(CompilerError):
    """Illegal character or unterminated token."""

class ParseError(CompilerError):
    """Token stream violates the grammar."""

class SemanticError(CompilerError):
    """Type error, undeclared variable, redeclaration, etc."""

class CodeGenError(CompilerError):
    """Unexpected node type during code generation."""


# ---------------------------------------------------------------------------
# Pipeline stage contracts (Abstract Base Classes)
# ---------------------------------------------------------------------------

class ILexer(ABC):
    @abstractmethod
    def tokenize(self, source: str) -> List[Token]: ...

class IParser(ABC):
    @abstractmethod
    def parse(self, tokens: List[Token]) -> ParseTree: ...

class IASTBuilder(ABC):
    @abstractmethod
    def build(self, parse_tree: ParseTree): ...

class ISemanticChecker(ABC):
    @abstractmethod
    def check(self, ast_root) -> AnnotatedAST: ...

class ICodeGenerator(ABC):
    @abstractmethod
    def generate(self, annotated_ast: AnnotatedAST) -> str: ...


# ---------------------------------------------------------------------------
# MOCK PARSE TREE  —  Member 2 uses this as test input (no Member 1 needed)
# ---------------------------------------------------------------------------
#
#  Represents:
#      int x = 5 + 3;
#
MOCK_PARSE_TREE_VAR_DECL: ParseTree = {
    "type": "VarDecl",
    "var_type": "int",
    "name": "x",
    "line": 1,
    "value": {
        "type": "BinaryOp",
        "op": "+",
        "line": 1,
        "left":  {"type": "Literal", "value": 5, "lit_type": "int",   "line": 1},
        "right": {"type": "Literal", "value": 3, "lit_type": "int",   "line": 1},
    },
}

#
#  Represents a full program:
#      int add(int a, int b) {
#          return a + b;
#      }
#
MOCK_PARSE_TREE_PROGRAM: ParseTree = {
    "type": "Program",
    "declarations": [
        {
            "type": "FuncDecl",
            "return_type": "int",
            "name": "add",
            "line": 1,
            "params": [
                {"type": "Param", "var_type": "int", "name": "a", "line": 1},
                {"type": "Param", "var_type": "int", "name": "b", "line": 1},
            ],
            "body": {
                "type": "Block",
                "line": 1,
                "statements": [
                    {
                        "type": "ReturnStmt",
                        "line": 2,
                        "value": {
                            "type": "BinaryOp",
                            "op": "+",
                            "line": 2,
                            "left":  {"type": "Identifier", "name": "a", "line": 2},
                            "right": {"type": "Identifier", "name": "b", "line": 2},
                        },
                    }
                ],
            },
        }
    ],
}


# ---------------------------------------------------------------------------
# MOCK ANNOTATED AST  —  Member 3 uses this as input (no Member 2 needed)
# ---------------------------------------------------------------------------
#
#  Same as MOCK_PARSE_TREE_VAR_DECL but every node has inferred_type added.
#
MOCK_ANNOTATED_AST: AnnotatedAST = {
    "type": "VarDecl",
    "var_type": "int",
    "name": "x",
    "inferred_type": "int",
    "line": 1,
    "value": {
        "type": "BinaryOp",
        "op": "+",
        "inferred_type": "int",
        "line": 1,
        "left":  {"type": "Literal", "value": 5, "lit_type": "int", "inferred_type": "int", "line": 1},
        "right": {"type": "Literal", "value": 3, "lit_type": "int", "inferred_type": "int", "line": 1},
    },
}

# interfaces.py — Shared contract between all 3 members
# Written on Day 1. Member 2 and Member 3 code against these examples.

# ─── TOKEN (Member 1 produces) ───────────────────────────────────────────────
# A token is a tuple: (token_type: str, value: str, line: int)
token_example = ("INT_LITERAL", "42", 3)

# ─── PARSE TREE (Member 1 produces →
