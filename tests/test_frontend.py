# tests/test_frontend.py  ── Member 1
# Run with:  python -m pytest tests/test_frontend.py -v
# or:        python tests/test_frontend.py
# ─────────────────────────────────────────────────────────────────────────────

import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lexer  import Lexer, LexerError, Token
from parser import Parser, ParseError


# ═══════════════════════════════════════════════════════════════════════════════
# LEXER TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestLexerTokenTypes(unittest.TestCase):

    def _tok_types(self, src):
        return [t.type for t in Lexer(src).tokenize()]

    def test_keywords(self):
        types = self._tok_types("int float void if else while return")
        self.assertEqual(types, ["INT","FLOAT","VOID","IF","ELSE","WHILE","RETURN","EOF"])

    def test_int_literal(self):
        tokens = Lexer("42").tokenize()
        self.assertEqual(tokens[0].type, "INT_LIT")
        self.assertEqual(tokens[0].value, 42)

    def test_float_literal(self):
        tokens = Lexer("3.14").tokenize()
        self.assertEqual(tokens[0].type, "FLOAT_LIT")
        self.assertAlmostEqual(tokens[0].value, 3.14)

    def test_identifier(self):
        tokens = Lexer("myVar").tokenize()
        self.assertEqual(tokens[0].type, "IDENT")
        self.assertEqual(tokens[0].value, "myVar")

    def test_operators(self):
        src = "+ - * / = == != < > <= >= && || !"
        types = self._tok_types(src)
        expected = ["PLUS","MINUS","STAR","SLASH","ASSIGN",
                    "EQ","NEQ","LT","GT","LEQ","GEQ","AND","OR","NOT","EOF"]
        self.assertEqual(types, expected)

    def test_delimiters(self):
        types = self._tok_types("( ) { } ; ,")
        self.assertEqual(types, ["LPAREN","RPAREN","LBRACE","RBRACE","SEMICOLON","COMMA","EOF"])

    def test_line_numbers(self):
        src = "int x;\nfloat y;"
        tokens = Lexer(src).tokenize()
        # int, x, ; → line 1
        self.assertEqual(tokens[0].line, 1)
        # float → line 2
        self.assertEqual(tokens[3].line, 2)

    def test_single_line_comment_ignored(self):
        types = self._tok_types("int x; // this is a comment\nfloat y;")
        self.assertNotIn("COMMENT", types)
        self.assertEqual(types[0], "INT")

    def test_block_comment_ignored(self):
        types = self._tok_types("int /* block\ncomment */ x;")
        self.assertNotIn("MCOMMENT", types)
        self.assertEqual(types, ["INT","IDENT","SEMICOLON","EOF"])

    def test_whitespace_ignored(self):
        types = self._tok_types("   int    x   ;  ")
        self.assertEqual(types, ["INT","IDENT","SEMICOLON","EOF"])

    def test_lexer_error_unknown_char(self):
        with self.assertRaises(LexerError):
            Lexer("int x = @5;").tokenize()

    def test_empty_source(self):
        tokens = Lexer("").tokenize()
        self.assertEqual(tokens[0].type, "EOF")

    def test_keyword_not_ident(self):
        tokens = Lexer("int").tokenize()
        self.assertEqual(tokens[0].type, "INT")   # not IDENT

    def test_ident_starting_underscore(self):
        tokens = Lexer("_myVar").tokenize()
        self.assertEqual(tokens[0].type, "IDENT")


# ═══════════════════════════════════════════════════════════════════════════════
# PARSER TESTS — valid programs
# ═══════════════════════════════════════════════════════════════════════════════

def parse(src: str) -> dict:
    return Parser(Lexer(src).tokenize()).parse()


