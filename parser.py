"""
parser.py — Mini-C Recursive Descent Parser  (Member 1)
Converts token list → parse tree dict matching interfaces.py format.
"""

from lexer import Token, tokenize, LexerError
from typing import List, Any, Dict


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    # ── Helpers ──────────────────────────────────────────────────────────────
    def current(self) -> Token:
        return self.tokens[self.pos]

    def peek(self, offset=1) -> Token:
        p = self.pos + offset
        return self.tokens[p] if p < len(self.tokens) else self.tokens[-1]

    def eat(self, expected_type: str) -> Token:
        tok = self.current()
        if tok.type != expected_type:
            raise ParseError(
                f"Line {tok.line}: expected {expected_type!r}, got {tok.type!r} ({tok.value!r})"
            )
        self.pos += 1
        return tok

    def match(self, *types) -> bool:
        return self.current().type in types

    # ── Entry ─────────────────────────────────────────────────────────────────
    def parse_program(self) -> Dict:
        decls = []
        while not self.match("EOF"):
            decls.append(self.parse_top_level())
        return {"type": "Program", "declarations": decls}

    def parse_top_level(self) -> Dict:
        # type name ( ... ) { ... }  →  FunctionDecl
        # type name ;  or  type name = expr ;  →  VarDecl
        type_tok = self.parse_type()
        name_tok = self.eat("ID")
        if self.match("LPAREN"):
            return self.parse_function_decl(type_tok, name_tok)
        return self.parse_var_decl_tail(type_tok, name_tok)

    def parse_type(self) -> str:
        tok = self.current()
        if tok.type in ("INT", "FLOAT", "VOID"):
            self.pos += 1
            return tok.value
        raise ParseError(f"Line {tok.line}: expected type keyword, got {tok.value!r}")

    # ── Function declaration ──────────────────────────────────────────────────
    def parse_function_decl(self, return_type: str, name_tok: Token) -> Dict:
        self.eat("LPAREN")
        params = []
        if not self.match("RPAREN"):
            params = self.parse_param_list()
        self.eat("RPAREN")
        body = self.parse_block()
        return {
            "type": "FunctionDecl",
            "return_type": return_type,
            "name": name_tok.value,
            "params": params,
            "body": body,
            "line": name_tok.line,
        }

    def parse_param_list(self) -> List[Dict]:
        params = []
        while True:
            ptype = self.parse_type()
            pname = self.eat("ID")
            params.append({"name": pname.value, "var_type": ptype, "line": pname.line})
            if not self.match("COMMA"):
                break
            self.eat("COMMA")
        return params

    # ── Block & statements ────────────────────────────────────────────────────
    def parse_block(self) -> Dict:
        self.eat("LBRACE")
        stmts = []
        while not self.match("RBRACE", "EOF"):
            stmts.append(self.parse_statement())
        self.eat("RBRACE")
        return {"type": "Block", "statements": stmts}

    def parse_statement(self) -> Dict:
        tok = self.current()
        if tok.type in ("INT", "FLOAT", "VOID"):
            return self.parse_local_var_decl()
        if tok.type == "IF":
            return self.parse_if()
        if tok.type == "WHILE":
            return self.parse_while()
        if tok.type == "RETURN":
            return self.parse_return()
        if tok.type == "LBRACE":
            return self.parse_block()
        # assignment or function call
        return self.parse_expr_stmt()

    def parse_local_var_decl(self) -> Dict:
        type_tok = self.parse_type()
        name_tok = self.eat("ID")
        return self.parse_var_decl_tail(type_tok, name_tok)

    def parse_var_decl_tail(self, var_type: str, name_tok: Token) -> Dict:
        value = None
        if self.match("ASSIGN"):
            self.eat("ASSIGN")
            value = self.parse_expr()
        self.eat("SEMICOLON")
        node = {"type": "VarDecl", "var_type": var_type, "name": name_tok.value, "line": name_tok.line}
        if value is not None:
            node["value"] = value
        return node

    def parse_if(self) -> Dict:
        line = self.current().line
        self.eat("IF")
        self.eat("LPAREN")
        cond = self.parse_expr()
        self.eat("RPAREN")
        then_block = self.parse_block()
        else_block = None
        if self.match("ELSE"):
            self.eat("ELSE")
            if self.match("IF"):
                else_block = self.parse_if()
            else:
                else_block = self.parse_block()
        node = {"type": "IfStmt", "condition": cond, "then": then_block, "line": line}
        if else_block:
            node["else"] = else_block
        return node

    def parse_while(self) -> Dict:
        line = self.current().line
        self.eat("WHILE")
        self.eat("LPAREN")
        cond = self.parse_expr()
        self.eat("RPAREN")
        body = self.parse_block()
        return {"type": "WhileStmt", "condition": cond, "body": body, "line": line}

    def parse_return(self) -> Dict:
        line = self.current().line
        self.eat("RETURN")
        value = None
        if not self.match("SEMICOLON"):
            value = self.parse_expr()
        self.eat("SEMICOLON")
        node = {"type": "ReturnStmt", "line": line}
        if value is not None:
            node["value"] = value
        return node

    def parse_expr_stmt(self) -> Dict:
        # Could be: name = expr ;   OR   name(args) ;
        expr = self.parse_expr()
        self.eat("SEMICOLON")
        return {"type": "ExprStmt", "expr": expr}

    # ── Expressions (Pratt-like with precedence levels) ───────────────────────
    def parse_expr(self) -> Dict:
        return self.parse_assign()

    def parse_assign(self) -> Dict:
        left = self.parse_or()
        if self.match("ASSIGN") and left["type"] == "Identifier":
            self.eat("ASSIGN")
            right = self.parse_assign()
            return {"type": "Assign", "name": left["name"], "value": right, "line": left["line"]}
        return left

    def parse_or(self) -> Dict:
        left = self.parse_and()
        while self.match("OR"):
            op = self.tokens[self.pos].value; self.pos += 1
            right = self.parse_and()
            left = {"type": "BinaryOp", "op": op, "left": left, "right": right}
        return left

    def parse_and(self) -> Dict:
        left = self.parse_equality()
        while self.match("AND"):
            op = self.tokens[self.pos].value; self.pos += 1
            right = self.parse_equality()
            left = {"type": "BinaryOp", "op": op, "left": left, "right": right}
        return left

    def parse_equality(self) -> Dict:
        left = self.parse_relational()
        while self.match("EQ", "NEQ"):
            op = self.tokens[self.pos].value; self.pos += 1
            right = self.parse_relational()
            left = {"type": "BinaryOp", "op": op, "left": left, "right": right}
        return left

    def parse_relational(self) -> Dict:
        left = self.parse_additive()
        while self.match("LT", "GT", "LEQ", "GEQ"):
            op = self.tokens[self.pos].value; self.pos += 1
            right = self.parse_additive()
            left = {"type": "BinaryOp", "op": op, "left": left, "right": right}
        return left

    def parse_additive(self) -> Dict:
        left = self.parse_multiplicative()
        while self.match("PLUS", "MINUS"):
            op = self.tokens[self.pos].value; self.pos += 1
            right = self.parse_multiplicative()
            left = {"type": "BinaryOp", "op": op, "left": left, "right": right}
        return left

    def parse_multiplicative(self) -> Dict:
        left = self.parse_unary()
        while self.match("STAR", "SLASH"):
            op = self.tokens[self.pos].value; self.pos += 1
            right = self.parse_unary()
            left = {"type": "BinaryOp", "op": op, "left": left, "right": right}
        return left

    def parse_unary(self) -> Dict:
        if self.match("NOT"):
            op = self.tokens[self.pos].value; self.pos += 1
            operand = self.parse_unary()
            return {"type": "UnaryOp", "op": op, "operand": operand}
        if self.match("MINUS"):
            self.pos += 1
            operand = self.parse_unary()
            return {"type": "UnaryOp", "op": "-", "operand": operand}
        return self.parse_call_or_primary()

    def parse_call_or_primary(self) -> Dict:
        node = self.parse_primary()
        if node["type"] == "Identifier" and self.match("LPAREN"):
            self.eat("LPAREN")
            args = []
            if not self.match("RPAREN"):
                args.append(self.parse_expr())
                while self.match("COMMA"):
                    self.eat("COMMA")
                    args.append(self.parse_expr())
            self.eat("RPAREN")
            return {"type": "FunctionCall", "name": node["name"], "args": args, "line": node["line"]}
        return node

    def parse_primary(self) -> Dict:
        tok = self.current()
        if tok.type == "INT_LIT":
            self.pos += 1
            return {"type": "Literal", "value": int(tok.value), "inferred_type": "int", "line": tok.line}
        if tok.type == "FLOAT_LIT":
            self.pos += 1
            return {"type": "Literal", "value": float(tok.value), "inferred_type": "float", "line": tok.line}
        if tok.type in ("TRUE", "FALSE"):
            self.pos += 1
            return {"type": "Literal", "value": tok.value == "true", "inferred_type": "bool", "line": tok.line}
        if tok.type == "STRING_LIT":
            self.pos += 1
            return {"type": "Literal", "value": tok.value[1:-1], "inferred_type": "string", "line": tok.line}
        if tok.type == "ID":
            self.pos += 1
            return {"type": "Identifier", "name": tok.value, "line": tok.line}
        if tok.type == "LPAREN":
            self.eat("LPAREN")
            expr = self.parse_expr()
            self.eat("RPAREN")
            return expr
        raise ParseError(f"Line {tok.line}: unexpected token {tok.type!r} ({tok.value!r})")


def parse(source: str) -> Dict:
    tokens = tokenize(source)
    return Parser(tokens).parse_program()


if __name__ == "__main__":
    import json
    src = """
int add(int a, int b) {
    return a + b;
}
int main() {
    int x = 5 + 3;
    float y = 3.14;
    if (x > 0) {
        x = x - 1;
    } else {
        x = 0;
    }
    while (x < 10) {
        x = x + 1;
    }
    return add(x, 2);
}
"""
    tree = parse(src)
    print(json.dumps(tree, indent=2))
