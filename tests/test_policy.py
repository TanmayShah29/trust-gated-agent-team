"""Unit tests for backend — trust policy checks."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


class TestTrustPolicy:
    def test_citation_check_passes(self):
        from app.trust.policy import TrustPolicy
        result = TrustPolicy.check_citation("According to https://example.com, the result is X.")
        assert result.passed is True

    def test_citation_check_fails_without_citations(self):
        from app.trust.policy import TrustPolicy
        result = TrustPolicy.check_citation("The result is X without any source.")
        assert result.passed is False

    def test_schema_check_valid_json(self):
        from app.trust.policy import TrustPolicy
        result = TrustPolicy.check_schema('{"answer": "test", "confidence": 0.8}')
        assert result.passed is True

    def test_schema_check_valid_freetext(self):
        from app.trust.policy import TrustPolicy
        result = TrustPolicy.check_schema("This is a sufficiently long free text output that passes the check.")
        assert result.passed is True

    def test_schema_check_invalid_short(self):
        from app.trust.policy import TrustPolicy
        result = TrustPolicy.check_schema("no")
        assert result.passed is False

    def test_not_empty_check(self):
        from app.trust.policy import TrustPolicy
        result = TrustPolicy.check_not_empty("This is a non-trivial output.")
        assert result.passed is True

    def test_not_empty_check_fails(self):
        from app.trust.policy import TrustPolicy
        result = TrustPolicy.check_not_empty("hi")
        assert result.passed is False

    def test_no_contradictions(self):
        from app.trust.policy import TrustPolicy
        result = TrustPolicy.check_no_contradictions(
            "The sky is blue.",
            ["The sky is blue"]
        )
        assert result.passed is True

    def test_contradiction_detected(self):
        from app.trust.policy import TrustPolicy
        result = TrustPolicy.check_no_contradictions(
            "The sky is not blue.",
            ["The sky is blue"]
        )
        assert result.passed is False
