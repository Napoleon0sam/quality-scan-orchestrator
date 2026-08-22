import unittest
from pathlib import Path
import tempfile

from quality_scanner.cli import main


class PipelineTests(unittest.TestCase):
    def test_clean_project_passes(self):
        project = (
            Path(__file__).resolve().parents[1]
            / "tests/fixtures/clean_project"
        )

        with tempfile.TemporaryDirectory() as tmp:
            result = main(
                [
                    "scan",
                    "--project",
                    str(project),
                    "--config",
                    "rules/default_rules.json",
                    "--output",
                    tmp,
                ]
            )

        self.assertEqual(0, result)


if __name__ == "__main__":
    unittest.main()
