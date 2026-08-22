from pathlib import Path
import tempfile
import unittest

from quality_scanner.discovery import discover_python_files


class DiscoveryTests(unittest.TestCase):
    def test_discovery_skips_runtime_cache_git_and_report_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "app.py").write_text("print('ok')\n", encoding="utf-8")

            ignored_dirs = [
                ".git",
                ".venv",
                "__pycache__",
                "reports",
            ]
            for dirname in ignored_dirs:
                ignored = root / dirname
                ignored.mkdir()
                (ignored / "ignored.py").write_text("print('ignore')\n", encoding="utf-8")

            self.assertEqual(("src/app.py",), discover_python_files(root))


if __name__ == "__main__":
    unittest.main()
