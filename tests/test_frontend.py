"""
tests/test_frontend.py — Lexer & Parser unit tests  (Member 1)
"""
import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from lexer import tokenize, LexerError
from parser import parse, ParseError


class TestLexer(unittest.TestCase):
    def tok_types(self, src):
        return [t.type for t in tokenize(src) if t.type != 'EOF']

    def test_keywords(self):
        types = self.tok_types('int float void if else while return')
        self.assertEqual(types, ['INT','FLOAT','VOID','IF','ELSE','WHILE','RETURN'])

    def test_identifiers(self):
        types = self.tok_types('x y_1 myVar _priv')
        self.assertEqual(types, ['ID','ID','ID','ID'])

    def test_int_literal(self):
        toks = tokenize('42')
        self.assertEqual(toks[0].type, 'INT_LIT')

    def test_float_literal(self):
        toks = tokenize('3.14')
        self.assertEqual(toks[0].type, 'FLOAT_LIT')

    def test_comment_stripped(self):
        types = self.tok_types('int x; // comment\nint y;')
        self.assertNotIn('COMMENT', types)

    def test_line_numbers(self):
        toks = tokenize('int x;\nfloat y;')
        self.assertEqual(toks[0].line, 1)

    def test_invalid_char_raises(self):
        with self.assertRaises(LexerError):
            tokenize('@invalid')


class TestParser(unittest.TestCase):
    def test_var_decl(self):
        tree = parse('int x = 5;')
        d = tree['declarations'][0]
        self.assertEqual(d['type'], 'VarDecl')
        self.assertEqual(d['name'], 'x')

    def test_function_decl(self):
        tree = parse('int add(int a, int b) { return a + b; }')
        d = tree['declarations'][0]
        self.assertEqual(d['type'], 'FunctionDecl')
        self.assertEqual(len(d['params']), 2)

    def test_if_else(self):
        src = 'int main() { if (x > 0) { return 1; } else { return 0; } }'
        tree = parse(src)
        stmt = tree['declarations'][0]['body']['statements'][0]
        self.assertEqual(stmt['type'], 'IfStmt')
        self.assertIn('else', stmt)

    def test_while(self):
        src = 'int main() { while (x < 10) { x = x + 1; } return x; }'
        tree = parse(src)
        stmt = tree['declarations'][0]['body']['statements'][0]
        self.assertEqual(stmt['type'], 'WhileStmt')

    def test_parse_error(self):
        with self.assertRaises(ParseError):
            parse('int main() { int x = 5 }')

    def test_precedence(self):
        src = 'int main() { int x = 2 + 3 * 4; return x; }'
        tree = parse(src)
        expr = tree['declarations'][0]['body']['statements'][0]['value']
        self.assertEqual(expr['op'], '+')
        self.assertEqual(expr['right']['op'], '*')


if __name__ == '__main__':
    unittest.main(verbosity=2)
