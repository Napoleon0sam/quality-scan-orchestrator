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
- baseline support for existing findings

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

## Baseline: only block new findings

The scanner supports two different meanings of baseline:

- `--baseline`: a Git revision used by FAST or AUTO mode to find changed files
- `--baseline-file`: a JSON file of known finding fingerprints used by the quality gate

Create a findings baseline from the current scan:

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m quality_scanner scan `
  --project ".\tests\fixtures\vulnerable_project" `
  --config ".\rules\default_rules.json" `
  --output ".\reports\baseline_seed" `
  --mode FULL `
  --write-baseline ".\codescan-baseline.json"
```

The command writes the baseline even when the current findings make the gate
return exit code `1`. That is intentional: this is a one-time maintenance
operation that records the current technical debt.

Use the baseline on later scans:

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m quality_scanner scan `
  --project ".\tests\fixtures\vulnerable_project" `
  --config ".\rules\default_rules.json" `
  --output ".\reports\with_baseline" `
  --mode FULL `
  --baseline-file ".\codescan-baseline.json"
```

Existing findings remain visible in the reports but are marked `EXISTING` and
do not fail the gate. A finding whose fingerprint is not in the file is marked
`NEW`; a new HIGH or CRITICAL finding fails the gate. The JSON and HTML reports
also include `new_findings` and severity-specific `new_*` counters.

The baseline stores fingerprints and location metadata, but not source
snippets. The current fingerprint includes rule ID, path, line, and message;
moving an issue to another line can therefore make it appear as a new finding.
That is a known limitation to address when improving issue tracking.

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

The repository currently demonstrates baseline behavior locally through the
CLI. The CI example still scans a clean fixture and does not yet apply a
repository-specific `--baseline-file`; connecting that baseline to the real CI
target is the next operational step.

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
