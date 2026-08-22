from dataclasses import dataclass
import json
from pathlib import Path

from .models import Category, Severity


@dataclass(frozen=True)
class RuleDefinition:
    id: str
    category: Category
    severity: Severity
    message: str
    remediation: str


@dataclass(frozen=True)
class ScanConfig:
    function_length_limit: int
    rules: tuple[RuleDefinition, ...]

    def by_id(self) -> dict[str, RuleDefinition]:
        return {rule.id: rule for rule in self.rules}


class ConfigError(ValueError):
    pass


def _required_string(row: dict[str, object], key: str, index: int) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"rules[{index}].{key} must be a non-empty string")
    return value.strip()


def load_config(path: Path) -> ScanConfig:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ConfigError(
            f"Cannot load config {path}: {type(exc).__name__}: {exc}"
        ) from exc

    if not isinstance(payload, dict):
        raise ConfigError("Config root must be an object")

    limit = payload.get("function_length_limit")
    if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
        raise ConfigError("function_length_limit must be a positive integer")

    raw_rules = payload.get("rules")
    if not isinstance(raw_rules, list) or not raw_rules:
        raise ConfigError("rules must be a non-empty array")

    rules: list[RuleDefinition] = []
    for index, raw_rule in enumerate(raw_rules):
        if not isinstance(raw_rule, dict):
            raise ConfigError(f"rules[{index}] must be an object")
        rule_id = _required_string(raw_rule, "id", index)
        category_text = _required_string(raw_rule, "category", index)
        severity_text = _required_string(raw_rule, "severity", index)
        try:
            category = Category(category_text)
            severity = Severity(severity_text)
        except ValueError as exc:
            raise ConfigError(
                f"rules[{index}] has unknown category or severity"
            ) from exc
        rules.append(
            RuleDefinition(
                id=rule_id,
                category=category,
                severity=severity,
                message=_required_string(raw_rule, "message", index),
                remediation=_required_string(raw_rule, "remediation", index),
            )
        )

    ids = [rule.id for rule in rules]
    if len(ids) != len(set(ids)):
        raise ConfigError("Rule IDs must be unique")

    return ScanConfig(function_length_limit=limit, rules=tuple(rules))
