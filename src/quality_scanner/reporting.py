import json
from pathlib import Path
from datetime import UTC, datetime
from html import escape

from .models import Finding, GateResult, ScanSummary
from .scope import ScanScope


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def write_json(path: Path, data: dict) -> None:
    _atomic_write_text(
        path,
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
    )


def write_html(path: Path, title: str, body: str) -> None:
    _atomic_write_text(
        path,
        f"<html><body><h1>{escape(title)}</h1><p>{escape(body)}</p></body></html>\n",
    )


def write_json_reports(
    output_dir: Path,
    *,
    findings: tuple[Finding, ...],
    errors: tuple[str, ...],
    summary: ScanSummary,
    gate: GateResult,
    scan_scope: ScanScope,
    project_root: Path,
    config_path: Path,
    tool_version: str,
    started_at: str,
    finished_at: str,
    new_fingerprints: frozenset[str],
    baseline_file: str | None,
    baseline_fingerprint_count: int,
) -> None:
    findings_payload = []
    for finding in findings:
        payload = finding.to_dict()
        payload["baseline_status"] = (
            "NEW" if finding.fingerprint in new_fingerprints else "EXISTING"
        )
        findings_payload.append(payload)

    write_json(
        output_dir / "scan-result.json",
        {
            "summary": summary.to_dict(),
            "baseline": {
                "applied": baseline_file is not None,
                "file": baseline_file,
                "known_findings": baseline_fingerprint_count,
            },
            "findings": findings_payload,
            "errors": list(errors),
        },
    )
    write_json(
        output_dir / "scan-scope.json",
        scan_scope.to_dict(),
    )
    write_json(
        output_dir / "quality-gate.json",
        gate.to_dict(),
    )
    write_json(
        output_dir / "run-manifest.json",
        {
            "tool_name": "quality-scan-orchestrator",
            "tool_version": tool_version,
            "project_root": str(project_root),
            "config_path": str(config_path),
            "report_directory": str(output_dir),
            "started_at": started_at,
            "finished_at": finished_at,
            "baseline_file": baseline_file,
            "baseline_fingerprint_count": baseline_fingerprint_count,
        },
    )


def write_html_report(
    output_dir: Path,
    *,
    findings: tuple[Finding, ...],
    errors: tuple[str, ...],
    summary: ScanSummary,
    gate: GateResult,
    new_fingerprints: frozenset[str],
    baseline_file: str | None,
) -> None:
    finding_rows = "\n".join(
        "<tr>"
        f"<td>{'NEW' if finding.fingerprint in new_fingerprints else 'EXISTING'}</td>"
        f"<td>{escape(finding.severity.value)}</td>"
        f"<td>{escape(finding.rule_id)}</td>"
        f"<td>{escape(finding.path)}:{finding.line}</td>"
        f"<td>{escape(finding.message)}</td>"
        f"<td><code>{escape(finding.snippet)}</code></td>"
        "</tr>"
        for finding in findings
    )
    if not finding_rows:
        finding_rows = '<tr><td colspan="6">No findings</td></tr>'

    error_items = "\n".join(
        f"<li>{escape(error)}</li>"
        for error in errors
    )
    if not error_items:
        error_items = "<li>No scanner errors</li>"

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>CodeScan Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; line-height: 1.45; margin: 2rem; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 0.5rem; text-align: left; vertical-align: top; }}
    th {{ background: #f3f3f3; }}
    code {{ white-space: pre-wrap; }}
  </style>
</head>
<body>
  <h1>CodeScan Report</h1>
  <p>Status: <strong>{escape(gate.status.value)}</strong></p>
  <p>{escape(gate.reason)}</p>
  <p>Baseline: {escape(baseline_file or "not applied")}</p>
  <h2>Summary</h2>
  <ul>
    <li>Scanned files: {summary.scanned_files}</li>
    <li>Findings: {summary.findings}</li>
    <li>Errors: {summary.errors}</li>
    <li>Critical: {summary.critical_count}</li>
    <li>High: {summary.high_count}</li>
    <li>Medium: {summary.medium_count}</li>
    <li>Low: {summary.low_count}</li>
    <li>New findings: {summary.new_findings}</li>
    <li>New critical: {summary.new_critical_count}</li>
    <li>New high: {summary.new_high_count}</li>
    <li>New medium: {summary.new_medium_count}</li>
    <li>New low: {summary.new_low_count}</li>
  </ul>
  <h2>Findings</h2>
  <table>
    <thead>
      <tr><th>Status</th><th>Severity</th><th>Rule</th><th>Location</th><th>Message</th><th>Snippet</th></tr>
    </thead>
    <tbody>
      {finding_rows}
    </tbody>
  </table>
  <h2>Scanner Errors</h2>
  <ul>
    {error_items}
  </ul>
</body>
</html>
"""
    _atomic_write_text(output_dir / "codescan-report.html", html)
