from __future__ import annotations

from pathlib import Path

from .config import ScanConfig
from .models import Category, Finding, Severity
from .reporting import write_json


ENGINE_ID = "codescan"


_CATEGORY_TO_SOFTWARE_QUALITY = {
    Category.SECURITY: "SECURITY",
    Category.RELIABILITY: "RELIABILITY",
    Category.MAINTAINABILITY: "MAINTAINABILITY",
}

_CATEGORY_TO_CLEAN_CODE_ATTRIBUTE = {
    Category.SECURITY: "TRUSTWORTHY",
    Category.RELIABILITY: "LOGICAL",
    Category.MAINTAINABILITY: "FOCUSED",
}

_SEVERITY_TO_IMPACT = {
    Severity.CRITICAL: "BLOCKER",
    Severity.HIGH: "HIGH",
    Severity.MEDIUM: "MEDIUM",
    Severity.LOW: "LOW",
}


def _rule_payload(rule_id: str, config: ScanConfig) -> dict[str, object]:
    rule = config.by_id()[rule_id]
    software_quality = _CATEGORY_TO_SOFTWARE_QUALITY[rule.category]
    impact_severity = _SEVERITY_TO_IMPACT[rule.severity]

    return {
        "id": rule.id,
        "name": rule.message,
        "description": rule.remediation,
        "engineId": ENGINE_ID,
        "cleanCodeAttribute": _CATEGORY_TO_CLEAN_CODE_ATTRIBUTE[rule.category],
        "impacts": [
            {
                "softwareQuality": software_quality,
                "severity": impact_severity,
            }
        ],
    }


def _sonar_file_path(
    finding: Finding,
    *,
    project_root: Path | None,
    sonar_base_dir: Path | None,
) -> str:
    if project_root is None or sonar_base_dir is None:
        return finding.path.replace("\\", "/")

    source_path = (project_root / finding.path).resolve()
    base_dir = sonar_base_dir.resolve()
    try:
        return source_path.relative_to(base_dir).as_posix()
    except ValueError:
        return finding.path.replace("\\", "/")


def _issue_payload(
    finding: Finding,
    *,
    project_root: Path | None,
    sonar_base_dir: Path | None,
) -> dict[str, object]:
    message = f"{finding.message} Remediation: {finding.remediation}"
    return {
        "ruleId": finding.rule_id,
        "effortMinutes": 0,
        "primaryLocation": {
            "message": message,
            "filePath": _sonar_file_path(
                finding,
                project_root=project_root,
                sonar_base_dir=sonar_base_dir,
            ),
            "textRange": {
                "startLine": finding.line,
            },
        },
    }


def build_sonar_external_issues(
    findings: tuple[Finding, ...],
    config: ScanConfig,
    *,
    project_root: Path | None = None,
    sonar_base_dir: Path | None = None,
) -> dict[str, object]:
    rule_ids = sorted(rule.id for rule in config.rules)
    return {
        "rules": [
            _rule_payload(rule_id, config)
            for rule_id in rule_ids
        ],
        "issues": [
            _issue_payload(
                finding,
                project_root=project_root,
                sonar_base_dir=sonar_base_dir,
            )
            for finding in findings
        ],
    }


def write_sonar_external_issues_report(
    output_dir: Path,
    *,
    findings: tuple[Finding, ...],
    config: ScanConfig,
    project_root: Path | None = None,
    sonar_base_dir: Path | None = None,
) -> None:
    write_json(
        output_dir / "sonar-external-issues.json",
        build_sonar_external_issues(
            findings,
            config,
            project_root=project_root,
            sonar_base_dir=sonar_base_dir,
        ),
    )
