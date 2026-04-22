"""
ast_builder.py  —  Member 2
============================
Converts a parse tree dictionary (Member 1's parser output, or the mock
from interfaces.py) into a tree of typed ASTNode objects.

HOW IT WORKS
------------
The builder is a single-dispatch visitor. Every node dict has a "type" key
(e.g. "VarDecl", "BinaryOp"). The builder looks up a method called
  _build_<type>(node_dict)
and calls it. Each method constructs and returns the matching ASTNode.

HOW MEMBER 2 USES IT STANDALONE
---------------------------------
    from interfaces import MOCK_PARSE_TREE_PROGRAM
    from ast_builder import ASTBuilder

    builder  = ASTBuilder()
    ast_root = builder.build(MOCK_PARSE_TREE_PROGRAM)
    print(ast_root)

In Week 4, swap MOCK_PARSE_TREE_PROGRAM for Member 1's real parser output.
The builder code does NOT change.
"""

from __future__ import annotations
from typing import List, Optional

from interfaces import IASTBuilder, ParseTree, CompilerError
import ast_nodes as N


class ASTBuilder(IASTBuilder):
    """
    Transforms a parse-tree dict into a tree of ASTNode objects.

    Entry point:
        root = ASTBuilder().build(parse_tree_dict)   # returns N.Program
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(self, parse_tree: ParseTree) -> N.Program:
        """
        Convert *parse_tree* (nested dict from parser) into AST objects.
        Returns the root N.Program node.
        """
        result = self._visit(parse_tree)
        if not isinstance(result, N.Program):
            raise CompilerError(
                f"ASTBuilder expected a Program node at root, got {type(result).__name__}"
            )
        return result

    # ------------------------------------------------------------------
    # Dispatch — routes each dict to the right _build_X method
    # ------------------------------------------------------------------

    def _visit(self, node: ParseTree) -> N.ASTNode:
        """Visit one parse-tree dict and return the corresponding ASTNode."""
        kind   = node.get("type")
        method = getattr(self, f"_build_{kind}", None)
        if method is None:
            raise CompilerError(
                f"ASTBuilder: no handler for node type '{kind}'",
                line=node.get("line"),
            )
        return method(node)

    def _visit_optional(self, node: Optional[ParseTree]) -> Optional[N.ASTNode]:
        """Visit a node dict that may be None."""
        return self._visit(node) if node is not None else None

    def _visit_list(self, nodes: List[ParseTree]) -> List[N.ASTNode]:
        """Visit a list of node dicts and return a list of ASTNodes."""
        return [self._visit(n) for n in nodes]

    # ------------------------------------------------------------------
    # Program
    # ------------------------------------------------------------------

    def _build_Program(self, node: ParseTree) -> N.Program:
        declarations = self._visit_list(node.get("declarations", []))
        return N.Program(declarations=declarations, line=node.get("line", 0))

    # ------------------------------------------------------------------
    # Declarations
    # ------------------------------------------------------------------

    def _build_FuncDecl(self, node: ParseTree) -> N.FuncDecl:
        params = [self._build_Param(p) for p in node.get("params", [])]
        body   = self._build_Block(node["body"])
        return N.FuncDecl(
            return_type = node["return_type"],
            name        = node["name"],
            params      = params,
            body        = body,
            line        = node.get("line", 0),
        )

    def _build_Param(self, node: ParseTree) -> N.Param:
        return N.Param(
            var_type = node["var_type"],
            name     = node["name"],
            line     = node.get("line", 0),
        )

    def _build_VarDecl(self, node: ParseTree) -> N.VarDecl:
        value = self._visit_optional(node.get("value"))
        return N.VarDecl(
            var_type = node["var_type"],
            name     = node["name"],
            value    = value,
            line     = node.get("line", 0),
        )

    # ------------------------------------------------------------------
    # Statements
    # ------------------------------------------------------------------

    def _build_Block(self, node: ParseTree) -> N.Block:
        stmts = self._visit_list(node.get("statements", []))
        return N.Block(statements=stmts, line=node.get("line", 0))

    def _build_IfStmt(self, node: ParseTree) -> N.IfStmt:
        condition   = self._visit(node["condition"])
        then_branch = self._build_Block(node["then_branch"])
        else_branch = (
            self._build_Block(node["else_branch"])
            if node.get("else_branch") else None
        )
        return N.IfStmt(
            condition   = condition,
            then_branch = then_branch,
            else_branch = else_branch,
            line        = node.get("line", 0),
        )

    def _build_WhileStmt(self, node: ParseTree) -> N.WhileStmt:
        condition = self._visit(node["condition"])
        body      = self._build_Block(node["body"])
        return N.WhileStmt(condition=condition, body=body, line=node.get("line", 0))

    def _build_ReturnStmt(self, node: ParseTree) -> N.ReturnStmt:
        value = self._visit_optional(node.get("value"))
        return N.ReturnStmt(value=value, line=node.get("line", 0))

    def _build_ExprStmt(self, node: ParseTree) -> N.ExprStmt:
        expr = self._visit(node["expr"])
        return N.ExprStmt(expr=expr, line=node.get("line", 0))

    # ------------------------------------------------------------------
    # Expressions
    # ------------------------------------------------------------------

    def _build_Assign(self, node: ParseTree) -> N.Assign:
        value = self._visit(node["value"])
        return N.Assign(name=node["name"], value=value, line=node.get("line", 0))

    def _build_BinaryOp(self, node: ParseTree) -> N.BinaryOp:
        left  = self._visit(node["left"])
        right = self._visit(node["right"])
        return N.BinaryOp(
            op    = node["op"],
            left  = left,
            right = right,
            line  = node.get("line", 0),
        )

    def _build_UnaryOp(self, node: ParseTree) -> N.UnaryOp:
        operand = self._visit(node["operand"])
        return N.UnaryOp(op=node["op"], operand=operand, line=node.get("line", 0))

    def _build_Literal(self, node: ParseTree) -> N.Literal:
        return N.Literal(
            value    = node["value"],
            lit_type = node["lit_type"],
            line     = node.get("line", 0),
        )

    def _build_Identifier(self, node: ParseTree) -> N.Identifier:
        return N.Identifier(name=node["name"], line=node.get("line", 0))

    def _build_FuncCall(self, node: ParseTree) -> N.FuncCall:
        args = self._visit_list(node.get("args", []))
        return N.FuncCall(name=node["name"], args=args, line=node.get("line", 0))
