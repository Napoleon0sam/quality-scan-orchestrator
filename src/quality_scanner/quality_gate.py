from .models import GateResult, GateStatus, ScanSummary


def evaluate(summary: ScanSummary) -> GateResult:
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

    if summary.critical_count or summary.high_count:
        return GateResult(
            GateStatus.FAIL,
            "Critical or high severity finding exists.",
            1,
        )

    return GateResult(
        GateStatus.PASS,
        "No blocking finding exists.",
        0,
    )
