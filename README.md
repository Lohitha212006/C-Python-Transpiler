# Mini-C → Python Compiler

A complete compiler that translates **Mini-C** source code into **Python**, built as a 3-member parallel project across 4 weeks.

## Architecture

```
.mc source
    │
    ▼
┌─────────┐     ┌──────────────────┐     ┌────────────────────┐     ┌──────────────┐
│  Lexer  │────▶│  Parser          │────▶│  Semantic Checker  │────▶│ Code Gen     │
│ lexer.py│     │ parser.py        │     │ semantic_checker.py│     │ code_gen.py  │
└─────────┘     └──────────────────┘     └────────────────────┘     └──────────────┘
  tokens         parse tree dict          annotated AST               .py output
```

## Project Files

| File | Owner | Description |
|------|-------|-------------|
| `interfaces.py` | All | Shared data structure contract |
| `lexer.py` | Member 1 | Tokenizer — source → tokens |
| `parser.py` | Member 1 | Recursive descent parser → parse tree dict |
| `grammar.txt` | Member 1 | EBNF grammar reference |
| `ast_nodes.py` | Member 2 | Dataclass definitions for every AST node |
| `ast_builder.py` | Member 2 | Parse tree dict → typed AST nodes |
| `symbol_table.py` | Member 2 | Scope-aware symbol table |
| `semantic_checker.py` | Member 2 | Type inference, scope checks, error reporting |
| `code_generator.py` | Member 3 | AST → Python source code (visitor pattern) |
| `main.py` | Member 3 | Compiler driver CLI |
| `compiler_ui.html` | Member 3 | Interactive browser UI with AST viewer |

## Installation

No dependencies beyond Python 3.9+.

```bash
git clone <repo>
cd mini_c_compiler
```

## Usage

### Compile a file
```bash
python main.py input.mc               # print to stdout
python main.py input.mc -o output.py  # write to file
```

### CLI options
```bash
python main.py --tokens input.mc      # show token stream
python main.py --parse-tree input.mc  # show parse tree JSON
python main.py --json input.mc        # full pipeline result as JSON
```

### Browser UI
Open `compiler_ui.html` in any browser. Features:
- Live Mini-C editor with line numbers
- Token visualizer (color-coded by type)
- Python output panel
- Error reporting panel
- Compilation pipeline status
- **Interactive AST Viewer** — Tree view and Graph view with pan/zoom

## Mini-C Language Reference

```c
// Variable declarations
int x = 5;
float pi = 3.14;

// Arithmetic: + - * /
int result = x * 2 + 1;

// Comparisons: == != < > <= >=
// Logic: && ||

// Functions
int add(int a, int b) {
    return a + b;
}

// If / else if / else
if (x > 0) {
    x = x - 1;
} else if (x == 0) {
    x = 1;
} else {
    x = 0;
}

// While loops
while (x < 10) {
    x = x + 1;
}
```

## Running Tests

```bash
# All test suites
python -m pytest tests/ -v

# Individual suites
python tests/test_frontend.py     # Lexer + Parser tests (Member 1)
python tests/test_semantic.py     # Semantic checker tests (Member 2)
python tests/test_integration.py  # End-to-end tests (Member 3)
```

## Known Limitations

- No arrays or pointers
- No `for` loop (use `while`)
- No `printf`/I/O built-ins (generated Python uses `print()` if patched)
- Integer division uses Python's `/` (returns float); use `//` mentally
- No `#include` or multi-file compilation

## Compilation Pipeline Phases

1. **Lexer** — tokenizes source, reports unknown characters with line numbers  
2. **Parser** — recursive descent, validates grammar, builds parse tree dict  
3. **AST Builder** — converts dict to typed Python dataclass nodes  
4. **Semantic Checker** — scope analysis, type inference, error collection  
5. **Code Generator** — visitor pattern walk, emits indented Python with type hints  

## Week 4 Integration Steps

1. Member 1 merges `member1` branch → `main`
2. Member 2 merges `member2` branch → `main`; connects real parser output to `ast_builder.py`
3. Member 3 merges `member3` branch → `main`; runs 6 test programs through `main.py`
4. All 3 members run `python tests/test_integration.py` together — all tests must pass
5. Demo: `python main.py tests/programs/06_combined.mc` (Fibonacci compiler)
