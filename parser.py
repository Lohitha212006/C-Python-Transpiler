# parser.py  ── Member 1
# Recursive-descent parser. Consumes a token list from lexer.py
# and produces a parse tree (nested dict) matching interfaces.py.
# ─────────────────────────────────────────────────────────────────────────────
#
# Mini-C Grammar (EBNF)
# ──────────────────────
# program        → function_decl+
# function_decl  → type IDENT '(' params ')' block
# params         → ε | param (',' param)*
# param          → type IDENT
# type           → 'int' | 'float' | 'void'
# block          → '{' statement* '}'
# statement      → var_decl | assign_stmt | if_stmt | while_stmt
#                | return_stmt | expr_stmt
# var_decl       → type IDENT ('=' expr)? ';'
# assign_stmt    → IDENT '=' expr ';'
# if_stmt        → 'if' '(' expr ')' block ('else' block)?
# while_stmt     → 'while' '(' expr ')' block
# return_stmt    → 'return' expr? ';'
# expr_stmt      → expr ';'
# expr           → or_expr
# or_expr        → and_expr ('||' and_expr)*
# and_expr       → equality ('&&' equality)*
# equality       → relational (('=='|'!=') relational)*
# relational     → additive  (('<'|'>'|'<='|'>=') additive)*
# additive       → term (('+' | '-') term)*
# term           → unary (('*' | '/') unary)*
# unary          → ('!' | '-') unary | primary
# primary        → INT_LIT | FLOAT_LIT | IDENT ('(' args ')')? | '(' expr ')'
# args           → ε | expr (',' expr)*

from lexer import Lexer, LexerError, Token


class ParseError(Exception):
    pass


