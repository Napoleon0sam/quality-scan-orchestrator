from .models import GateResult, GateStatus, ScanSummary


def evaluate(
    summary: ScanSummary,
    *,
    baseline_applied: bool = False,
) -> GateResult:
    if summary.errors:
        return GateResult(
            GateStatus.ERROR,
            "Scanner errors occurred.",
            3,
        )

    if summary.scanned_files == 0:
        return GateResult(
            GateStatus.ERROR,
            "No Python files were selected for scanning.",
            3,
        )

    if summary.new_critical_count or summary.new_high_count:
        return GateResult(
            GateStatus.FAIL,
            (
                "Critical or high severity new finding exists."
                if baseline_applied
                else "Critical or high severity finding exists."
            ),
            1,
        )

    return GateResult(
        GateStatus.PASS,
        (
            "No new blocking finding exists; existing findings are baselined."
            if baseline_applied
            else "No blocking finding exists."
        ),
        0,
    )
