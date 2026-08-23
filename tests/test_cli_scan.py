from pathlib import Path
import json
import subprocess
import tempfile
import unittest

from quality_scanner.cli import main


def _git(project_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=project_root,
        check=True,
        text=True,
        capture_output=True,
    )
    return completed.stdout.strip()


def _create_git_target_with_python_and_docs_change(root: Path) -> tuple[str, str]:
    (root / "app.py").write_text(
        "def greet(name):\n"
        "    return f'hello {name}'\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text("baseline\n", encoding="utf-8")

    _git(root, "init")
    _git(root, "config", "user.email", "codescan-test@example.test")
    _git(root, "config", "user.name", "CodeScan Test")
    _git(root, "add", "app.py", "README.md")
    _git(root, "commit", "-m", "baseline")
    baseline = _git(root, "rev-parse", "HEAD")

    (root / "app.py").write_text(
        "def greet(name):\n"
        "    return f'hi {name}'\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text("changed docs\n", encoding="utf-8")
    _git(root, "add", "app.py", "README.md")
    _git(root, "commit", "-m", "change app and docs")
    head = _git(root, "rev-parse", "HEAD")

    return baseline, head


class CliScanTests(unittest.TestCase):
    def test_scan_command_returns_success(self):
        root = (
            Path(__file__).resolve().parents[1]
            / "tests/fixtures/clean_project"
        )

        with tempfile.TemporaryDirectory() as tmp:
            result = main(
                [
                    "scan",
                    "--project",
                    str(root),
                    "--config",
                    "rules/default_rules.json",
                    "--output",
                    tmp,
                ]
            )

        self.assertEqual(0, result)

    def test_scan_command_writes_b3_report_contract_for_findings(self) -> None:
        root = (
            Path(__file__).resolve().parents[1]
            / "tests/fixtures/vulnerable_project"
        )

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            result = main(
                [
                    "scan",
                    "--project",
                    str(root),
                    "--config",
                    "rules/default_rules.json",
                    "--output",
                    str(output),
                    "--mode",
                    "FULL",
                ]
            )

            self.assertEqual(1, result)
            self.assertTrue((output / "scan-result.json").is_file())
            self.assertTrue((output / "scan-scope.json").is_file())
            self.assertTrue((output / "quality-gate.json").is_file())
            self.assertTrue((output / "codescan-report.html").is_file())
            self.assertTrue((output / "sonar-external-issues.json").is_file())
            self.assertTrue((output / "run-manifest.json").is_file())

            scan_result = json.loads(
                (output / "scan-result.json").read_text(encoding="utf-8")
            )
            self.assertEqual(6, len(scan_result["findings"]))
            self.assertEqual([], scan_result["errors"])
            self.assertEqual(
                {
                    "scanned_files": 1,
                    "findings": 6,
                    "errors": 0,
                    "critical_count": 0,
                    "high_count": 4,
                    "medium_count": 2,
                    "low_count": 0,
                },
                scan_result["summary"],
            )

            scope = json.loads(
                (output / "scan-scope.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                {
                    "requested_mode": "FULL",
                    "effective_mode": "FULL",
                    "baseline": None,
                    "head": None,
                    "changed_files": [],
                    "candidate_files": ["app.py"],
                    "selected_files": ["app.py"],
                    "fallback_reason": None,
                },
                scope,
            )

            gate = json.loads(
                (output / "quality-gate.json").read_text(encoding="utf-8")
            )
            self.assertEqual("FAIL", gate["status"])
            self.assertEqual(1, gate["exit_code"])

            html = (output / "codescan-report.html").read_text(encoding="utf-8")
            self.assertIn("QSO-PY-SEC-001", html)
            self.assertNotIn("fixture-secret-not-real", html)

    def test_scan_command_writes_error_report_for_syntax_error(self) -> None:
        root = (
            Path(__file__).resolve().parents[1]
            / "tests/fixtures/broken_project"
        )

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            result = main(
                [
                    "scan",
                    "--project",
                    str(root),
                    "--config",
                    "rules/default_rules.json",
                    "--output",
                    str(output),
                ]
            )

            self.assertEqual(3, result)

            scan_result = json.loads(
                (output / "scan-result.json").read_text(encoding="utf-8")
            )
            self.assertEqual(1, scan_result["summary"]["errors"])
            self.assertIn("broken.py: SyntaxError", scan_result["errors"][0])

            gate = json.loads(
                (output / "quality-gate.json").read_text(encoding="utf-8")
            )
            self.assertEqual("ERROR", gate["status"])
            self.assertEqual(3, gate["exit_code"])

    def test_scan_command_fast_mode_scans_changed_python_files_since_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "target"
            root.mkdir()
            baseline, head = _create_git_target_with_python_and_docs_change(root)

            output = Path(tmp) / "reports"
            result = main(
                [
                    "scan",
                    "--project",
                    str(root),
                    "--config",
                    "rules/default_rules.json",
                    "--output",
                    str(output),
                    "--mode",
                    "FAST",
                    "--baseline",
                    baseline,
                ]
            )

            self.assertEqual(0, result)

            scope = json.loads(
                (output / "scan-scope.json").read_text(encoding="utf-8")
            )
            self.assertEqual("FAST", scope["requested_mode"])
            self.assertEqual("FAST", scope["effective_mode"])
            self.assertEqual(baseline, scope["baseline"])
            self.assertEqual(head, scope["head"])
            self.assertEqual(["README.md", "app.py"], scope["changed_files"])
            self.assertEqual(["app.py"], scope["candidate_files"])
            self.assertEqual(["app.py"], scope["selected_files"])
            self.assertIsNone(scope["fallback_reason"])

            scan_result = json.loads(
                (output / "scan-result.json").read_text(encoding="utf-8")
            )
            self.assertEqual(1, scan_result["summary"]["scanned_files"])
            self.assertEqual(0, scan_result["summary"]["findings"])

    def test_scan_command_auto_mode_with_baseline_uses_fast_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "target"
            root.mkdir()
            baseline, head = _create_git_target_with_python_and_docs_change(root)

            output = Path(tmp) / "reports"
            result = main(
                [
                    "scan",
                    "--project",
                    str(root),
                    "--config",
                    "rules/default_rules.json",
                    "--output",
                    str(output),
                    "--mode",
                    "AUTO",
                    "--baseline",
                    baseline,
                ]
            )

            self.assertEqual(0, result)

            scope = json.loads(
                (output / "scan-scope.json").read_text(encoding="utf-8")
            )
            self.assertEqual("AUTO", scope["requested_mode"])
            self.assertEqual("FAST", scope["effective_mode"])
            self.assertEqual(baseline, scope["baseline"])
            self.assertEqual(head, scope["head"])
            self.assertEqual(["README.md", "app.py"], scope["changed_files"])
            self.assertEqual(["app.py"], scope["candidate_files"])
            self.assertEqual(["app.py"], scope["selected_files"])
            self.assertIsNone(scope["fallback_reason"])

    def test_scan_command_auto_mode_without_baseline_falls_back_to_full(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "target"
            root.mkdir()
            (root / "app.py").write_text("print('app')\n", encoding="utf-8")
            (root / "utils.py").write_text("print('utils')\n", encoding="utf-8")

            output = Path(tmp) / "reports"
            result = main(
                [
                    "scan",
                    "--project",
                    str(root),
                    "--config",
                    "rules/default_rules.json",
                    "--output",
                    str(output),
                    "--mode",
                    "AUTO",
                ]
            )

            self.assertEqual(0, result)

            scope = json.loads(
                (output / "scan-scope.json").read_text(encoding="utf-8")
            )
            self.assertEqual("AUTO", scope["requested_mode"])
            self.assertEqual("FULL", scope["effective_mode"])
            self.assertIsNone(scope["baseline"])
            self.assertIsNone(scope["head"])
            self.assertEqual([], scope["changed_files"])
            self.assertEqual(["app.py", "utils.py"], scope["candidate_files"])
            self.assertEqual(["app.py", "utils.py"], scope["selected_files"])
            self.assertEqual(
                "baseline not provided; falling back to FULL",
                scope["fallback_reason"],
            )

    def test_scan_command_auto_mode_with_invalid_baseline_falls_back_to_full(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "target"
            root.mkdir()
            baseline, head = _create_git_target_with_python_and_docs_change(root)

            output = Path(tmp) / "reports"
            result = main(
                [
                    "scan",
                    "--project",
                    str(root),
                    "--config",
                    "rules/default_rules.json",
                    "--output",
                    str(output),
                    "--mode",
                    "AUTO",
                    "--baseline",
                    f"{baseline}-missing",
                ]
            )

            self.assertEqual(0, result)

            scope = json.loads(
                (output / "scan-scope.json").read_text(encoding="utf-8")
            )
            self.assertEqual("AUTO", scope["requested_mode"])
            self.assertEqual("FULL", scope["effective_mode"])
            self.assertEqual(f"{baseline}-missing", scope["baseline"])
            self.assertEqual(head, scope["head"])
            self.assertEqual([], scope["changed_files"])
            self.assertEqual(["app.py"], scope["candidate_files"])
            self.assertEqual(["app.py"], scope["selected_files"])
            self.assertTrue(scope["fallback_reason"].startswith("FAST scope unavailable:"))
            self.assertIn(f"{baseline}-missing", scope["fallback_reason"])


if __name__ == "__main__":
    unittest.main()
