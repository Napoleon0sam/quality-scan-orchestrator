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
- SonarQube Cloud CI analysis wiring
- SonarQube generic external issues export

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
- `sonar-external-issues.json`
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
uploads the generated reports as a GitHub Actions artifact, and then runs
SonarQube Cloud analysis.

For learning checkpoints, each trigger should be backed by its run URL and the
uploaded `codescan-reports` artifact.

## SonarQube Cloud

This project uses SonarQube Cloud as an external quality platform. It does not
self-host SonarQube Server.

The repository stores only non-sensitive SonarQube project metadata in:

```text
sonar-project.properties
```

The authentication token must be stored as a GitHub Actions repository secret:

```text
SONAR_TOKEN
```

Do not commit SonarQube tokens to this repository.

The GitHub Actions workflow waits for the SonarQube Cloud Quality Gate result:

```text
sonar.externalIssuesReportPaths=reports/ci_target_full/sonar-external-issues.json
sonar.python.coverage.reportPaths=coverage.xml
sonar.qualitygate.wait=true
```

If the Sonar Quality Gate fails or times out, the SonarQube scan step fails the
workflow. This is separate from GitHub branch protection, which must be enabled
in repository settings before failed checks can block merges.

SonarQube Cloud does not create Python coverage by itself. The CI workflow runs
unit tests through Coverage.py, writes `coverage.xml`, and then SonarQube Cloud
imports that file during analysis.

The workflow lets the CodeScan step continue long enough for SonarQube Cloud to
import `sonar-external-issues.json`, then enforces the CodeScan result in a
separate step. This keeps the native CodeScan gate meaningful while still
allowing SonarQube Cloud to act as the shared quality dashboard.

The CI CodeScan command passes `--sonar-base-dir .` so external issue file paths
are written relative to the same repository root used by SonarQube Cloud
analysis.

The workflow runs on pull requests and on pushes to `main`; feature branch
pushes should be validated through a pull request.

Recommended GitHub repository:

```text
https://github.com/Napoleon0sam/quality-scan-orchestrator
```
