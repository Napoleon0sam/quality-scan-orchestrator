from dataclasses import dataclass
from enum import Enum


class ScanMode(str, Enum):
    FULL = "FULL"
    FAST = "FAST"
    AUTO = "AUTO"


@dataclass(frozen=True)
class ScanScope:
    requested_mode: ScanMode
    effective_mode: ScanMode
    baseline: str | None
    head: str | None
    changed_files: tuple[str, ...]
    candidate_files: tuple[str, ...]
    selected_files: tuple[str, ...]
    fallback_reason: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "requested_mode": self.requested_mode.value,
            "effective_mode": self.effective_mode.value,
            "baseline": self.baseline,
            "head": self.head,
            "changed_files": list(self.changed_files),
            "candidate_files": list(self.candidate_files),
            "selected_files": list(self.selected_files),
            "fallback_reason": self.fallback_reason,
        }


def select_scope(
    *,
    requested_mode: ScanMode,
    candidate_files: tuple[str, ...],
    baseline: str | None = None,
    head: str | None = None,
    changed_files: tuple[str, ...] = (),
    fallback_reason: str | None = None,
) -> ScanScope:
    if requested_mode is ScanMode.FAST:
        if baseline is None:
            raise ValueError("FAST scan mode requires a baseline.")
        if head is None:
            raise ValueError("FAST scan mode requires a head revision.")

        selected_files = _select_changed_candidates(
            changed_files=changed_files,
            candidate_files=candidate_files,
        )

        return ScanScope(
            requested_mode=requested_mode,
            effective_mode=ScanMode.FAST,
            baseline=baseline,
            head=head,
            changed_files=changed_files,
            candidate_files=candidate_files,
            selected_files=selected_files,
            fallback_reason=None,
        )

    if requested_mode is ScanMode.AUTO:
        if fallback_reason is not None:
            return _full_scope(
                requested_mode=requested_mode,
                baseline=baseline,
                head=head,
                changed_files=changed_files,
                candidate_files=candidate_files,
                fallback_reason=fallback_reason,
            )
        if baseline is None:
            return _full_scope(
                requested_mode=requested_mode,
                baseline=baseline,
                head=head,
                changed_files=changed_files,
                candidate_files=candidate_files,
                fallback_reason="baseline not provided; falling back to FULL",
            )
        if head is None:
            return _full_scope(
                requested_mode=requested_mode,
                baseline=baseline,
                head=head,
                changed_files=changed_files,
                candidate_files=candidate_files,
                fallback_reason="head revision not available; falling back to FULL",
            )

        selected_files = _select_changed_candidates(
            changed_files=changed_files,
            candidate_files=candidate_files,
        )
        if not selected_files:
            return _full_scope(
                requested_mode=requested_mode,
                baseline=baseline,
                head=head,
                changed_files=changed_files,
                candidate_files=candidate_files,
                fallback_reason="no changed Python candidate files; falling back to FULL",
            )

        return ScanScope(
            requested_mode=requested_mode,
            effective_mode=ScanMode.FAST,
            baseline=baseline,
            head=head,
            changed_files=changed_files,
            candidate_files=candidate_files,
            selected_files=selected_files,
            fallback_reason=None,
        )

    if requested_mode is not ScanMode.FULL:
        raise ValueError(f"Unsupported scan mode: {requested_mode.value}")

    return _full_scope(
        requested_mode=requested_mode,
        baseline=None,
        head=None,
        changed_files=changed_files,
        candidate_files=candidate_files,
        fallback_reason=None,
    )


def _select_changed_candidates(
    *,
    changed_files: tuple[str, ...],
    candidate_files: tuple[str, ...],
) -> tuple[str, ...]:
    candidates = set(candidate_files)
    return tuple(
        path for path in changed_files
        if path in candidates
    )


def _full_scope(
    *,
    requested_mode: ScanMode,
    baseline: str | None,
    head: str | None,
    changed_files: tuple[str, ...],
    candidate_files: tuple[str, ...],
    fallback_reason: str | None,
) -> ScanScope:
    return ScanScope(
        requested_mode=requested_mode,
        effective_mode=ScanMode.FULL,
        baseline=baseline,
        head=head,
        changed_files=changed_files,
        candidate_files=candidate_files,
        selected_files=candidate_files,
        fallback_reason=fallback_reason,
    )
