"""
ast_nodes.py — AST Node Classes  (Member 2)
Every Mini-C construct has a corresponding Python dataclass.
Each node stores its source line number for error reporting.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any


@dataclass
class ASTNode:
    line: int = 0
    inferred_type: Optional[str] = None


@dataclass
class Program(ASTNode):
    declarations: List[ASTNode] = field(default_factory=list)


@dataclass
class FunctionDecl(ASTNode):
    return_type: str = ""
    name: str = ""
    params: List["Param"] = field(default_factory=list)
    body: Optional["Block"] = None


@dataclass
class Param(ASTNode):
    name: str = ""
    var_type: str = ""


@dataclass
class VarDecl(ASTNode):
    var_type: str = ""
    name: str = ""
    value: Optional[ASTNode] = None


@dataclass
class Block(ASTNode):
    statements: List[ASTNode] = field(default_factory=list)


@dataclass
class IfStmt(ASTNode):
    condition: Optional[ASTNode] = None
    then: Optional[ASTNode] = None
    else_: Optional[ASTNode] = None


@dataclass
class WhileStmt(ASTNode):
    condition: Optional[ASTNode] = None
    body: Optional[ASTNode] = None


@dataclass
class ReturnStmt(ASTNode):
    value: Optional[ASTNode] = None


@dataclass
class ExprStmt(ASTNode):
    expr: Optional[ASTNode] = None


@dataclass
class Assign(ASTNode):
    name: str = ""
    value: Optional[ASTNode] = None


@dataclass
class BinaryOp(ASTNode):
    op: str = ""
    left: Optional[ASTNode] = None
    right: Optional[ASTNode] = None


@dataclass
class UnaryOp(ASTNode):
    op: str = ""
    operand: Optional[ASTNode] = None


@dataclass
class Literal(ASTNode):
    value: Any = None


@dataclass
class Identifier(ASTNode):
    name: str = ""


@dataclass
class FunctionCall(ASTNode):
    name: str = ""
    args: List[ASTNode] = field(default_factory=list)
