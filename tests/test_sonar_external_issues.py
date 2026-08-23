from pathlib import Path
import json
import tempfile
import unittest

from quality_scanner.cli import main


REPOSITORY = Path(__file__).resolve().parents[1]


class SonarExternalIssuesTests(unittest.TestCase):
    def test_scan_writes_sonar_external_issues_report(self) -> None:
        project = REPOSITORY / "tests/fixtures/vulnerable_project"

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            result = main(
                [
                    "scan",
                    "--project",
                    str(project),
                    "--config",
                    "rules/default_rules.json",
                    "--output",
                    str(output),
                    "--mode",
                    "FULL",
                ]
            )

            self.assertEqual(1, result)
            report = json.loads(
                (output / "sonar-external-issues.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual({"rules", "issues"}, set(report))
        self.assertEqual(5, len(report["rules"]))
        self.assertEqual(6, len(report["issues"]))

        eval_rule = next(
            rule for rule in report["rules"]
            if rule["id"] == "QSO-PY-SEC-001"
        )
        self.assertEqual("codescan", eval_rule["engineId"])
        self.assertEqual("Avoid eval or exec.", eval_rule["name"])
        self.assertEqual("TRUSTWORTHY", eval_rule["cleanCodeAttribute"])
        self.assertEqual(
            [{"softwareQuality": "SECURITY", "severity": "HIGH"}],
            eval_rule["impacts"],
        )

        eval_issue = next(
            issue for issue in report["issues"]
            if issue["ruleId"] == "QSO-PY-SEC-001"
        )
        self.assertEqual(0, eval_issue["effortMinutes"])
        self.assertEqual(
            {
                "message": (
                    "Avoid eval or exec. "
                    "Remediation: Use explicit parsing or a constrained dispatcher."
                ),
                "filePath": "app.py",
                "textRange": {"startLine": 7},
            },
            eval_issue["primaryLocation"],
        )

    def test_scan_writes_empty_sonar_external_issues_report_when_clean(self) -> None:
        project = REPOSITORY / "tests/fixtures/clean_project"

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            result = main(
                [
                    "scan",
                    "--project",
                    str(project),
                    "--config",
                    "rules/default_rules.json",
                    "--output",
                    str(output),
                    "--mode",
                    "FULL",
                ]
            )

            self.assertEqual(0, result)
            report = json.loads(
                (output / "sonar-external-issues.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(5, len(report["rules"]))
        self.assertEqual([], report["issues"])

    def test_scan_can_write_sonar_file_paths_relative_to_analysis_base(self) -> None:
        project = REPOSITORY / "tests/fixtures/vulnerable_project"

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            result = main(
                [
                    "scan",
                    "--project",
                    str(project),
                    "--config",
                    "rules/default_rules.json",
                    "--output",
                    str(output),
                    "--mode",
                    "FULL",
                    "--sonar-base-dir",
                    str(REPOSITORY),
                ]
            )

            self.assertEqual(1, result)
            report = json.loads(
                (output / "sonar-external-issues.json").read_text(
                    encoding="utf-8"
                )
            )

        file_paths = {
            issue["primaryLocation"]["filePath"]
            for issue in report["issues"]
        }
        self.assertEqual(
            {"tests/fixtures/vulnerable_project/app.py"},
            file_paths,
        )


if __name__ == "__main__":
    unittest.main()
