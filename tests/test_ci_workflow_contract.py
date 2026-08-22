from pathlib import Path
import unittest


class CiWorkflowContractTests(unittest.TestCase):
    def test_codescan_ci_workflow_runs_tests_scan_and_uploads_reports(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        workflow = repository / ".github/workflows/codescan-ci.yml"

        self.assertTrue(workflow.is_file())

        text = workflow.read_text(encoding="utf-8")
        self.assertIn("CodeScan CI", text)
        self.assertIn("push:", text)
        self.assertIn("pull_request:", text)
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("actions/checkout@", text)
        self.assertIn("fetch-depth: 0", text)
        self.assertIn("actions/setup-python@", text)
        self.assertIn("python-version: '3.12'", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("python -m quality_scanner scan", text)
        self.assertIn("--output reports/ci_clean_full", text)
        self.assertIn("actions/upload-artifact@", text)
        self.assertIn("if: always()", text)


if __name__ == "__main__":
    unittest.main()
