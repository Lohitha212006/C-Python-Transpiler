"""
tests/test_semantic.py — Semantic checker unit tests  (Member 2)
"""
import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from parser import parse
from ast_builder import build
from semantic_checker import analyze


def check(src):
    tree = parse(src)
    ast = build(tree)
    _, errors = analyze(ast)
    return errors


class TestSemanticChecker(unittest.TestCase):
    def test_valid_program_no_errors(self):
        errs = check('int add(int a, int b) { return a + b; } int main() { int x = add(1,2); return x; }')
        self.assertEqual(errs, [])

    def test_undeclared_variable(self):
        errs = check('int main() { y = 5; return y; }')
        self.assertTrue(any('undeclared' in e.lower() for e in errs))

    def test_redeclaration_same_scope(self):
        errs = check('int main() { int x = 1; int x = 2; return x; }')
        self.assertTrue(any('already declared' in e for e in errs))

    def test_wrong_arg_count(self):
        errs = check('int add(int a, int b) { return a+b; } int main() { return add(1); }')
        self.assertTrue(any('expects' in e for e in errs))

    def test_recursive_function_allowed(self):
        errs = check('int fib(int n) { if (n <= 1) { return n; } return fib(n - 1); }')
        self.assertEqual(errs, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
