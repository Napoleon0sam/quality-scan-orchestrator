from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re

from .models import Finding
from .reporting import write_json


BASELINE_SCHEMA_VERSION = 1
_FINGERPRINT_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class BaselineError(ValueError):
    """Raised when a baseline file is missing or malformed."""


@dataclass(frozen=True)
class Baseline:
    fingerprints: frozenset[str]


@dataclass(frozen=True)
class BaselineClassification:
    existing: tuple[Finding, ...]
    new: tuple[Finding, ...]


def classify_findings(
    findings: tuple[Finding, ...],
    baseline: Baseline | None,
) -> BaselineClassification:
    known = baseline.fingerprints if baseline is not None else frozenset()
    existing = tuple(
        finding
        for finding in findings
        if finding.fingerprint in known
    )
    new = tuple(
        finding
        for finding in findings
        if finding.fingerprint not in known
    )
    return BaselineClassification(existing=existing, new=new)


def load_baseline(path: Path) -> Baseline:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BaselineError(f"Baseline file not found: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise BaselineError(f"Could not read baseline file {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise BaselineError("Baseline root must be a JSON object.")

    schema_version = payload.get("schema_version")
    if schema_version != BASELINE_SCHEMA_VERSION:
        raise BaselineError(
            "Unsupported baseline schema version: "
            f"{schema_version!r}; expected {BASELINE_SCHEMA_VERSION}."
        )

    entries = payload.get("findings")
    if not isinstance(entries, list):
        raise BaselineError("Baseline findings must be a JSON array.")

    fingerprints: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise BaselineError(f"Baseline finding at index {index} must be an object.")
        fingerprint = entry.get("fingerprint")
        if (
            not isinstance(fingerprint, str)
            or _FINGERPRINT_PATTERN.fullmatch(fingerprint) is None
        ):
            raise BaselineError(
                f"Baseline finding at index {index} has an invalid fingerprint."
            )
        fingerprints.add(fingerprint)

    return Baseline(fingerprints=frozenset(fingerprints))


def write_baseline(
    path: Path,
    findings: tuple[Finding, ...],
    *,
    generated_at: str,
    tool_version: str,
) -> None:
    entries = [
        {
            "fingerprint": finding.fingerprint,
            "rule_id": finding.rule_id,
            "path": finding.path,
            "line": finding.line,
            "column": finding.column,
            "message": finding.message,
        }
        for finding in sorted(
            findings,
            key=lambda item: (
                item.path,
                item.line,
                item.column,
                item.rule_id,
                item.fingerprint,
            ),
        )
    ]
    write_json(
        path,
        {
            "schema_version": BASELINE_SCHEMA_VERSION,
            "generated_at": generated_at,
            "tool_version": tool_version,
            "findings": entries,
        },
    )
