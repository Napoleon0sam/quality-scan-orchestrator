import io
import unittest
from contextlib import redirect_stdout

from quality_scanner.cli import main


class CliTests(unittest.TestCase):
    def test_version_returns_zero_and_prints_version(self) -> None:
        output = io.StringIO()

        with redirect_stdout(output):
            result = main(["--version"])

        self.assertEqual(0, result)
        self.assertEqual("0.3.2\n", output.getvalue())


if __name__ == "__main__":
    unittest.main()
