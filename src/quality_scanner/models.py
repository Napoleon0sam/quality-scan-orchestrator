from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import re


class Category(str, Enum):
    RELIABILITY = "Reliability"
    SECURITY = "Security"
    MAINTAINABILITY = "Maintainability"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class GateStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"


_SECRET_ASSIGNMENT = re.compile(
    r"(?i)(password|passwd|secret|token|api[_-]?key)(\s*=\s*)"
    r"(['\"])(.*?)(\3)"
)


def redact_snippet(value: str) -> str:
    return _SECRET_ASSIGNMENT.sub(
        lambda match: (
            f"{match.group(1)}{match.group(2)}"
            f"{match.group(3)}<redacted>{match.group(5)}"
        ),
        value,
    )


def stable_fingerprint(
    rule_id: str,
    path: str,
    line: int,
    message: str,
) -> str:
    normalized_path = path.replace("\\", "/")
    raw = f"{rule_id}|{normalized_path}|{line}|{message}"
    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class Finding:
    rule_id: str
    category: Category
    severity: Severity
    path: str
    line: int
    column: int
    message: str
    remediation: str
    fingerprint: str
    snippet: str

    @classmethod
    def create(
        cls,
        *,
        rule_id: str,
        category: Category,
        severity: Severity,
        path: str,
        line: int,
        column: int,
        message: str,
        remediation: str,
        snippet: str,
    ) -> "Finding":
        safe_snippet = redact_snippet(snippet)
        fingerprint = stable_fingerprint(
            rule_id,
            path,
            line,
            message,
        )

        return cls(
            rule_id=rule_id,
            category=category,
            severity=severity,
            path=path,
            line=line,
            column=column,
            message=message,
            remediation=remediation,
            fingerprint=fingerprint,
            snippet=safe_snippet,
        )

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["category"] = self.category.value
        payload["severity"] = self.severity.value
        return payload


@dataclass(frozen=True)
class ScanSummary:
    scanned_files: int
    findings: int
    errors: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True)
class GateResult:
    status: GateStatus
    reason: str
    exit_code: int

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "reason": self.reason,
            "exit_code": self.exit_code,
        }
