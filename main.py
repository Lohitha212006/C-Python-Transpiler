"""
main.py — Mini-C Compiler Driver  (Member 3)
Chains: .mc source → Lexer → Parser → ASTBuilder → SemanticChecker → CodeGenerator → .py
"""

import sys
import json
import argparse
from pathlib import Path

from lexer import tokenize, LexerError
from parser import parse, ParseError
from ast_builder import build, ASTBuildError
from semantic_checker import analyze
from code_generator import generate, CodeGenError


def compile_source(source: str, filename: str = "<input>") -> dict:
    """
    Run the full compilation pipeline on source text.
    Returns a result dict with keys:
      tokens, parse_tree, ast, errors, python_code, success
    """
    result = {
        "filename": filename,
        "tokens": [],
        "parse_tree": None,
        "ast": None,
        "errors": [],
        "python_code": "",
        "success": False,
    }

    # Phase 1 — Lexing
    try:
        tokens = tokenize(source)
        result["tokens"] = [{"type": t.type, "value": t.value, "line": t.line} for t in tokens]
    except LexerError as e:
        result["errors"].append(f"[Lexer] {e}")
        return result

    # Phase 2 — Parsing
    try:
        parse_tree = parse(source)
        result["parse_tree"] = parse_tree
    except ParseError as e:
        result["errors"].append(f"[Parser] {e}")
        return result

    # Phase 3 — AST Construction
    try:
        ast_root = build(parse_tree)
    except ASTBuildError as e:
        result["errors"].append(f"[ASTBuilder] {e}")
        return result

    # Phase 4 — Semantic Analysis
    ast_root, semantic_errors = analyze(ast_root)
    result["ast"] = _ast_to_dict(ast_root)
    if semantic_errors:
        result["errors"].extend(f"[Semantic] {e}" for e in semantic_errors)
        # Don't stop — still try to generate code for partial programs

    # Phase 5 — Code Generation
    try:
        python_code = generate(ast_root)
        result["python_code"] = python_code
        result["success"] = len(result["errors"]) == 0
    except CodeGenError as e:
        result["errors"].append(f"[CodeGen] {e}")

    return result


def _ast_to_dict(node) -> dict:
    """Serialize AST nodes to dict for JSON output / UI consumption."""
    if node is None:
        return None
    import dataclasses
    if dataclasses.is_dataclass(node):
        d = {}
        d["_nodeType"] = type(node).__name__
        for f in dataclasses.fields(node):
            val = getattr(node, f.name)
            if isinstance(val, list):
                d[f.name] = [_ast_to_dict(v) if dataclasses.is_dataclass(v) else v for v in val]
            elif dataclasses.is_dataclass(val):
                d[f.name] = _ast_to_dict(val)
            else:
                d[f.name] = val
        return d
    return node


def main():
    parser = argparse.ArgumentParser(description="Mini-C → Python Compiler")
    parser.add_argument("input", nargs="?", help="Input .mc file (reads stdin if omitted)")
    parser.add_argument("-o", "--output", help="Output .py file")
    parser.add_argument("--json", action="store_true", help="Print full pipeline result as JSON")
    parser.add_argument("--tokens", action="store_true", help="Print tokens only")
    parser.add_argument("--parse-tree", action="store_true", help="Print parse tree only")
    args = parser.parse_args()

    if args.input:
        source = Path(args.input).read_text()
        fname = args.input
    else:
        source = sys.stdin.read()
        fname = "<stdin>"

    result = compile_source(source, fname)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
        return

    if args.tokens:
        for tok in result["tokens"]:
            print(f"  {tok['type']:15} {tok['value']!r:20} line {tok['line']}")
        return

    if args.parse_tree:
        print(json.dumps(result["parse_tree"], indent=2))
        return

    if result["errors"]:
        print("Compilation errors:", file=sys.stderr)
        for e in result["errors"]:
            print(f"  {e}", file=sys.stderr)
        if not result["python_code"]:
            sys.exit(1)

    if result["python_code"]:
        if args.output:
            Path(args.output).write_text(result["python_code"])
            print(f"Written to {args.output}")
        else:
            print(result["python_code"])


if __name__ == "__main__":
    main()
