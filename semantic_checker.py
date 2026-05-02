"""
semantic_checker.py — Semantic Analysis Pass  (Member 2)
Walks the AST, builds the symbol table, infers types, reports errors.
Annotates every node with inferred_type.
"""

from ast_nodes import (
    Program, FunctionDecl, Param, VarDecl, Block,
    IfStmt, WhileStmt, ReturnStmt, ExprStmt,
    Assign, BinaryOp, UnaryOp, Literal, Identifier, FunctionCall, ASTNode,
)
from symbol_table import SymbolTable, SymbolError
from typing import List, Optional


NUMERIC = {"int", "float"}
BOOL_OPS = {"==", "!=", "<", ">", "<=", ">=", "&&", "||"}
ARITH_OPS = {"+", "-", "*", "/"}


def _widen(a: str, b: str) -> str:
    """Return the wider of two numeric types."""
    if a == "float" or b == "float":
        return "float"
    return "int"


class SemanticError(Exception):
    pass


class SemanticChecker:
    def __init__(self):
        self.table = SymbolTable()
        self.errors: List[str] = []
        self._current_return_type: Optional[str] = None

    def _error(self, msg: str):
        self.errors.append(msg)

    # ── Top-level ─────────────────────────────────────────────────────────────
    def check(self, node: ASTNode) -> ASTNode:
        method = getattr(self, f"_check_{type(node).__name__}", self._check_default)
        return method(node)

    def _check_default(self, node: ASTNode) -> ASTNode:
        return node

    def _check_Program(self, node: Program) -> Program:
        # First pass: register all function names (allow forward calls)
        for decl in node.declarations:
            if isinstance(decl, FunctionDecl):
                try:
                    self.table.declare(
                        decl.name, decl.return_type, "function",
                        decl.line,
                        params=[p.var_type for p in decl.params],
                    )
                except SymbolError as e:
                    self._error(str(e))
        for decl in node.declarations:
            self.check(decl)
        node.inferred_type = "void"
        return node

    def _check_FunctionDecl(self, node: FunctionDecl) -> FunctionDecl:
        self._current_return_type = node.return_type
        self.table.push_scope()
        for p in node.params:
            try:
                self.table.declare(p.name, p.var_type, "param", p.line)
            except SymbolError as e:
                self._error(str(e))
            p.inferred_type = p.var_type
        if node.body:
            self.check(node.body)
        self.table.pop_scope()
        self._current_return_type = None
        node.inferred_type = node.return_type
        return node

    def _check_VarDecl(self, node: VarDecl) -> VarDecl:
        if node.value:
            self.check(node.value)
            val_type = node.value.inferred_type
            if val_type and val_type not in (node.var_type, "unknown"):
                # allow int literal assigned to float
                if not (node.var_type == "float" and val_type == "int"):
                    self._error(
                        f"Line {node.line}: type mismatch — "
                        f"cannot assign {val_type!r} to {node.var_type!r} variable '{node.name}'"
                    )
        try:
            self.table.declare(node.name, node.var_type, "variable", node.line)
        except SymbolError as e:
            self._error(str(e))
        node.inferred_type = node.var_type
        return node

    def _check_Block(self, node: Block) -> Block:
        self.table.push_scope()
        for stmt in node.statements:
            self.check(stmt)
        self.table.pop_scope()
        node.inferred_type = "void"
        return node

    def _check_IfStmt(self, node: IfStmt) -> IfStmt:
        if node.condition:
            self.check(node.condition)
        if node.then:
            self.check(node.then)
        if node.else_:
            self.check(node.else_)
        node.inferred_type = "void"
        return node

    def _check_WhileStmt(self, node: WhileStmt) -> WhileStmt:
        if node.condition:
            self.check(node.condition)
        if node.body:
            self.check(node.body)
        node.inferred_type = "void"
        return node

    def _check_ReturnStmt(self, node: ReturnStmt) -> ReturnStmt:
        if node.value:
            self.check(node.value)
            ret_type = node.value.inferred_type
        else:
            ret_type = "void"
        expected = self._current_return_type
        if expected and expected != "void" and ret_type != expected:
            # allow int→float widening
            if not (expected == "float" and ret_type == "int"):
                self._error(
                    f"Line {node.line}: return type mismatch — "
                    f"expected {expected!r}, got {ret_type!r}"
                )
        node.inferred_type = ret_type
        return node

    def _check_ExprStmt(self, node: ExprStmt) -> ExprStmt:
        if node.expr:
            self.check(node.expr)
            node.inferred_type = node.expr.inferred_type
        return node

    def _check_Assign(self, node: Assign) -> Assign:
        try:
            sym = self.table.require(node.name, node.line)
        except SymbolError as e:
            self._error(str(e))
            sym = None
        if node.value:
            self.check(node.value)
        if sym and node.value:
            vt = node.value.inferred_type
            if vt and vt != sym.sym_type:
                if not (sym.sym_type == "float" and vt == "int"):
                    self._error(
                        f"Line {node.line}: type mismatch in assignment to '{node.name}' "
                        f"— expected {sym.sym_type!r}, got {vt!r}"
                    )
        node.inferred_type = sym.sym_type if sym else "unknown"
        return node

    def _check_BinaryOp(self, node: BinaryOp) -> BinaryOp:
        if node.left:
            self.check(node.left)
        if node.right:
            self.check(node.right)
        lt = node.left.inferred_type if node.left else "unknown"
        rt = node.right.inferred_type if node.right else "unknown"
        if node.op in BOOL_OPS:
            node.inferred_type = "bool"
        elif node.op in ARITH_OPS:
            node.inferred_type = _widen(lt or "int", rt or "int")
        else:
            node.inferred_type = "unknown"
        return node

    def _check_UnaryOp(self, node: UnaryOp) -> UnaryOp:
        if node.operand:
            self.check(node.operand)
            node.inferred_type = node.operand.inferred_type
        return node

    def _check_Literal(self, node: Literal) -> Literal:
        if node.inferred_type is None:
            if isinstance(node.value, bool):
                node.inferred_type = "bool"
            elif isinstance(node.value, int):
                node.inferred_type = "int"
            elif isinstance(node.value, float):
                node.inferred_type = "float"
            elif isinstance(node.value, str):
                node.inferred_type = "string"
            else:
                node.inferred_type = "unknown"
        return node

    def _check_Identifier(self, node: Identifier) -> Identifier:
        try:
            sym = self.table.require(node.name, node.line)
            node.inferred_type = sym.sym_type
        except SymbolError as e:
            self._error(str(e))
            node.inferred_type = "unknown"
        return node

    def _check_FunctionCall(self, node: FunctionCall) -> FunctionCall:
        sym = self.table.lookup(node.name)
        if sym is None:
            self._error(f"Line {node.line}: call to undeclared function '{node.name}'")
            node.inferred_type = "unknown"
        else:
            expected_params = sym.params or []
            if len(node.args) != len(expected_params):
                self._error(
                    f"Line {node.line}: function '{node.name}' expects "
                    f"{len(expected_params)} arguments, got {len(node.args)}"
                )
            for arg in node.args:
                self.check(arg)
            node.inferred_type = sym.sym_type
        return node


def analyze(ast_root: ASTNode):
    """Run semantic analysis. Returns (annotated_root, errors_list)."""
    checker = SemanticChecker()
    checker.check(ast_root)
    return ast_root, checker.errors
