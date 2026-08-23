from pathlib import Path
import unittest


class CiWorkflowContractTests(unittest.TestCase):
    def test_codescan_ci_workflow_runs_tests_scan_and_uploads_reports(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        workflow = repository / ".github/workflows/codescan-ci.yml"
        ci_target = repository / "tests/fixtures/ci_target_project/app.py"

        self.assertTrue(workflow.is_file())
        self.assertTrue(ci_target.is_file())

        text = workflow.read_text(encoding="utf-8")
        self.assertIn("CodeScan CI", text)
        self.assertIn("push:", text)
        self.assertIn("  push:\n    branches:\n      - main", text)
        self.assertIn("pull_request:", text)
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("actions/checkout@", text)
        self.assertIn("fetch-depth: 0", text)
        self.assertIn("actions/setup-python@", text)
        self.assertIn("python-version: '3.12'", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("python -m quality_scanner scan", text)
        self.assertIn("--project tests/fixtures/ci_target_project", text)
        self.assertIn("--output reports/ci_target_full", text)
        self.assertIn("--sonar-base-dir .", text)
        self.assertIn("actions/upload-artifact@", text)
        self.assertIn("if: always()", text)

    def test_codescan_ci_workflow_runs_sonarqube_cloud_scan(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        workflow = repository / ".github/workflows/codescan-ci.yml"
        sonar_properties = repository / "sonar-project.properties"

        self.assertTrue(workflow.is_file())
        self.assertTrue(sonar_properties.is_file())

        workflow_text = workflow.read_text(encoding="utf-8")
        self.assertIn("id: codescan", workflow_text)
        self.assertIn("continue-on-error: true", workflow_text)
        self.assertIn("Run SonarQube Cloud scan", workflow_text)
        self.assertIn("SonarSource/sonarqube-scan-action@", workflow_text)
        self.assertIn("args: >", workflow_text)
        self.assertIn(
            "-Dsonar.externalIssuesReportPaths=reports/ci_target_full/sonar-external-issues.json",
            workflow_text,
        )
        self.assertIn("-Dsonar.qualitygate.wait=true", workflow_text)
        self.assertIn("-Dsonar.qualitygate.timeout=300", workflow_text)
        self.assertIn("SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}", workflow_text)
        self.assertIn("Enforce CodeScan quality gate", workflow_text)
        self.assertIn("steps.codescan.outcome == 'failure'", workflow_text)

        properties = sonar_properties.read_text(encoding="utf-8")
        self.assertIn("sonar.organization=napoleon0sam", properties)
        self.assertIn(
            "sonar.projectKey=Napoleon0sam_quality-scan-orchestrator",
            properties,
        )
        self.assertIn("sonar.sources=src,scripts", properties)
        self.assertIn("sonar.tests=tests", properties)
        self.assertIn("sonar.python.version=3.12", properties)


if __name__ == "__main__":
    unittest.main()
