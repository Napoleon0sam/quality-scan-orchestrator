from pathlib import Path
import tempfile
import unittest

from quality_scanner.baseline import (
    Baseline,
    BaselineError,
    classify_findings,
    load_baseline,
    write_baseline,
)
from quality_scanner.models import Category, Finding, Severity


def _finding(*, rule_id: str, path: str, line: int) -> Finding:
    return Finding.create(
        rule_id=rule_id,
        category=Category.SECURITY,
        severity=Severity.HIGH,
        path=path,
        line=line,
        column=0,
        message="Avoid unsafe operation.",
        remediation="Use a safe operation.",
        snippet="unsafe_call()",
    )


class BaselineTests(unittest.TestCase):
    def test_write_and_load_baseline_keeps_fingerprints_without_snippets(self) -> None:
        finding = _finding(rule_id="QSO-PY-SEC-001", path="app.py", line=4)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "codescan-baseline.json"
            write_baseline(
                path,
                (finding,),
                generated_at="2026-08-23T00:00:00Z",
                tool_version="0.6.0",
            )

            serialized = path.read_text(encoding="utf-8")
            loaded = load_baseline(path)

        self.assertEqual(frozenset({finding.fingerprint}), loaded.fingerprints)
        self.assertNotIn("unsafe_call()", serialized)

    def test_classify_findings_marks_existing_and_new_findings(self) -> None:
        existing = _finding(rule_id="QSO-PY-SEC-001", path="app.py", line=4)
        new = _finding(rule_id="QSO-PY-SEC-002", path="app.py", line=8)

        classification = classify_findings(
            (existing, new),
            Baseline(fingerprints=frozenset({existing.fingerprint})),
        )

        self.assertEqual((existing,), classification.existing)
        self.assertEqual((new,), classification.new)

    def test_load_baseline_rejects_unknown_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "codescan-baseline.json"
            path.write_text(
                '{"schema_version": 99, "findings": []}\n',
                encoding="utf-8",
            )

            with self.assertRaises(BaselineError):
                load_baseline(path)


if __name__ == "__main__":
    unittest.main()
