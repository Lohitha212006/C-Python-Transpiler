"""
symbol_table.py — Scope-Aware Symbol Table  (Member 2)
Supports push/pop scope for blocks and function bodies.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class Symbol:
    name: str
    sym_type: str          # "int" | "float" | "void" | function sig
    kind: str              # "variable" | "function" | "param"
    line: int = 0
    params: Optional[list] = None   # for functions


class SymbolError(Exception):
    pass


class SymbolTable:
    def __init__(self):
        self._scopes: list[Dict[str, Symbol]] = [{}]   # global scope

    # ── Scope management ──────────────────────────────────────────────────────
    def push_scope(self):
        self._scopes.append({})

    def pop_scope(self):
        if len(self._scopes) == 1:
            raise RuntimeError("Cannot pop global scope")
        self._scopes.pop()

    # ── Symbol operations ─────────────────────────────────────────────────────
    def declare(self, name: str, sym_type: str, kind: str, line: int = 0, params=None):
        """Declare a symbol in the *current* (innermost) scope."""
        current_scope = self._scopes[-1]
        if name in current_scope:
            raise SymbolError(
                f"Line {line}: '{name}' already declared in this scope "
                f"(first declared at line {current_scope[name].line})"
            )
        current_scope[name] = Symbol(name=name, sym_type=sym_type, kind=kind, line=line, params=params)

    def lookup(self, name: str) -> Optional[Symbol]:
        """Search from innermost scope outward. Returns None if not found."""
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        return None

    def require(self, name: str, line: int = 0) -> Symbol:
        """lookup() but raises SymbolError if not found."""
        sym = self.lookup(name)
        if sym is None:
            raise SymbolError(f"Line {line}: undeclared identifier '{name}'")
        return sym

    def __repr__(self):
        lines = []
        for depth, scope in enumerate(self._scopes):
            lines.append(f"  Scope {depth}: {list(scope.keys())}")
        return "SymbolTable(\n" + "\n".join(lines) + "\n)"
