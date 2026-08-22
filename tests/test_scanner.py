from pathlib import Path
import unittest

from quality_scanner.config import load_config
from quality_scanner.scanner import scan_files

REPOSITORY = Path(__file__).resolve().parents[1]
CONFIG = load_config(REPOSITORY / "rules/default_rules.json")

class ScannerTests(unittest.TestCase):
    def test_vulnerable_fixture_finds_all_rule_types(self) -> None:
        root = REPOSITORY / "tests/fixtures/vulnerable_project"
        findings, errors = scan_files(root, ("app.py",), CONFIG)
        self.assertEqual((), errors)
        self.assertEqual(
            {"QSO-PY-SEC-001","QSO-PY-SEC-002","QSO-PY-SEC-003","QSO-PY-REL-001","QSO-PY-MNT-001"},
            {finding.rule_id for finding in findings},
        )
        self.assertNotIn("fixture-secret-not-real", "\n".join(f.snippet for f in findings))

    def test_clean_fixture_has_no_findings(self) -> None:
        root = REPOSITORY / "tests/fixtures/clean_project"
        findings, errors = scan_files(root, ("app.py",), CONFIG)
        self.assertEqual((), findings)
        self.assertEqual((), errors)

    def test_syntax_error_is_reported_and_other_file_continues(self) -> None:
        root = REPOSITORY / "tests/fixtures/broken_project"
        findings, errors = scan_files(root, ("broken.py", "clean.py"), CONFIG)
        self.assertEqual((), findings)
        self.assertEqual(1, len(errors))
        self.assertIn("broken.py: SyntaxError", errors[0])

if __name__ == "__main__":
    unittest.main()
