import argparse
from pathlib import Path
import subprocess
import sys

from . import __version__
from .baseline import (
    BaselineError,
    classify_findings,
    load_baseline,
    write_baseline,
)
from .config import load_config
from .discovery import discover_python_files
from .models import ScanSummary
from .quality_gate import evaluate
from .reporting import utc_now, write_html_report, write_json_reports
from .scanner import scan_files
from .sonar_external import write_sonar_external_issues_report
from .scope import ScanMode, select_scope


class GitScopeError(RuntimeError):
    pass


def _git_stdout(project_root: Path, args: list[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=project_root,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip()
        raise GitScopeError(" ".join(message.split()))
    return completed.stdout.strip()


def _git_head(project_root: Path) -> str:
    return _git_stdout(project_root, ["rev-parse", "HEAD"])


def _git_changed_files(
    project_root: Path,
    *,
    baseline: str,
    head: str,
) -> tuple[str, ...]:
    try:
        output = _git_stdout(
            project_root,
            [
                "diff",
                "--name-only",
                "--diff-filter=ACMR",
                f"{baseline}...{head}",
            ],
        )
    except GitScopeError as exc:
        raise GitScopeError(f"git diff failed for baseline {baseline!r}") from exc
    return tuple(
        sorted(
            line.strip().replace("\\", "/")
            for line in output.splitlines()
            if line.strip()
        )
    )


def _scan(args: argparse.Namespace) -> int:
    started_at = utc_now()
    project = Path(args.project).resolve()
    config_path = Path(args.config).resolve()
    sonar_base_dir = (
        Path(args.sonar_base_dir).resolve()
        if args.sonar_base_dir
        else project
    )
    baseline_file = (
        Path(args.baseline_file).resolve()
        if args.baseline_file
        else None
    )
    finding_baseline = None
    if baseline_file is not None:
        try:
            finding_baseline = load_baseline(baseline_file)
        except BaselineError as exc:
            print(f"Baseline error: {exc}", file=sys.stderr)
            return 3

    config = load_config(config_path)

    candidate_files = discover_python_files(project)
    requested_mode = ScanMode(args.mode)
    baseline = None
    head = None
    changed_files: tuple[str, ...] = ()
    fallback_reason = None

    if requested_mode in {ScanMode.FAST, ScanMode.AUTO}:
        if not args.baseline:
            if requested_mode is ScanMode.FAST:
                print("FAST scan mode requires --baseline.", file=sys.stderr)
                return 2
            fallback_reason = "baseline not provided; falling back to FULL"
        else:
            baseline = args.baseline
            try:
                head = _git_head(project)
                changed_files = _git_changed_files(
                    project,
                    baseline=baseline,
                    head=head,
                )
            except GitScopeError as exc:
                if requested_mode is ScanMode.FAST:
                    print(f"Git scope error: {exc}", file=sys.stderr)
                    return 3
                fallback_reason = f"FAST scope unavailable: {exc}; falling back to FULL"

    scan_scope = select_scope(
        requested_mode=requested_mode,
        baseline=baseline,
        head=head,
        changed_files=changed_files,
        fallback_reason=fallback_reason,
        candidate_files=candidate_files,
    )

    findings, errors = scan_files(
        project,
        scan_scope.selected_files,
        config,
    )
    classification = classify_findings(findings, finding_baseline)

    high_count = sum(
        1 for finding in findings
        if finding.severity.value == "HIGH"
    )

    critical_count = sum(
        1 for finding in findings
        if finding.severity.value == "CRITICAL"
    )

    medium_count = sum(
        1 for finding in findings
        if finding.severity.value == "MEDIUM"
    )

    low_count = sum(
        1 for finding in findings
        if finding.severity.value == "LOW"
    )

    new_high_count = sum(
        1 for finding in classification.new
        if finding.severity.value == "HIGH"
    )

    new_critical_count = sum(
        1 for finding in classification.new
        if finding.severity.value == "CRITICAL"
    )

    new_medium_count = sum(
        1 for finding in classification.new
        if finding.severity.value == "MEDIUM"
    )

    new_low_count = sum(
        1 for finding in classification.new
        if finding.severity.value == "LOW"
    )

    summary = ScanSummary(
        scanned_files=len(scan_scope.selected_files),
        findings=len(findings),
        errors=len(errors),
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        new_findings=len(classification.new),
        new_critical_count=new_critical_count,
        new_high_count=new_high_count,
        new_medium_count=new_medium_count,
        new_low_count=new_low_count,
    )

    gate = evaluate(
        summary,
        baseline_applied=finding_baseline is not None,
    )

    output = Path(args.output)
    finished_at = utc_now()
    write_baseline_path = (
        Path(args.write_baseline).resolve()
        if args.write_baseline
        else None
    )
    if write_baseline_path is not None and not errors:
        try:
            write_baseline(
                write_baseline_path,
                findings,
                generated_at=finished_at,
                tool_version=__version__,
            )
        except OSError as exc:
            print(f"Could not write baseline: {exc}", file=sys.stderr)
            return 3

    write_json_reports(
        output,
        findings=findings,
        errors=errors,
        summary=summary,
        gate=gate,
        scan_scope=scan_scope,
        project_root=project,
        config_path=config_path,
        tool_version=__version__,
        started_at=started_at,
        finished_at=finished_at,
        new_fingerprints=frozenset(
            finding.fingerprint for finding in classification.new
        ),
        baseline_file=(str(baseline_file) if baseline_file is not None else None),
        baseline_fingerprint_count=(
            len(finding_baseline.fingerprints)
            if finding_baseline is not None
            else 0
        ),
    )
    write_html_report(
        output,
        findings=findings,
        errors=errors,
        summary=summary,
        gate=gate,
        new_fingerprints=frozenset(
            finding.fingerprint for finding in classification.new
        ),
        baseline_file=(str(baseline_file) if baseline_file is not None else None),
    )
    write_sonar_external_issues_report(
        output,
        findings=findings,
        config=config,
        project_root=project,
        sonar_base_dir=sonar_base_dir,
    )

    print(f"Status: {gate.status.value}")
    print(f"Scanned files: {summary.scanned_files}")
    print(f"Findings: {summary.findings}")
    print(f"New findings: {summary.new_findings}")
    if write_baseline_path is not None:
        print(f"Baseline file: {write_baseline_path}")
    print(f"Report directory: {output}")

    return gate.exit_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="quality-scanner"
    )

    parser.add_argument(
        "--version",
        action="store_true",
    )

    subparsers = parser.add_subparsers(
        dest="command"
    )

    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan a Python project.",
    )

    scan_parser.add_argument(
        "--project",
        required=True,
    )

    scan_parser.add_argument(
        "--config",
        default="rules/default_rules.json",
    )

    scan_parser.add_argument(
        "--output",
        default="reports",
    )

    scan_parser.add_argument(
        "--sonar-base-dir",
        help=(
            "Base directory used to write file paths in "
            "sonar-external-issues.json."
        ),
    )

    scan_parser.add_argument(
        "--mode",
        choices=[mode.value for mode in ScanMode],
        default=ScanMode.FULL.value,
    )

    scan_parser.add_argument(
        "--baseline",
        help="Git baseline revision used by FAST or AUTO mode.",
    )

    scan_parser.add_argument(
        "--baseline-file",
        help=(
            "JSON file containing known finding fingerprints used by the "
            "quality gate."
        ),
    )

    scan_parser.add_argument(
        "--write-baseline",
        help="Write the current findings to a JSON baseline file.",
    )

    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0

    if args.command == "scan":
        return _scan(args)

    parser.print_help()
    return 0
