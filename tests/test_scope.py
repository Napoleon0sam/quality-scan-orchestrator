import unittest

from quality_scanner.scope import ScanMode, select_scope


class ScopeTests(unittest.TestCase):
    def test_full_mode_selects_all_candidate_files(self) -> None:
        scope = select_scope(
            requested_mode=ScanMode.FULL,
            candidate_files=("app.py", "config.py", "utils.py"),
        )

        self.assertEqual("FULL", scope.requested_mode.value)
        self.assertEqual("FULL", scope.effective_mode.value)
        self.assertIsNone(scope.baseline)
        self.assertIsNone(scope.head)
        self.assertEqual((), scope.changed_files)
        self.assertEqual(("app.py", "config.py", "utils.py"), scope.candidate_files)
        self.assertEqual(("app.py", "config.py", "utils.py"), scope.selected_files)
        self.assertIsNone(scope.fallback_reason)

    def test_fast_mode_selects_changed_python_candidates_only(self) -> None:
        scope = select_scope(
            requested_mode=ScanMode.FAST,
            baseline="baseline-sha",
            head="head-sha",
            changed_files=("README.md", "app.py", "missing.py"),
            candidate_files=("app.py", "config.py", "utils.py"),
        )

        self.assertEqual("FAST", scope.requested_mode.value)
        self.assertEqual("FAST", scope.effective_mode.value)
        self.assertEqual("baseline-sha", scope.baseline)
        self.assertEqual("head-sha", scope.head)
        self.assertEqual(("README.md", "app.py", "missing.py"), scope.changed_files)
        self.assertEqual(("app.py", "config.py", "utils.py"), scope.candidate_files)
        self.assertEqual(("app.py",), scope.selected_files)
        self.assertIsNone(scope.fallback_reason)

    def test_auto_mode_uses_fast_when_baseline_and_head_are_available(self) -> None:
        scope = select_scope(
            requested_mode=ScanMode.AUTO,
            baseline="baseline-sha",
            head="head-sha",
            changed_files=("README.md", "app.py"),
            candidate_files=("app.py", "config.py", "utils.py"),
        )

        self.assertEqual("AUTO", scope.requested_mode.value)
        self.assertEqual("FAST", scope.effective_mode.value)
        self.assertEqual("baseline-sha", scope.baseline)
        self.assertEqual("head-sha", scope.head)
        self.assertEqual(("README.md", "app.py"), scope.changed_files)
        self.assertEqual(("app.py", "config.py", "utils.py"), scope.candidate_files)
        self.assertEqual(("app.py",), scope.selected_files)
        self.assertIsNone(scope.fallback_reason)

    def test_auto_mode_falls_back_to_full_when_baseline_is_missing(self) -> None:
        scope = select_scope(
            requested_mode=ScanMode.AUTO,
            candidate_files=("app.py", "config.py", "utils.py"),
        )

        self.assertEqual("AUTO", scope.requested_mode.value)
        self.assertEqual("FULL", scope.effective_mode.value)
        self.assertIsNone(scope.baseline)
        self.assertIsNone(scope.head)
        self.assertEqual((), scope.changed_files)
        self.assertEqual(("app.py", "config.py", "utils.py"), scope.candidate_files)
        self.assertEqual(("app.py", "config.py", "utils.py"), scope.selected_files)
        self.assertEqual("baseline not provided; falling back to FULL", scope.fallback_reason)

    def test_auto_mode_falls_back_to_full_when_no_python_candidate_changed(self) -> None:
        scope = select_scope(
            requested_mode=ScanMode.AUTO,
            baseline="baseline-sha",
            head="head-sha",
            changed_files=("README.md",),
            candidate_files=("app.py", "config.py", "utils.py"),
        )

        self.assertEqual("AUTO", scope.requested_mode.value)
        self.assertEqual("FULL", scope.effective_mode.value)
        self.assertEqual("baseline-sha", scope.baseline)
        self.assertEqual("head-sha", scope.head)
        self.assertEqual(("README.md",), scope.changed_files)
        self.assertEqual(("app.py", "config.py", "utils.py"), scope.candidate_files)
        self.assertEqual(("app.py", "config.py", "utils.py"), scope.selected_files)
        self.assertEqual(
            "no changed Python candidate files; falling back to FULL",
            scope.fallback_reason,
        )


if __name__ == "__main__":
    unittest.main()
