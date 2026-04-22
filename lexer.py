# lexer.py  ── Member 1
# Converts raw Mini-C source text into a list of tokens.
# ─────────────────────────────────────────────────────────────────────────────

import re

# ── Token types ───────────────────────────────────────────────────────────────
TT = {
    # Keywords
    "INT": "INT", "FLOAT": "FLOAT", "IF": "IF", "ELSE": "ELSE",
    "WHILE": "WHILE", "RETURN": "RETURN", "VOID": "VOID",
    # Literals
    "INT_LIT": "INT_LIT", "FLOAT_LIT": "FLOAT_LIT",
    # Identifier
    "IDENT": "IDENT",
    # Operators
    "PLUS": "PLUS", "MINUS": "MINUS", "STAR": "STAR", "SLASH": "SLASH",
    "ASSIGN": "ASSIGN",
    "EQ": "EQ", "NEQ": "NEQ",
    "LEQ": "LEQ", "GEQ": "GEQ", "LT": "LT", "GT": "GT",
    "AND": "AND", "OR": "OR", "NOT": "NOT",
    # Delimiters
    "LPAREN": "LPAREN", "RPAREN": "RPAREN",
    "LBRACE": "LBRACE", "RBRACE": "RBRACE",
    "SEMICOLON": "SEMICOLON", "COMMA": "COMMA",
    # Special
    "EOF": "EOF",
}

KEYWORDS = {"int", "float", "if", "else", "while", "return", "void"}
KEYWORD_MAP = {k: k.upper() for k in KEYWORDS}

# Token spec: list of (token_type, regex) tried in order
TOKEN_SPEC = [
    # Comments MUST come before SLASH so  /*  and  //  are never split
    ("MCOMMENT",   r'/\*.*?\*/'),
    ("COMMENT",    r'//[^\n]*'),
    ("FLOAT_LIT",  r'\d+\.\d+'),
    ("INT_LIT",    r'\d+'),
    ("IDENT",      r'[A-Za-z_][A-Za-z0-9_]*'),
    ("EQ",         r'=='),
    ("NEQ",        r'!='),
    ("LEQ",        r'<='),
    ("GEQ",        r'>='),
    ("AND",        r'&&'),
    ("OR",         r'\|\|'),
    ("LT",         r'<'),
    ("GT",         r'>'),
    ("ASSIGN",     r'='),
    ("PLUS",       r'\+'),
    ("MINUS",      r'-'),
    ("STAR",       r'\*'),
    ("SLASH",      r'/'),
    ("NOT",        r'!'),
    ("LPAREN",     r'\('),
    ("RPAREN",     r'\)'),
    ("LBRACE",     r'\{'),
    ("RBRACE",     r'\}'),
    ("SEMICOLON",  r';'),
    ("COMMA",      r','),
    ("NEWLINE",    r'\n'),
    ("SKIP",       r'[ \t\r]+'),
    ("MISMATCH",   r'.'),
]

MASTER_PATTERN = re.compile(
    '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPEC),
    re.DOTALL,
)


class LexerError(Exception):
    pass


class Token:
    __slots__ = ("type", "value", "line")

    def __init__(self, type_: str, value, line: int):
        self.type  = type_
        self.value = value
        self.line  = line

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, line={self.line})"

    def to_dict(self):
        return {"type": self.type, "value": self.value, "line": self.line}


class Lexer:
    """
    Usage:
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()   # list[Token], last token is EOF
    """

    def __init__(self, source: str):
        self.source = source
        self._errors: list[str] = []

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        line = 1

        for mo in MASTER_PATTERN.finditer(self.source):
            kind  = mo.lastgroup
            value = mo.group()

            if kind == "NEWLINE":
                line += 1
                continue
            elif kind in ("SKIP", "COMMENT", "MCOMMENT"):
                # Count newlines inside block comments
                line += value.count('\n')
                continue
            elif kind == "MISMATCH":
                self._errors.append(
                    f"Line {line}: unexpected character {value!r}"
                )
                continue
            elif kind == "FLOAT_LIT":
                tokens.append(Token("FLOAT_LIT", float(value), line))
            elif kind == "INT_LIT":
                tokens.append(Token("INT_LIT", int(value), line))
            elif kind == "IDENT":
                # Promote keywords
                tok_type = KEYWORD_MAP.get(value, "IDENT")
                tokens.append(Token(tok_type, value, line))
            else:
                tokens.append(Token(kind, value, line))

        tokens.append(Token("EOF", None, line))

        if self._errors:
            raise LexerError("\n".join(self._errors))

        return tokens


# ── Standalone runner ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys, json

    if len(sys.argv) < 2:
        print("Usage: python lexer.py <source.mc>")
        sys.exit(1)

    src = open(sys.argv[1]).read()
    try:
        tokens = Lexer(src).tokenize()
        for tok in tokens:
            print(tok)
    except LexerError as e:
        print(f"Lexer error:\n{e}", file=sys.stderr)
        sys.exit(1)
