"""
ast_nodes.py  —  Member 2
==========================
Defines one Python class for every Mini-C construct.

Every node:
  • stores its children as typed fields
  • stores the source line number  (for error messages)
  • has an  inferred_type  field  (filled by semantic_checker.py)
  • has a  to_dict()  method      (produces the annotated AST dict
                                   that Member 3's code generator consumes)

Node hierarchy
--------------
ASTNode  (base)
 ├── Program
 ├── FuncDecl
 ├── Param
 ├── VarDecl
 ├── Block
 ├── IfStmt
 ├── WhileStmt
 ├── ReturnStmt
 ├── ExprStmt
 ├── Assign
 ├── BinaryOp
 ├── UnaryOp
 ├── Literal
 ├── Identifier
 └── FuncCall
"""

from __future__ import annotations
from typing import Any, List, Optional


# ---------------------------------------------------------------------------
# Base node
# ---------------------------------------------------------------------------

class ASTNode:
    """Abstract base for all AST nodes."""

    def __init__(self, line: int = 0) -> None:
        self.line: int = line
        # Filled in by SemanticChecker; None until then
        self.inferred_type: Optional[str] = None

    def __repr__(self) -> str:
        fields = ", ".join(
            f"{k}={v!r}"
            for k, v in self.__dict__.items()
            if k not in ("line",) and v is not None
        )
        return f"{type(self).__name__}({fields})"

    def to_dict(self) -> dict:
        """
        Return a plain dict representation of this node (including
        inferred_type). This is what Member 3's CodeGenerator walks.
        """
        raise NotImplementedError(f"{type(self).__name__}.to_dict() not implemented")


# ---------------------------------------------------------------------------
# Top-level
# ---------------------------------------------------------------------------

class Program(ASTNode):
    """
    Root node of the AST.
    Holds all top-level declarations (functions and global variables).
    """

    def __init__(self, declarations: List[ASTNode], line: int = 0) -> None:
        super().__init__(line)
        self.declarations: List[ASTNode] = declarations

    def to_dict(self) -> dict:
        return {
            "type": "Program",
            "declarations": [d.to_dict() for d in self.declarations],
            "inferred_type": self.inferred_type,
        }


# ---------------------------------------------------------------------------
# Declarations
# ---------------------------------------------------------------------------

class FuncDecl(ASTNode):
    """
    A function declaration.

    Example Mini-C:   int add(int a, int b) { return a + b; }

    Fields:
        return_type  : "int" | "float" | "void"
        name         : function name string
        params       : list of Param nodes
        body         : Block node
    """

    def __init__(
        self,
        return_type: str,
        name: str,
        params: List["Param"],
        body: "Block",
        line: int = 0,
    ) -> None:
        super().__init__(line)
        self.return_type: str        = return_type
        self.name:        str        = name
        self.params:      List[Param] = params
        self.body:        Block      = body

    def to_dict(self) -> dict:
        return {
            "type":        "FuncDecl",
            "return_type": self.return_type,
            "name":        self.name,
            "params":      [p.to_dict() for p in self.params],
            "body":        self.body.to_dict(),
            "inferred_type": self.inferred_type,
            "line":        self.line,
        }


class Param(ASTNode):
    """
    A single function parameter.

    Example Mini-C:  int a
    """

    def __init__(self, var_type: str, name: str, line: int = 0) -> None:
        super().__init__(line)
        self.var_type: str = var_type
        self.name:     str = name

    def to_dict(self) -> dict:
        return {
            "type":          "Param",
            "var_type":      self.var_type,
            "name":          self.name,
            "inferred_type": self.inferred_type,
            "line":          self.line,
        }


class VarDecl(ASTNode):
    """
    A variable declaration, optionally with an initialiser.

    Example Mini-C:  int x = 5 + 3;
                     float y;          (no initialiser)

    Fields:
        var_type : declared C type ("int" | "float" | "void")
        name     : variable name
        value    : optional initialiser expression node
    """

    def __init__(
        self,
        var_type: str,
        name:     str,
        value:    Optional[ASTNode] = None,
        line:     int = 0,
    ) -> None:
        super().__init__(line)
        self.var_type: str              = var_type
        self.name:     str              = name
        self.value:    Optional[ASTNode] = value

    def to_dict(self) -> dict:
        node: dict = {
            "type":          "VarDecl",
            "var_type":      self.var_type,
            "name":          self.name,
            "inferred_type": self.inferred_type,
            "line":          self.line,
        }
        if self.value is not None:
            node["value"] = self.value.to_dict()
        return node


# ---------------------------------------------------------------------------
# Statements
# ---------------------------------------------------------------------------

class Block(ASTNode):
    """
    A braced sequence of statements  { stmt1; stmt2; ... }
    """

    def __init__(self, statements: List[ASTNode], line: int = 0) -> None:
        super().__init__(line)
        self.statements: List[ASTNode] = statements

    def to_dict(self) -> dict:
        return {
            "type":       "Block",
            "statements": [s.to_dict() for s in self.statements],
            "line":       self.line,
        }


class IfStmt(ASTNode):
    """
    if (condition) then_branch [ else else_branch ]

    Example Mini-C:
        if (x > 0) { return x; } else { return -x; }
    """

    def __init__(
        self,
        condition:   ASTNode,
        then_branch: Block,
        else_branch: Optional[Block] = None,
        line:        int = 0,
    ) -> None:
        super().__init__(line)
        self.condition:   ASTNode          = condition
        self.then_branch: Block            = then_branch
        self.else_branch: Optional[Block]  = else_branch

    def to_dict(self) -> dict:
        return {
            "type":        "IfStmt",
            "condition":   self.condition.to_dict(),
            "then_branch": self.then_branch.to_dict(),
            "else_branch": self.else_branch.to_dict() if self.else_branch else None,
            "inferred_type": self.inferred_type,
            "line":        self.line,
        }


