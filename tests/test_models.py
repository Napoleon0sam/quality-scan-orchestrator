import unittest

from quality_scanner.models import Category, Finding, Severity, redact_snippet

class ModelTests(unittest.TestCase):
    def test_finding_has_stable_contract(self) -> None:
        finding = Finding.create(
            rule_id="QSO-PY-SEC-001", category=Category.SECURITY, severity=Severity.HIGH,
            path="src/app.py", line=4, column=2, message="Avoid eval.",
            remediation="Use explicit parsing.", snippet="eval(user_input)",
        )
        payload = finding.to_dict()
        self.assertEqual("Security", payload["category"])
        self.assertEqual("HIGH", payload["severity"])
        self.assertEqual(64, len(payload["fingerprint"]))

    def test_redaction_hides_secret_value(self) -> None:
        redacted = redact_snippet('api_token = "real-secret-value"')
        self.assertNotIn("real-secret-value", redacted)
        self.assertEqual('api_token = "<redacted>"', redacted)

if __name__ == "__main__":
    unittest.main()
