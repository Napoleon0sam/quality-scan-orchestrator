from pathlib import Path
from quality_scanner.config import load_config
from quality_scanner.scanner import scan_files

repository = Path(__file__).resolve().parents[1]
config = load_config(repository / "rules/default_rules.json")
project = repository / "tests/fixtures/vulnerable_project"
findings, errors = scan_files(project, ("app.py",), config)
print(f"findings={len(findings)}")
for finding in findings:
    print(f"{finding.severity.value} {finding.rule_id} {finding.path}:{finding.line}")
print(f"errors={len(errors)}")
