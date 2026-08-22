# quality-scan-orchestrator

Learning-oriented research and development quality automation tool.

This project demonstrates a small but complete Python code scanning pipeline:

- Python AST based native scanner
- configurable rule metadata
- stable finding schema
- quality gate exit codes
- FULL / FAST / AUTO scan scope
- JSON and HTML reports
- GitHub Actions CI workflow

## Local Commands

Run tests:

```powershell
cd "C:\Users\Work\Downloads\CodeScan學習\quality-scan-orchestrator"
$env:PYTHONPATH = "$PWD\src"
python -m unittest discover -s tests -v
```

Run a clean FULL scan:

```powershell
cd "C:\Users\Work\Downloads\CodeScan學習\quality-scan-orchestrator"
$env:PYTHONPATH = "$PWD\src"
python -m quality_scanner scan `
  --project ".\tests\fixtures\clean_project" `
  --config ".\rules\default_rules.json" `
  --output ".\reports\ci_clean_full" `
  --mode FULL
```

Run AUTO mode with fallback:

```powershell
cd "C:\Users\Work\Downloads\CodeScan學習\quality-scan-orchestrator"
$env:PYTHONPATH = "$PWD\src"
python -m quality_scanner scan `
  --project ".\tests\fixtures\clean_project" `
  --config ".\rules\default_rules.json" `
  --output ".\reports\ci_auto_full" `
  --mode AUTO
```

## Report Files

Each scan writes:

- `scan-result.json`
- `scan-scope.json`
- `quality-gate.json`
- `codescan-report.html`
- `run-manifest.json`

## Exit Codes

- `0`: scan passed
- `1`: quality gate failed because a blocking finding exists
- `2`: command usage error
- `3`: scanner or scope error

## CI

GitHub Actions workflow:

```text
.github/workflows/codescan-ci.yml
```

The workflow runs on:

- push
- pull request
- manual workflow dispatch

It compiles Python files, runs unit tests, runs CodeScan on a clean fixture,
and uploads the generated reports as a GitHub Actions artifact.

Recommended GitHub repository:

```text
https://github.com/Napoleon0sam/quality-scan-orchestrator
```
