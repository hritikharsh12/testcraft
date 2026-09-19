import ast
from pathlib import Path

from app.models.schemas import ClassInfo, FunctionInfo, ParsedSummary

_EXTENSION_TO_LANGUAGE = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".java": "java",
    ".go": "go",
}


def detect_language(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    return _EXTENSION_TO_LANGUAGE.get(ext, "unknown")


def parse_code(filename: str, source_code: str) -> ParsedSummary:
    """
    Deep (AST-based) parsing for Python, since that's this project's primary
    target. Other languages get a lighter line/import-count pass — a real
    system would slot in tree-sitter grammars here without changing the
    ParsedSummary contract downstream (RAG + prompt building don't care
    which parser produced it).
    """
    language = detect_language(filename)
    line_count = len(source_code.splitlines())

    if language == "python":
        return _parse_python(source_code, line_count)

    return ParsedSummary(
        language=language,
        line_count=line_count,
        functions=[],
        classes=[],
        imports=[],
        warnings=[f"Deep parsing not yet implemented for '{language}'; only line count computed."],
    )


def _parse_python(source_code: str, line_count: int) -> ParsedSummary:
    warnings: list[str] = []
    try:
        tree = ast.parse(source_code)
    except SyntaxError as exc:
        return ParsedSummary(
            language="python",
            line_count=line_count,
            functions=[],
            classes=[],
            imports=[],
            warnings=[f"Syntax error at line {exc.lineno}: {exc.msg}"],
        )

    functions: list[FunctionInfo] = []
    classes: list[ClassInfo] = []
    imports: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(
                FunctionInfo(
                    name=node.name,
                    line_number=node.lineno,
                    args=[a.arg for a in node.args.args],
                    has_docstring=ast.get_docstring(node) is not None,
                    is_async=isinstance(node, ast.AsyncFunctionDef),
                )
            )
        elif isinstance(node, ast.ClassDef):
            methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            classes.append(ClassInfo(name=node.name, line_number=node.lineno, methods=methods))
        elif isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)

    undocumented = [f.name for f in functions if not f.has_docstring]
    if undocumented:
        warnings.append(f"{len(undocumented)} function(s) missing docstrings: {', '.join(undocumented[:5])}")
    if not functions and not classes:
        warnings.append("No functions or classes found — nothing testable was detected.")

    return ParsedSummary(
        language="python",
        line_count=line_count,
        functions=functions,
        classes=classes,
        imports=sorted(set(imports)),
        warnings=warnings,
    )
