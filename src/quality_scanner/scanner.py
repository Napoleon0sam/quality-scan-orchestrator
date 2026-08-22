import ast
from pathlib import Path
import re

from .config import ScanConfig
from .models import Finding


_SECRET_NAME = re.compile(r"(?i)(password|passwd|secret|token|api_?key)")


def _dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _target_names(node: ast.AST) -> tuple[str, ...]:
    if isinstance(node, ast.Name):
        return (node.id,)
    if isinstance(node, (ast.Tuple, ast.List)):
        names: list[str] = []
        for child in node.elts:
            names.extend(_target_names(child))
        return tuple(names)
    return ()


class RuleVisitor(ast.NodeVisitor):
    def __init__(self, relative_path: str, source: str, config: ScanConfig) -> None:
        self.relative_path = relative_path
        self.source = source
        self.rules = config.by_id()
        self.function_length_limit = config.function_length_limit
        self.findings: list[Finding] = []

    def _snippet(self, node: ast.AST) -> str:
        segment = ast.get_source_segment(self.source, node)
        return segment.strip() if segment else ""

    def _add(self, rule_id: str, node: ast.AST) -> None:
        rule = self.rules[rule_id]
        self.findings.append(
            Finding.create(
                rule_id=rule.id,
                category=rule.category,
                severity=rule.severity,
                path=self.relative_path,
                line=getattr(node, "lineno", 1),
                column=getattr(node, "col_offset", 0),
                message=rule.message,
                remediation=rule.remediation,
                snippet=self._snippet(node),
            )
        )

    def visit_Call(self, node: ast.Call) -> None:
        name = _dotted_name(node.func)
        if name in {"eval", "exec"}:
            self._add("QSO-PY-SEC-001", node)
        elif name == "os.system":
            self._add("QSO-PY-SEC-002", node)
        elif name in {"subprocess.run", "subprocess.call", "subprocess.Popen"}:
            shell_true = any(
                keyword.arg == "shell"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is True
                for keyword in node.keywords
            )
            if shell_true:
                self._add("QSO-PY-SEC-002", node)
        self.generic_visit(node)

    def _check_secret(self, target: ast.AST, value: ast.AST, node: ast.AST) -> None:
        if (
            not isinstance(value, ast.Constant)
            or not isinstance(value.value, str)
            or not value.value
        ):
            return
        if any(_SECRET_NAME.search(name) for name in _target_names(target)):
            self._add("QSO-PY-SEC-003", node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self._check_secret(target, node.value, node)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value is not None:
            self._check_secret(node.target, node.value, node)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.type is None:
            self._add("QSO-PY-REL-001", node)
        self.generic_visit(node)

    def _check_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        end_line = node.end_lineno if node.end_lineno is not None else node.lineno
        if end_line - node.lineno + 1 > self.function_length_limit:
            self._add("QSO-PY-MNT-001", node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_function(node)
        self.generic_visit(node)


def scan_file(
    project_root: Path,
    relative_path: str,
    config: ScanConfig,
) -> tuple[Finding, ...]:
    root = project_root.resolve()
    path = (root / relative_path).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Path escapes project root: {relative_path}") from exc

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=relative_path)
    visitor = RuleVisitor(relative_path, source, config)
    visitor.visit(tree)
    return tuple(
        sorted(
            visitor.findings,
            key=lambda item: (item.path, item.line, item.column, item.rule_id),
        )
    )


def scan_files(
    project_root: Path,
    relative_paths: tuple[str, ...],
    config: ScanConfig,
) -> tuple[tuple[Finding, ...], tuple[str, ...]]:
    findings: list[Finding] = []
    errors: list[str] = []

    for relative_path in relative_paths:
        try:
            findings.extend(scan_file(project_root, relative_path, config))
        except (SyntaxError, UnicodeDecodeError, OSError, ValueError) as exc:
            errors.append(f"{relative_path}: {type(exc).__name__}: {exc}")

    return (
        tuple(
            sorted(
                findings,
                key=lambda item: (item.path, item.line, item.column, item.rule_id),
            )
        ),
        tuple(sorted(errors)),
    )
