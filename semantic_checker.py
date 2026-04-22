"""
semantic_checker.py  —  Member 2
==================================
Walks the AST, performs all semantic checks, and annotates every node
with its inferred_type.  The annotated dict output is what Member 3's
CodeGenerator consumes.

CHECKS PERFORMED
----------------
1. Undeclared variable usage          → SemanticError
2. Redeclaration in same scope        → SemanticError
3. Type mismatch in assignment        → SemanticError  (float→int narrowing)
4. Type mismatch in return statement  → SemanticError
5. Missing return in non-void func    → SemanticError  (basic check)
6. Function call: wrong arg count     → SemanticError
7. Function call: wrong arg types     → SemanticError
8. Calling a variable as a function   → SemanticError
9. if/while condition type check      → SemanticError if not numeric/bool
10. Arithmetic on non-numeric types   → SemanticError

TYPE SYSTEM
-----------
  "int"   — integer
  "float" — floating point  (int is widened to float automatically)
  "bool"  — result of comparisons and logical ops
  "void"  — functions that return nothing

Widening rule:  int  →  float  is allowed  (int used where float expected)
Narrowing rule: float → int   is NOT allowed (SemanticError)
bool ↔ int is allowed (C semantics: bool is numeric)

HOW MEMBER 2 USES IT STANDALONE
---------------------------------
    from interfaces import MOCK_PARSE_TREE_PROGRAM
    from ast_builder import ASTBuilder
    from semantic_checker import SemanticChecker

    ast_root = ASTBuilder().build(MOCK_PARSE_TREE_PROGRAM)
    annotated_dict = SemanticChecker().check(ast_root)
    # annotated_dict is what Member 3 passes to CodeGenerator
"""

from __future__ import annotations
from typing import Optional

from interfaces import ISemanticChecker, SemanticError, AnnotatedAST
import ast_nodes as N
from symbol_table import SymbolInfo, SymbolTable


# ---------------------------------------------------------------------------
# Type helpers
# ---------------------------------------------------------------------------

# Operators that produce a bool result
_COMPARISON_OPS = {"==", "!=", "<", ">", "<=", ">="}
_LOGICAL_OPS    = {"&&", "||"}
_ARITHMETIC_OPS = {"+", "-", "*", "/", "%"}


def _is_numeric(t: str) -> bool:
    """True for types that can appear in arithmetic expressions."""
    return t in ("int", "float")


def _is_bool_like(t: str) -> bool:
    """True for types valid as an if/while condition (C treats int as bool)."""
    return t in ("int", "float", "bool")


def _numeric_result(t1: str, t2: str) -> str:
    """Return the type of  t1 op t2  for arithmetic (int+float → float)."""
    if t1 == "float" or t2 == "float":
        return "float"
    return "int"


def _types_compatible(target: str, source: str) -> bool:
    """
    Return True if a value of type *source* can be stored in *target*.

    Rules:
      • same type        → always compatible
      • int  → float     → allowed (widening / promotion)
      • bool → int       → allowed (C semantics)
      • anything else    → NOT compatible
    """
    if target == source:
        return True
    if target == "float" and source == "int":   # widening
        return True
    if target == "int"   and source == "bool":  # C: bool is int
        return True
    return False


# ---------------------------------------------------------------------------
# Semantic checker
# ---------------------------------------------------------------------------

