"""
ast_builder.py — Parse Tree Dict → AST Node Objects  (Member 2)
Walk the dict produced by parser.py and construct typed ASTNode instances.
"""

from ast_nodes import (
    Program, FunctionDecl, Param, VarDecl, Block,
    IfStmt, WhileStmt, ReturnStmt, ExprStmt,
    Assign, BinaryOp, UnaryOp, Literal, Identifier, FunctionCall, ASTNode,
)
from typing import Dict, Any, Optional


class ASTBuildError(Exception):
    pass


def build(node: Dict) -> ASTNode:
    """Dispatch on node['type'] and construct the corresponding ASTNode."""
    t = node.get("type")
    line = node.get("line", 0)
    dispatch = {
        "Program":      _build_program,
        "FunctionDecl": _build_function_decl,
        "VarDecl":      _build_var_decl,
        "Block":        _build_block,
        "IfStmt":       _build_if,
        "WhileStmt":    _build_while,
        "ReturnStmt":   _build_return,
        "ExprStmt":     _build_expr_stmt,
        "Assign":       _build_assign,
        "BinaryOp":     _build_binary_op,
        "UnaryOp":      _build_unary_op,
        "Literal":      _build_literal,
        "Identifier":   _build_identifier,
        "FunctionCall": _build_function_call,
    }
    if t not in dispatch:
        raise ASTBuildError(f"Unknown node type: {t!r} at line {line}")
    return dispatch[t](node)


def _build_program(node: Dict) -> Program:
    return Program(
        declarations=[build(d) for d in node.get("declarations", [])],
        line=node.get("line", 0),
    )


def _build_function_decl(node: Dict) -> FunctionDecl:
    params = [
        Param(name=p["name"], var_type=p["var_type"], line=p.get("line", 0))
        for p in node.get("params", [])
    ]
    return FunctionDecl(
        return_type=node["return_type"],
        name=node["name"],
        params=params,
        body=build(node["body"]) if node.get("body") else None,
        line=node.get("line", 0),
    )


def _build_var_decl(node: Dict) -> VarDecl:
    return VarDecl(
        var_type=node["var_type"],
        name=node["name"],
        value=build(node["value"]) if node.get("value") else None,
        line=node.get("line", 0),
    )


def _build_block(node: Dict) -> Block:
    return Block(
        statements=[build(s) for s in node.get("statements", [])],
        line=node.get("line", 0),
    )


def _build_if(node: Dict) -> IfStmt:
    return IfStmt(
        condition=build(node["condition"]),
        then=build(node["then"]),
        else_=build(node["else"]) if node.get("else") else None,
        line=node.get("line", 0),
    )


def _build_while(node: Dict) -> WhileStmt:
    return WhileStmt(
        condition=build(node["condition"]),
        body=build(node["body"]),
        line=node.get("line", 0),
    )


def _build_return(node: Dict) -> ReturnStmt:
    return ReturnStmt(
        value=build(node["value"]) if node.get("value") else None,
        line=node.get("line", 0),
    )


def _build_expr_stmt(node: Dict) -> ExprStmt:
    return ExprStmt(expr=build(node["expr"]), line=node.get("line", 0))


def _build_assign(node: Dict) -> Assign:
    return Assign(
        name=node["name"],
        value=build(node["value"]),
        line=node.get("line", 0),
    )


def _build_binary_op(node: Dict) -> BinaryOp:
    return BinaryOp(
        op=node["op"],
        left=build(node["left"]),
        right=build(node["right"]),
        line=node.get("line", 0),
    )


def _build_unary_op(node: Dict) -> UnaryOp:
    return UnaryOp(
        op=node["op"],
        operand=build(node["operand"]),
        line=node.get("line", 0),
    )


def _build_literal(node: Dict) -> Literal:
    return Literal(value=node["value"], line=node.get("line", 0))


def _build_identifier(node: Dict) -> Identifier:
    return Identifier(name=node["name"], line=node.get("line", 0))


def _build_function_call(node: Dict) -> FunctionCall:
    return FunctionCall(
        name=node["name"],
        args=[build(a) for a in node.get("args", [])],
        line=node.get("line", 0),
    )