class TestParserValidPrograms(unittest.TestCase):

    def test_minimal_function(self):
        tree = parse("int main() { return 0; }")
        self.assertEqual(tree["type"], "Program")
        self.assertEqual(len(tree["functions"]), 1)
        fn = tree["functions"][0]
        self.assertEqual(fn["name"], "main")
        self.assertEqual(fn["return_type"], "int")

    def test_var_decl_no_init(self):
        tree = parse("int main() { int x; return 0; }")
        stmts = tree["functions"][0]["body"]["statements"]
        self.assertEqual(stmts[0]["type"], "VarDecl")
        self.assertIsNone(stmts[0]["value"])

    def test_var_decl_with_init(self):
        tree = parse("int main() { int x = 5; return x; }")
        decl = tree["functions"][0]["body"]["statements"][0]
        self.assertEqual(decl["type"], "VarDecl")
        self.assertEqual(decl["value"]["value"], 5)

    def test_assign_stmt(self):
        tree = parse("int main() { int x; x = 10; return x; }")
        stmts = tree["functions"][0]["body"]["statements"]
        assign = stmts[1]
        self.assertEqual(assign["type"], "AssignStmt")
        self.assertEqual(assign["name"], "x")

    def test_if_stmt(self):
        tree = parse("int main() { int x = 1; if (x > 0) { return 1; } return 0; }")
        stmts = tree["functions"][0]["body"]["statements"]
        if_stmt = stmts[1]
        self.assertEqual(if_stmt["type"], "IfStmt")
        self.assertIsNone(if_stmt["else_block"])

    def test_if_else_stmt(self):
        tree = parse("int main() { if (1 == 1) { return 1; } else { return 0; } }")
        if_stmt = tree["functions"][0]["body"]["statements"][0]
        self.assertIsNotNone(if_stmt["else_block"])

    def test_while_stmt(self):
        tree = parse("int main() { int i = 0; while (i < 10) { i = i + 1; } return i; }")
        stmts = tree["functions"][0]["body"]["statements"]
        self.assertEqual(stmts[1]["type"], "WhileStmt")

    def test_function_with_params(self):
        tree = parse("int add(int a, int b) { return a + b; }")
        fn = tree["functions"][0]
        self.assertEqual(len(fn["params"]), 2)
        self.assertEqual(fn["params"][0]["name"], "a")

    def test_function_call(self):
        tree = parse("int foo(int x) { return x; } int main() { int r = foo(3); return r; }")
        stmts = tree["functions"][1]["body"]["statements"]
        call = stmts[0]["value"]
        self.assertEqual(call["type"], "FunctionCall")
        self.assertEqual(call["name"], "foo")

    def test_binary_op_precedence(self):
        # 2 + 3 * 4  should parse as  2 + (3 * 4)
        tree = parse("int main() { int x = 2 + 3 * 4; return x; }")
        expr = tree["functions"][0]["body"]["statements"][0]["value"]
        self.assertEqual(expr["op"], "+")
        self.assertEqual(expr["right"]["op"], "*")

    def test_float_type(self):
        tree = parse("float main() { float x = 1.5; return x; }")
        fn = tree["functions"][0]
        self.assertEqual(fn["return_type"], "float")

    def test_unary_minus(self):
        tree = parse("int main() { int x = -5; return x; }")
        expr = tree["functions"][0]["body"]["statements"][0]["value"]
        self.assertEqual(expr["type"], "UnaryOp")
        self.assertEqual(expr["op"], "-")

    def test_logical_and(self):
        tree = parse("int main() { if (1 == 1 && 2 == 2) { return 1; } return 0; }")
        cond = tree["functions"][0]["body"]["statements"][0]["condition"]
        self.assertEqual(cond["op"], "&&")

    def test_multiple_functions(self):
        tree = parse("int foo() { return 1; } int bar() { return 2; }")
        self.assertEqual(len(tree["functions"]), 2)

    def test_void_function(self):
        tree = parse("void doNothing() { return; }")
        fn = tree["functions"][0]
        self.assertEqual(fn["return_type"], "void")

    def test_all_six_test_files(self):
        """Parse every .mc file in tests/programs/."""
        programs_dir = os.path.join(os.path.dirname(__file__), "programs")
        mc_files = [f for f in os.listdir(programs_dir) if f.endswith(".mc")]
        self.assertGreater(len(mc_files), 0, "No .mc test files found")
        for fname in mc_files:
            path = os.path.join(programs_dir, fname)
            with self.subTest(file=fname):
                src  = open(path).read()
                tree = parse(src)
                self.assertEqual(tree["type"], "Program")


# ═══════════════════════════════════════════════════════════════════════════════
# PARSER TESTS — invalid programs (should raise ParseError)
# ═══════════════════════════════════════════════════════════════════════════════

class TestParserErrors(unittest.TestCase):

    def _expect_error(self, src):
        with self.assertRaises((ParseError, LexerError)):
            parse(src)

    def test_missing_semicolon(self):
        self._expect_error("int main() { int x = 5 return x; }")

    def test_missing_closing_brace(self):
        self._expect_error("int main() { int x = 5;")

    def test_missing_lparen_in_if(self):
        self._expect_error("int main() { if x > 0 { return 1; } }")

    def test_empty_program(self):
        self._expect_error("")

    def test_expression_missing_operand(self):
        self._expect_error("int main() { int x = + ; return x; }")

    def test_unknown_character(self):
        self._expect_error("int main() { int x = @5; return x; }")


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    unittest.main(verbosity=2)