class Parser:
    """
    Usage:
        tokens = Lexer(source).tokenize()
        tree   = Parser(tokens).parse()   # returns parse-tree dict
    """

    def __init__(self, tokens: list[Token]):
        self._tokens = tokens
        self._pos    = 0

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _peek(self) -> Token:
        return self._tokens[self._pos]

    def _advance(self) -> Token:
        tok = self._tokens[self._pos]
        if tok.type != "EOF":
            self._pos += 1
        return tok

    def _check(self, *types) -> bool:
        return self._peek().type in types

    def _expect(self, *types) -> Token:
        tok = self._peek()
        if tok.type not in types:
            expected = " or ".join(types)
            raise ParseError(
                f"Line {tok.line}: expected {expected}, got {tok.type!r} ({tok.value!r})"
            )
        return self._advance()

    def _match(self, *types) -> Token | None:
        if self._check(*types):
            return self._advance()
        return None

    def _is_type_keyword(self) -> bool:
        return self._check("INT", "FLOAT", "VOID")

    # ── Top level ─────────────────────────────────────────────────────────────

    def parse(self) -> dict:
        functions = []
        while not self._check("EOF"):
            functions.append(self._function_decl())
        if not functions:
            raise ParseError("Program must contain at least one function.")
        return {"type": "Program", "functions": functions}

    # ── Function declaration ──────────────────────────────────────────────────

    def _function_decl(self) -> dict:
        ret_type = self._type()
        name_tok = self._expect("IDENT")
        self._expect("LPAREN")
        params = self._params()
        self._expect("RPAREN")
        body = self._block()
        return {
            "type":        "FunctionDecl",
            "return_type": ret_type,
            "name":        name_tok.value,
            "params":      params,
            "body":        body,
            "line":        name_tok.line,
        }

    def _params(self) -> list[dict]:
        params = []
        if self._is_type_keyword():
            params.append(self._param())
            while self._match("COMMA"):
                params.append(self._param())
        return params

    def _param(self) -> dict:
        var_type = self._type()
        name_tok = self._expect("IDENT")
        return {"type": "Param", "var_type": var_type, "name": name_tok.value, "line": name_tok.line}

    def _type(self) -> str:
        tok = self._advance()
        if tok.type not in ("INT", "FLOAT", "VOID"):
            raise ParseError(f"Line {tok.line}: expected type keyword, got {tok.type!r}")
        return tok.value  # "int", "float", "void"

    # ── Block & statements ────────────────────────────────────────────────────

    def _block(self) -> dict:
        self._expect("LBRACE")
        stmts = []
        while not self._check("RBRACE", "EOF"):
            stmts.append(self._statement())
        self._expect("RBRACE")
        return {"type": "Block", "statements": stmts}

    def _statement(self) -> dict:
        tok = self._peek()

        # var declaration: starts with a type keyword followed by IDENT
        if self._is_type_keyword():
            # peek two ahead to distinguish  int x  vs  int(  (cast – not supported)
            return self._var_decl()

        if tok.type == "IF":
            return self._if_stmt()

        if tok.type == "WHILE":
            return self._while_stmt()

        if tok.type == "RETURN":
            return self._return_stmt()

        # assignment  IDENT '=' expr ';'  or  expr_stmt
        if tok.type == "IDENT":
            # look ahead one more token
            next_pos = self._pos + 1
            if next_pos < len(self._tokens) and self._tokens[next_pos].type == "ASSIGN":
                return self._assign_stmt()

        return self._expr_stmt()

    def _var_decl(self) -> dict:
        var_type = self._type()
        name_tok = self._expect("IDENT")
        value = None
        if self._match("ASSIGN"):
            value = self._expr()
        self._expect("SEMICOLON")
        return {
            "type":     "VarDecl",
            "var_type": var_type,
            "name":     name_tok.value,
            "value":    value,
            "line":     name_tok.line,
        }

    def _assign_stmt(self) -> dict:
        name_tok = self._expect("IDENT")
        self._expect("ASSIGN")
        value = self._expr()
        self._expect("SEMICOLON")
        return {
            "type":  "AssignStmt",
            "name":  name_tok.value,
            "value": value,
            "line":  name_tok.line,
        }

    def _if_stmt(self) -> dict:
        line = self._peek().line
        self._expect("IF")
        self._expect("LPAREN")
        condition = self._expr()
        self._expect("RPAREN")
        then_block = self._block()
        else_block = None
        if self._match("ELSE"):
            else_block = self._block()
        return {
            "type":       "IfStmt",
            "condition":  condition,
            "then_block": then_block,
            "else_block": else_block,
            "line":       line,
        }

    def _while_stmt(self) -> dict:
        line = self._peek().line
        self._expect("WHILE")
        self._expect("LPAREN")
        condition = self._expr()
        self._expect("RPAREN")
        body = self._block()
        return {"type": "WhileStmt", "condition": condition, "body": body, "line": line}

    def _return_stmt(self) -> dict:
        line = self._peek().line
        self._expect("RETURN")
        value = None
        if not self._check("SEMICOLON"):
            value = self._expr()
        self._expect("SEMICOLON")
        return {"type": "ReturnStmt", "value": value, "line": line}

    def _expr_stmt(self) -> dict:
        expr = self._expr()
        self._expect("SEMICOLON")
        return {"type": "ExprStmt", "expr": expr, "line": expr.get("line", 0)}

    # ── Expression hierarchy (operator precedence) ────────────────────────────

    def _expr(self) -> dict:
        return self._or_expr()

    def _or_expr(self) -> dict:
        left = self._and_expr()
        while self._check("OR"):
            op_tok = self._advance()
            right  = self._and_expr()
            left   = {"type": "BinaryOp", "op": "||", "left": left, "right": right, "line": op_tok.line}
        return left

    def _and_expr(self) -> dict:
        left = self._equality()
        while self._check("AND"):
            op_tok = self._advance()
            right  = self._equality()
            left   = {"type": "BinaryOp", "op": "&&", "left": left, "right": right, "line": op_tok.line}
        return left

    def _equality(self) -> dict:
        left = self._relational()
        while self._check("EQ", "NEQ"):
            op_tok = self._advance()
            right  = self._relational()
            left   = {"type": "BinaryOp", "op": op_tok.value, "left": left, "right": right, "line": op_tok.line}
        return left

    def _relational(self) -> dict:
        left = self._additive()
        while self._check("LT", "GT", "LEQ", "GEQ"):
            op_tok = self._advance()
            right  = self._additive()
            left   = {"type": "BinaryOp", "op": op_tok.value, "left": left, "right": right, "line": op_tok.line}
        return left

    def _additive(self) -> dict:
        left = self._term()
        while self._check("PLUS", "MINUS"):
            op_tok = self._advance()
            right  = self._term()
            left   = {"type": "BinaryOp", "op": op_tok.value, "left": left, "right": right, "line": op_tok.line}
        return left

    def _term(self) -> dict:
        left = self._unary()
        while self._check("STAR", "SLASH"):
            op_tok = self._advance()
            right  = self._unary()
            left   = {"type": "BinaryOp", "op": op_tok.value, "left": left, "right": right, "line": op_tok.line}
        return left

    def _unary(self) -> dict:
        if self._check("NOT", "MINUS"):
            op_tok = self._advance()
            operand = self._unary()
            return {"type": "UnaryOp", "op": op_tok.value, "operand": operand, "line": op_tok.line}
        return self._primary()

    def _primary(self) -> dict:
        tok = self._peek()

        if tok.type == "INT_LIT":
            self._advance()
            return {"type": "Literal", "var_type": "int", "value": tok.value, "line": tok.line}

        if tok.type == "FLOAT_LIT":
            self._advance()
            return {"type": "Literal", "var_type": "float", "value": tok.value, "line": tok.line}

        if tok.type == "IDENT":
            self._advance()
            # function call?
            if self._match("LPAREN"):
                args = self._args()
                self._expect("RPAREN")
                return {"type": "FunctionCall", "name": tok.value, "args": args, "line": tok.line}
            return {"type": "Identifier", "name": tok.value, "line": tok.line}

        if tok.type == "LPAREN":
            self._advance()
            expr = self._expr()
            self._expect("RPAREN")
            return expr

        raise ParseError(
            f"Line {tok.line}: unexpected token {tok.type!r} ({tok.value!r}) in expression"
        )

    def _args(self) -> list[dict]:
        args = []
        if not self._check("RPAREN"):
            args.append(self._expr())
            while self._match("COMMA"):
                args.append(self._expr())
        return args


# ── Standalone runner ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys, json

    if len(sys.argv) < 2:
        print("Usage: python parser.py <source.mc>")
        sys.exit(1)

    src = open(sys.argv[1]).read()
    try:
        tokens = Lexer(src).tokenize()
        tree   = Parser(tokens).parse()
        print(json.dumps(tree, indent=2))
    except (LexerError, ParseError) as e:
        print(f"Error:\n{e}", file=sys.stderr)
        sys.exit(1)
