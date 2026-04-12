from src.semantic.ast_nodes import VarDecl, BinaryOp, Literal

node = VarDecl("int", "x", BinaryOp("+", Literal(5), Literal(3)))
print(node)