import json
import re
from typing import Optional
from pydantic import BaseModel


class TrustPolicyResult(BaseModel):
    passed: bool
    reason: str
    policy_name: str


class TrustPolicy:
    @staticmethod
    def check_citation(output: str) -> TrustPolicyResult:
        url_pattern = r"https?://[^\s\]\)\"']+"
        urls = re.findall(url_pattern, output)
        if urls:
            return TrustPolicyResult(passed=True, reason="Citation found", policy_name="citation_check")
        return TrustPolicyResult(
            passed=False,
            reason="No citation or source URL found in output",
            policy_name="citation_check",
        )

    @staticmethod
    def check_schema(output: str) -> TrustPolicyResult:
        try:
            data = json.loads(output)
            if isinstance(data, dict) and len(data) > 0:
                return TrustPolicyResult(passed=True, reason="Valid JSON schema", policy_name="schema_check")
            return TrustPolicyResult(
                passed=False,
                reason="JSON must be a non-empty object",
                policy_name="schema_check",
            )
        except (json.JSONDecodeError, TypeError):
            if len(output.strip()) > 20:
                return TrustPolicyResult(
                    passed=True, reason="Free-text output meets minimum length", policy_name="schema_check"
                )
            return TrustPolicyResult(
                passed=False,
                reason=f"Output too short ({len(output.strip())} chars) and not valid JSON",
                policy_name="schema_check",
            )

    @staticmethod
    def check_not_empty(output: str) -> TrustPolicyResult:
        if output and len(output.strip()) > 10:
            return TrustPolicyResult(passed=True, reason="Output is non-trivial", policy_name="non_empty_check")
        return TrustPolicyResult(
            passed=False,
            reason="Output is empty or too short",
            policy_name="non_empty_check",
        )

    @staticmethod
    def check_no_contradictions(output: str, verified_facts: list[str]) -> TrustPolicyResult:
        output_lower = output.lower()
        for fact in verified_facts:
            fact_lower = fact.lower()
            negation_patterns = [
                f"not {fact_lower}",
                f"no {fact_lower}",
                f"never {fact_lower}",
                f"{fact_lower} is false",
                f"{fact_lower} is wrong",
            ]
            for pattern in negation_patterns:
                if pattern in output_lower:
                    return TrustPolicyResult(
                        passed=False,
                        reason=f"Potential contradiction with verified fact: '{fact}'",
                        policy_name="contradiction_check",
                    )
        return TrustPolicyResult(passed=True, reason="No contradictions detected", policy_name="contradiction_check")


def run_trust_policies(
    output: str,
    agent_id: str,
    verified_facts: Optional[list[str]] = None,
) -> tuple[bool, list[TrustPolicyResult]]:
    policies = [
        TrustPolicy.check_not_empty(output),
        TrustPolicy.check_schema(output),
    ]

    if agent_id in ("researcher", "analyst"):
        policies.append(TrustPolicy.check_citation(output))

    if verified_facts:
        policies.append(TrustPolicy.check_no_contradictions(output, verified_facts))

    all_passed = all(p.passed for p in policies)
    return all_passed, policies