class WhileStmt(ASTNode):
    """
    while (condition) body

    Example Mini-C:
        while (i < 10) { i = i + 1; }
    """

    def __init__(self, condition: ASTNode, body: Block, line: int = 0) -> None:
        super().__init__(line)
        self.condition: ASTNode = condition
        self.body:      Block   = body

    def to_dict(self) -> dict:
        return {
            "type":        "WhileStmt",
            "condition":   self.condition.to_dict(),
            "body":        self.body.to_dict(),
            "inferred_type": self.inferred_type,
            "line":        self.line,
        }


class ReturnStmt(ASTNode):
    """
    return [value];

    Example Mini-C:
        return a + b;
        return;          (void function)
    """

    def __init__(self, value: Optional[ASTNode] = None, line: int = 0) -> None:
        super().__init__(line)
        self.value: Optional[ASTNode] = value

    def to_dict(self) -> dict:
        node: dict = {
            "type":          "ReturnStmt",
            "inferred_type": self.inferred_type,
            "line":          self.line,
        }
        if self.value is not None:
            node["value"] = self.value.to_dict()
        return node


class ExprStmt(ASTNode):
    """
    A statement that is just an expression followed by semicolon.
    Commonly used for function calls and assignments used as statements.

    Example Mini-C:  foo(1, 2);
    """

    def __init__(self, expr: ASTNode, line: int = 0) -> None:
        super().__init__(line)
        self.expr: ASTNode = expr

    def to_dict(self) -> dict:
        return {
            "type":          "ExprStmt",
            "expr":          self.expr.to_dict(),
            "inferred_type": self.inferred_type,
            "line":          self.line,
        }


# ---------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------

class Assign(ASTNode):
    """
    Variable assignment expression:  name = value

    Example Mini-C:  x = x + 1;
    """

    def __init__(self, name: str, value: ASTNode, line: int = 0) -> None:
        super().__init__(line)
        self.name:  str     = name
        self.value: ASTNode = value

    def to_dict(self) -> dict:
        return {
            "type":          "Assign",
            "name":          self.name,
            "value":         self.value.to_dict(),
            "inferred_type": self.inferred_type,
            "line":          self.line,
        }


class BinaryOp(ASTNode):
    """
    Binary operation:  left  op  right

    op is one of:  + - * / %  ==  != < > <= >=  && ||

    Example Mini-C:  a + b * 2
    """

    def __init__(
        self,
        op:    str,
        left:  ASTNode,
        right: ASTNode,
        line:  int = 0,
    ) -> None:
        super().__init__(line)
        self.op:    str     = op
        self.left:  ASTNode = left
        self.right: ASTNode = right

    def to_dict(self) -> dict:
        return {
            "type":          "BinaryOp",
            "op":            self.op,
            "left":          self.left.to_dict(),
            "right":         self.right.to_dict(),
            "inferred_type": self.inferred_type,
            "line":          self.line,
        }


class UnaryOp(ASTNode):
    """
    Unary operation:  op  operand

    op is one of:  -  !

    Example Mini-C:  -x    !flag
    """

    def __init__(self, op: str, operand: ASTNode, line: int = 0) -> None:
        super().__init__(line)
        self.op:      str     = op
        self.operand: ASTNode = operand

    def to_dict(self) -> dict:
        return {
            "type":          "UnaryOp",
            "op":            self.op,
            "operand":       self.operand.to_dict(),
            "inferred_type": self.inferred_type,
            "line":          self.line,
        }


class Literal(ASTNode):
    """
    A numeric or boolean literal.

    Fields:
        value    : Python int / float / bool
        lit_type : "int" | "float" | "bool"

    Example Mini-C:  5    3.14    true    false
    """

    def __init__(self, value: Any, lit_type: str, line: int = 0) -> None:
        super().__init__(line)
        self.value:    Any = value
        self.lit_type: str = lit_type

    def to_dict(self) -> dict:
        return {
            "type":          "Literal",
            "value":         self.value,
            "lit_type":      self.lit_type,
            "inferred_type": self.inferred_type,
            "line":          self.line,
        }


class Identifier(ASTNode):
    """
    A variable or function name reference.

    Example Mini-C:  x    result    add
    """

    def __init__(self, name: str, line: int = 0) -> None:
        super().__init__(line)
        self.name: str = name

    def to_dict(self) -> dict:
        return {
            "type":          "Identifier",
            "name":          self.name,
            "inferred_type": self.inferred_type,
            "line":          self.line,
        }


class FuncCall(ASTNode):
    """
    A function call expression.

    Example Mini-C:  add(a, b)    factorial(n - 1)

    Fields:
        name : function name
        args : list of argument expression nodes
    """

    def __init__(self, name: str, args: List[ASTNode], line: int = 0) -> None:
        super().__init__(line)
        self.name: str            = name
        self.args: List[ASTNode] = args

    def to_dict(self) -> dict:
        return {
            "type":          "FuncCall",
            "name":          self.name,
            "args":          [a.to_dict() for a in self.args],
            "inferred_type": self.inferred_type,
            "line":          self.line,
        }
