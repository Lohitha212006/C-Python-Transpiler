"""
tests/test_integration.py — End-to-end integration tests  (Member 3)
Runs all 6 .mc programs through the full pipeline and validates output.
Cross-platform: works on Windows, Linux, and Mac.
"""
import sys, os, subprocess, unittest, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from main import compile_source

PROGRAMS_DIR = os.path.join(os.path.dirname(__file__), 'programs')

def read_mc(name):
    with open(os.path.join(PROGRAMS_DIR, name)) as f:
        return f.read()

class TestIntegration(unittest.TestCase):

    def _compile_ok(self, src):
        r = compile_source(src)
        self.assertTrue(r['python_code'], "No Python output")
        return r

    def test_01_arithmetic(self):
        r = self._compile_ok(read_mc('01_arithmetic.mc'))
        self.assertIn('def main', r['python_code'])
        self.assertIn('a + b', r['python_code'])

    def test_02_if_else(self):
        r = self._compile_ok(read_mc('02_if_else.mc'))
        self.assertIn('if x < 0', r['python_code'])
        self.assertIn('else:', r['python_code'])

    def test_03_while_loop(self):
        r = self._compile_ok(read_mc('03_while_loop.mc'))
        self.assertIn('while', r['python_code'])

    def test_04_functions(self):
        r = self._compile_ok(read_mc('04_functions.mc'))
        self.assertIn('def add', r['python_code'])
        self.assertIn('def multiply', r['python_code'])

    def test_05_nested_scopes(self):
        r = self._compile_ok(read_mc('05_nested_scopes.mc'))
        self.assertIn('while', r['python_code'])
        self.assertIn('result', r['python_code'])

    def test_06_fibonacci(self):
        r = self._compile_ok(read_mc('06_combined.mc'))
        self.assertIn('def fib', r['python_code'])
        self.assertIn('if __name__', r['python_code'])

    def test_generated_fibonacci_runs(self):
        """Compile fib.mc, run it, check output — works on Windows/Linux/Mac."""
        r = self._compile_ok(read_mc('06_combined.mc'))
        # Patch main() to print its return value so we can capture it
        code = r['python_code'].replace(
            'if __name__ == "__main__":\n    main()',
            'if __name__ == "__main__":\n    print(main())'
        )
        # mkstemp: creates + opens file, returns (fd, path)
        # We close fd immediately so Windows can open the file again via subprocess
        fd, tmp = tempfile.mkstemp(suffix='.py')
        try:
            os.write(fd, code.encode('utf-8'))  # write via fd (no separate open needed)
            os.close(fd)                         # MUST close before subprocess on Windows
            out = subprocess.check_output(
                [sys.executable, tmp], text=True
            ).strip()
            self.assertEqual(out, '21')          # fib(8) = 21
        finally:
            os.unlink(tmp)                       # always delete temp file

    def test_semantic_error_detected(self):
        src = """
int main() {
    int x = 5;
    int x = 10;
    return x;
}"""
        r = compile_source(src)
        self.assertTrue(any('already declared' in e for e in r['errors']))

    def test_undeclared_variable_detected(self):
        src = """
int main() {
    y = 5;
    return y;
}"""
        r = compile_source(src)
        self.assertTrue(any('undeclared' in e.lower() for e in r['errors']))

    def test_wrong_arg_count_detected(self):
        src = """
int add(int a, int b) { return a + b; }
int main() { return add(1); }"""
        r = compile_source(src)
        self.assertTrue(any('expects' in e for e in r['errors']))


if __name__ == '__main__':
    unittest.main(verbosity=2)
