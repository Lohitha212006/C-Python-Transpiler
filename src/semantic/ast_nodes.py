class ASTNode:
    def __init__(self):
        self.inferred_type = None


class VarDecl(ASTNode):
    def __init__(self, var_type, name, value):
        super().__init__()
        self.var_type = var_type
        self.name = name
        self.value = value

    def __repr__(self):
        return f"VarDecl({self.var_type} {self.name} = {self.value})"


class BinaryOp(ASTNode):
    def __init__(self, op, left, right):
        super().__init__()
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return f"({self.left} {self.op} {self.right})"


class Literal(ASTNode):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def __repr__(self):
        return str(self.value)


class Identifier(ASTNode):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def __repr__(self):
        return self.name