class SemanticChecker(ISemanticChecker):
    """
    Traverses the AST, enforces semantic rules, annotates every node
    with inferred_type, and returns the annotated dict representation.

    Usage:
        checker        = SemanticChecker()
        annotated_dict = checker.check(ast_root)
    """

    def __init__(self) -> None:
        self._table = SymbolTable()

        # Track which function we are currently inside (for return checks)
        self._current_function:    Optional[str] = None
        self._current_return_type: Optional[str] = None
        # Whether we saw a return statement in the current function
        self._has_return: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check(self, root: N.Program) -> AnnotatedAST:
        """
        Type-check and annotate *root*.
        Returns the annotated dict (JSON-serialisable) for Member 3.
        Raises SemanticError on any violation.
        """
        self._table.push_scope()   # open global scope
        self._visit(root)
        self._table.pop_scope()
        return root.to_dict()

    # ------------------------------------------------------------------
    # Dispatcher
    # ------------------------------------------------------------------

    def _visit(self, node: N.ASTNode) -> str:
        """
        Visit *node*, run semantic checks, set node.inferred_type,
        and return the inferred type string.
        """
        handler = getattr(self, f"_check_{type(node).__name__}", None)
        if handler is None:
            raise SemanticError(
                f"SemanticChecker: no handler for node type "
                f"'{type(node).__name__}'",
                line=getattr(node, "line", None),
            )
        return handler(node)

    # ------------------------------------------------------------------
    # Program & top-level declarations
    # ------------------------------------------------------------------

    def _check_Program(self, node: N.Program) -> str:
        for decl in node.declarations:
            self._visit(decl)
        node.inferred_type = "void"
        return "void"

    # ------------------------------------------------------------------
    # Function declaration
    # ------------------------------------------------------------------

    def _check_FuncDecl(self, node: N.FuncDecl) -> str:
        # 1. Register function in the global scope BEFORE entering body
        #    (allows recursion — the function can call itself)
        param_types = [p.var_type for p in node.params]
        self._table.declare(SymbolInfo(
            name        = node.name,
            kind        = "function",
            type_       = node.return_type,
            param_types = param_types,
            line        = node.line,
        ))

        # 2. Open a new scope for params + body
        self._table.push_scope()

        # 3. Save and update function context
        prev_func        = self._current_function
        prev_return_type = self._current_return_type
        prev_has_return  = self._has_return

        self._current_function    = node.name
        self._current_return_type = node.return_type
        self._has_return          = False

        # 4. Declare parameters (they live in the function scope)
        for param in node.params:
            self._visit(param)

        # 5. Check body statements directly in the function scope
        #    (so param names and top-level local names share one scope,
        #     making param redeclaration in the body a SemanticError)
        for stmt in node.body.statements:
            self._visit(stmt)
        node.body.inferred_type = "void"

        # 6. Check that non-void functions have a return statement
        if node.return_type != "void" and not self._has_return:
            raise SemanticError(
                f"Function '{node.name}' has return type "
                f"'{node.return_type}' but no return statement was found.",
                line=node.line,
            )

        # 7. Restore context
        self._current_function    = prev_func
        self._current_return_type = prev_return_type
        self._has_return          = prev_has_return

        self._table.pop_scope()

        node.inferred_type = node.return_type
        return node.return_type

    def _check_Param(self, node: N.Param) -> str:
        self._table.declare(SymbolInfo(
            name  = node.name,
            kind  = "param",
            type_ = node.var_type,
            line  = node.line,
        ))
        node.inferred_type = node.var_type
        return node.var_type

    # ------------------------------------------------------------------
    # Variable declaration
    # ------------------------------------------------------------------

    def _check_VarDecl(self, node: N.VarDecl) -> str:
        # Check initialiser FIRST (prevents  int x = x;)
        if node.value is not None:
            init_type = self._visit(node.value)
            if not _types_compatible(node.var_type, init_type):
                raise SemanticError(
                    f"Cannot initialise '{node.var_type}' variable "
                    f"'{node.name}' with a '{init_type}' value. "
                    f"(Hint: float cannot be narrowed to int.)",
                    line=node.line,
                )

        # Declare AFTER checking initialiser
        self._table.declare(SymbolInfo(
            name  = node.name,
            kind  = "variable",
            type_ = node.var_type,
            line  = node.line,
        ))
        node.inferred_type = node.var_type
        return node.var_type

    # ------------------------------------------------------------------
    # Statements
    # ------------------------------------------------------------------

    def _check_Block(self, node: N.Block) -> str:
        """Push a new scope, check all statements, pop scope."""
        self._table.push_scope()
        for stmt in node.statements:
            self._visit(stmt)
        self._table.pop_scope()
        node.inferred_type = "void"
        return "void"

    def _check_IfStmt(self, node: N.IfStmt) -> str:
        # Condition must be a boolean-like type
        cond_type = self._visit(node.condition)
        if not _is_bool_like(cond_type):
            raise SemanticError(
                f"'if' condition must be a numeric or bool expression, "
                f"got '{cond_type}'.",
                line=node.line,
            )

        self._visit(node.then_branch)
        if node.else_branch is not None:
            self._visit(node.else_branch)

        node.inferred_type = "void"
        return "void"

    def _check_WhileStmt(self, node: N.WhileStmt) -> str:
        # Condition must be a boolean-like type
        cond_type = self._visit(node.condition)
        if not _is_bool_like(cond_type):
            raise SemanticError(
                f"'while' condition must be a numeric or bool expression, "
                f"got '{cond_type}'.",
                line=node.line,
            )

        self._visit(node.body)
        node.inferred_type = "void"
        return "void"

    def _check_ReturnStmt(self, node: N.ReturnStmt) -> str:
        # Must be inside a function
        if self._current_return_type is None:
            raise SemanticError(
                "return statement outside of any function.",
                line=node.line,
            )

        self._has_return = True   # mark that we saw a return

        # void return
        if node.value is None:
            if self._current_return_type != "void":
                raise SemanticError(
                    f"Function '{self._current_function}' must return "
                    f"'{self._current_return_type}', but 'return;' returns nothing.",
                    line=node.line,
                )
            node.inferred_type = "void"
            return "void"

        # non-void return
        ret_type = self._visit(node.value)
        if not _types_compatible(self._current_return_type, ret_type):
            raise SemanticError(
                f"Function '{self._current_function}' has return type "
                f"'{self._current_return_type}' but return expression "
                f"has type '{ret_type}'.",
                line=node.line,
            )

        node.inferred_type = ret_type
        return ret_type

    def _check_ExprStmt(self, node: N.ExprStmt) -> str:
        t = self._visit(node.expr)
        node.inferred_type = t
        return t

    # ------------------------------------------------------------------
    # Expressions
    # ------------------------------------------------------------------

    def _check_Assign(self, node: N.Assign) -> str:
        # Look up the target variable
        sym = self._table.lookup(node.name, line=node.line)

        # Cannot assign to a function name
        if sym.kind == "function":
            raise SemanticError(
                f"'{node.name}' is a function and cannot be assigned to.",
                line=node.line,
            )

        # Check right-hand side type
        rhs_type = self._visit(node.value)
        if not _types_compatible(sym.type_, rhs_type):
            raise SemanticError(
                f"Cannot assign '{rhs_type}' to variable "
                f"'{node.name}' of type '{sym.type_}'.",
                line=node.line,
            )

        node.inferred_type = sym.type_
        return sym.type_

    def _check_BinaryOp(self, node: N.BinaryOp) -> str:
        left_type  = self._visit(node.left)
        right_type = self._visit(node.right)

        if node.op in _ARITHMETIC_OPS:
            # Both operands must be numeric
            if not _is_numeric(left_type):
                raise SemanticError(
                    f"Left operand of '{node.op}' must be numeric, "
                    f"got '{left_type}'.",
                    line=node.line,
                )
            if not _is_numeric(right_type):
                raise SemanticError(
                    f"Right operand of '{node.op}' must be numeric, "
                    f"got '{right_type}'.",
                    line=node.line,
                )
            result = _numeric_result(left_type, right_type)

        elif node.op in _COMPARISON_OPS:
            # Both operands should be numeric for meaningful comparison
            if not (_is_numeric(left_type) and _is_numeric(right_type)):
                raise SemanticError(
                    f"Comparison '{node.op}' requires numeric operands, "
                    f"got '{left_type}' and '{right_type}'.",
                    line=node.line,
                )
            result = "bool"

        elif node.op in _LOGICAL_OPS:
            # Logical operators produce bool; operands can be any bool-like
            result = "bool"

        else:
            raise SemanticError(
                f"Unknown binary operator '{node.op}'.",
                line=node.line,
            )

        node.inferred_type = result
        return result

    def _check_UnaryOp(self, node: N.UnaryOp) -> str:
        operand_type = self._visit(node.operand)

        if node.op == "-":
            if not _is_numeric(operand_type):
                raise SemanticError(
                    f"Unary '-' requires a numeric operand, "
                    f"got '{operand_type}'.",
                    line=node.line,
                )
            node.inferred_type = operand_type
            return operand_type

        if node.op == "!":
            node.inferred_type = "bool"
            return "bool"

        raise SemanticError(
            f"Unknown unary operator '{node.op}'.",
            line=node.line,
        )

    def _check_Literal(self, node: N.Literal) -> str:
        node.inferred_type = node.lit_type
        return node.lit_type

    def _check_Identifier(self, node: N.Identifier) -> str:
        sym = self._table.lookup(node.name, line=node.line)
        node.inferred_type = sym.type_
        return sym.type_

    def _check_FuncCall(self, node: N.FuncCall) -> str:
        # 1. Look up the name
        sym = self._table.lookup(node.name, line=node.line)

        # 2. Must be a function, not a variable
        if sym.kind != "function":
            raise SemanticError(
                f"'{node.name}' is a {sym.kind}, not a function.",
                line=node.line,
            )

        # 3. Check argument count
        expected_count = len(sym.param_types)
        actual_count   = len(node.args)
        if actual_count != expected_count:
            raise SemanticError(
                f"Function '{node.name}' expects {expected_count} argument(s) "
                f"but got {actual_count}.",
                line=node.line,
            )

        # 4. Check each argument type
        for i, (param_type, arg_node) in enumerate(
            zip(sym.param_types, node.args), start=1
        ):
            arg_type = self._visit(arg_node)
            if not _types_compatible(param_type, arg_type):
                raise SemanticError(
                    f"Argument {i} of call to '{node.name}': "
                    f"expected '{param_type}' but got '{arg_type}'.",
                    line=node.line,
                )

        node.inferred_type = sym.type_
        return sym.type_
