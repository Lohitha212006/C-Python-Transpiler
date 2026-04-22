"""
symbol_table.py  —  Member 2
==============================
Scope-aware symbol table for tracking variable and function declarations.

STRUCTURE
---------
The table is a STACK OF DICTIONARIES.
  • Each dictionary = one lexical scope.
  • Index 0  = global scope  (bottom of stack).
  • Last item = innermost (current) scope (top of stack).

  Stack when inside a function body that has one if block:
    [
      { "add": FuncInfo,  "x": VarInfo },   ← global scope
      { "a": ParamInfo,  "b": ParamInfo  },  ← function scope
      { "tmp": VarInfo },                    ← if-block scope
    ]

USAGE
-----
    st = SymbolTable()

    st.push_scope()                      # open global scope
    st.declare(SymbolInfo("x", "variable", "int", line=1))
    info = st.lookup("x")               # finds it
    st.pop_scope()                       # close scope

LOOKUP RULE
-----------
Searches from innermost scope outward. First match wins.
This implements lexical scoping: inner variables shadow outer ones.

REDECLARATION RULE
------------------
declare() only checks the CURRENT (innermost) scope.
Declaring the same name in an outer scope is allowed (shadowing).
Declaring the same name twice in the SAME scope → SemanticError.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from interfaces import SemanticError


# ---------------------------------------------------------------------------
# Symbol record
# ---------------------------------------------------------------------------

@dataclass
class SymbolInfo:
    """All information the compiler tracks for one declared name."""

    name:  str          # the identifier text
    kind:  str          # "variable" | "function" | "param"
    type_: str          # "int" | "float" | "void" | "bool"
    line:  int = 0      # source line where it was declared

    # Only populated for functions: the types of each parameter in order.
    # Used by the semantic checker to validate call-site argument types.
    param_types: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        base = f"{self.kind} '{self.name}': {self.type_} (line {self.line})"
        if self.param_types:
            base += f"  params={self.param_types}"
        return base


# ---------------------------------------------------------------------------
# Symbol table
# ---------------------------------------------------------------------------

class SymbolTable:
    """
    Lexically scoped symbol table implemented as a stack of dicts.

    Public methods
    --------------
    push_scope()     → open a new scope
    pop_scope()      → close innermost scope, return it
    declare(info)    → add symbol to current scope (error on redecl)
    lookup(name)     → find symbol in any enclosing scope (error if missing)
    lookup_optional  → same but returns None instead of raising
    is_declared_in_current_scope(name) → bool
    dump()           → string representation for debugging
    """

    def __init__(self) -> None:
        # Stack of scopes. Each scope is a dict: name → SymbolInfo.
        self._scopes: List[Dict[str, SymbolInfo]] = []

    # ------------------------------------------------------------------
    # Scope management
    # ------------------------------------------------------------------

    def push_scope(self) -> None:
        """Open a new lexical scope (call when entering a block or function)."""
        self._scopes.append({})

    def pop_scope(self) -> Dict[str, SymbolInfo]:
        """
        Close the innermost scope.
        Returns the closed scope dict (useful for debugging).
        Raises RuntimeError if the stack is already empty.
        """
        if not self._scopes:
            raise RuntimeError("pop_scope() called on an empty symbol table")
        return self._scopes.pop()

    @property
    def depth(self) -> int:
        """Number of currently open scopes (0 = no scope open yet)."""
        return len(self._scopes)

    # ------------------------------------------------------------------
    # Symbol operations
    # ------------------------------------------------------------------

    def declare(self, info: SymbolInfo) -> None:
        """
        Add *info* to the current (innermost) scope.

        Raises SemanticError if the name already exists IN THIS SCOPE.
        (Shadowing an outer scope is allowed.)
        """
        if not self._scopes:
            raise RuntimeError("declare() called with no open scope")

        current_scope = self._scopes[-1]

        if info.name in current_scope:
            existing = current_scope[info.name]
            raise SemanticError(
                f"Redeclaration of '{info.name}' in the same scope. "
                f"First declared at line {existing.line}.",
                line=info.line,
            )

        current_scope[info.name] = info

    def lookup(self, name: str, line: int = 0) -> SymbolInfo:
        """
        Search for *name* starting from the innermost scope outward.

        Raises SemanticError if *name* is not found in any scope.
        """
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        raise SemanticError(
            f"Undeclared identifier '{name}'",
            line=line,
        )

    def lookup_optional(self, name: str) -> Optional[SymbolInfo]:
        """
        Same as lookup() but returns None instead of raising when not found.
        Use this when you want to check existence without causing an error.
        """
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        return None

    def is_declared_in_current_scope(self, name: str) -> bool:
        """
        Return True if *name* exists in the innermost scope only.
        Ignores outer scopes (does NOT check shadowing).
        """
        if not self._scopes:
            return False
        return name in self._scopes[-1]

    # ------------------------------------------------------------------
    # Debug helpers
    # ------------------------------------------------------------------

    def dump(self) -> str:
        """Return a human-readable snapshot of the entire scope stack."""
        if not self._scopes:
            return "<SymbolTable: empty>"
        lines = []
        for i, scope in enumerate(self._scopes):
            label = "global" if i == 0 else f"scope-{i}"
            lines.append(f"[{label}]")
            if scope:
                for info in scope.values():
                    lines.append(f"  {info}")
            else:
                lines.append("  (empty)")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"SymbolTable(depth={self.depth})"
