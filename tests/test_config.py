import json
from pathlib import Path
import tempfile
import unittest

from quality_scanner.config import ConfigError, load_config

REPOSITORY = Path(__file__).resolve().parents[1]

class ConfigTests(unittest.TestCase):
    def test_loads_valid_default_config(self) -> None:
        config = load_config(REPOSITORY / "rules/default_rules.json")
        self.assertEqual(5, len(config.rules))
        self.assertEqual(20, config.function_length_limit)

    def test_rejects_duplicate_rule_ids(self) -> None:
        payload = {
            "function_length_limit": 20,
            "rules": [
                {"id":"X","category":"Security","severity":"HIGH","message":"m","remediation":"r"},
                {"id":"X","category":"Security","severity":"HIGH","message":"m","remediation":"r"},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rules.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(ConfigError):
                load_config(path)

if __name__ == "__main__":
    unittest.main()
