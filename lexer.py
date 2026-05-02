"""
lexer.py — Mini-C Lexer  (Member 1)
Tokenizes Mini-C source into a list of (type, value, line) tuples.
"""

import re
from dataclasses import dataclass
from typing import List

# ── Token types ──────────────────────────────────────────────────────────────
KEYWORDS = {
    "int", "float", "void", "if", "else", "while", "return",
    "true", "false",
}

TOKEN_SPEC = [
    ("MCOMMENT",   r"/\*[\s\S]*?\*/"),   # /* ... */  MUST be before SLASH
    ("COMMENT",    r"//[^\n]*"),          # // ...     MUST be before SLASH
    ("FLOAT_LIT",  r"\d+\.\d+"),
    ("INT_LIT",    r"\d+"),
    ("STRING_LIT", r'"[^"]*"'),
    ("ID",         r"[A-Za-z_]\w*"),
    ("LBRACE",     r"\{"),
    ("RBRACE",     r"\}"),
    ("LPAREN",     r"\("),
    ("RPAREN",     r"\)"),
    ("SEMICOLON",  r";"),
    ("COMMA",      r","),
    ("EQ",         r"=="),
    ("NEQ",        r"!="),
    ("LEQ",        r"<="),
    ("GEQ",        r">="),
    ("LT",         r"<"),
    ("GT",         r">"),
    ("ASSIGN",     r"="),
    ("PLUS",       r"\+"),
    ("MINUS",      r"-"),
    ("STAR",       r"\*"),
    ("SLASH",      r"/"),
    ("AND",        r"&&"),
    ("OR",         r"\|\|"),
    ("NOT",        r"!"),
    ("NEWLINE",    r"\n"),
    ("SKIP",       r"[ \t]+"),
    ("MISMATCH",   r"."),
]

MASTER_RE = re.compile(
    "|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC)
)


@dataclass
class Token:
    type: str
    value: str
    line: int

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, line={self.line})"


class LexerError(Exception):
    pass


def tokenize(source: str) -> List[Token]:
    tokens: List[Token] = []
    line = 1
    for mo in MASTER_RE.finditer(source):
        kind = mo.lastgroup
        value = mo.group()
        if kind in ("NEWLINE",):
            line += 1
        elif kind in ("SKIP", "COMMENT", "MCOMMENT"):
            line += value.count("\n")
        elif kind == "MISMATCH":
            raise LexerError(f"Unexpected character {value!r} at line {line}")
        else:
            if kind == "ID" and value in KEYWORDS:
                kind = value.upper()   # e.g. "int" → "INT"
            tokens.append(Token(kind, value, line))
    tokens.append(Token("EOF", "", line))
    return tokens


if __name__ == "__main__":
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
    for tok in tokenize(src):
        print(tok)
