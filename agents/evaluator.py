# P2-01: Implement Evaluator Agent with Self-Correction
# Location: agents/evaluator.py
"""
Create the quality assurance agent that provides external feedback
and drives the iterative correction cycle.
"""

from __future__ import annotations

import re
from typing import Callable, Dict, List, Optional

from agents.critique import Critique


class EvaluatorAgent:
    def __init__(
        self,
        evaluation_framework: Optional[Dict[str, Callable]] = None,
        fact_check_llm: Optional[Callable[[str], str]] = None,
    ) -> None:
        """Initialize with comprehensive evaluation capabilities.

        Required components:
        - Multiple evaluation criteria (accuracy, completeness, bias)
        - Source verification mechanisms
        - Quality scoring algorithms
        - Feedback generation templates
        """
        self.evaluation_framework: Dict[str, Callable[[Dict, Dict], Dict]] = (
            evaluation_framework or {}
        )
        self.evaluation_framework.setdefault("accuracy", self._evaluate_accuracy)
        self.evaluation_framework.setdefault(
            "completeness", self._evaluate_completeness
        )
        self.evaluation_framework.setdefault("bias", self._evaluate_bias)
        self.evaluation_framework.setdefault("citations", self._evaluate_citations)

        # Optional callable for verifying individual claims against provided
        # sources. The callable should accept a prompt string and return a
        # textual response such as "yes" or "no".
        self.fact_check_llm = fact_check_llm

    # ------------------------------------------------------------------
    # Default evaluation helpers
    # ------------------------------------------------------------------
    def _evaluate_accuracy(self, output: Dict, criteria: Dict) -> Dict:
        sources: List[str] = output.get("sources", [])
        claims: List[str] = criteria.get("claims", [])
        missing: List[str] = [
            c for c in claims if not any(c.lower() in s.lower() for s in sources)
        ]
        score = 1.0 if not claims else max(0.0, 1.0 - len(missing) / len(claims))
        return {"score": score, "missing_claims": missing}

    def _evaluate_completeness(self, output: Dict, criteria: Dict) -> Dict:
        text = output.get("text", "").lower()
        required: List[str] = criteria.get("required_points", [])
        missing: List[str] = [p for p in required if p.lower() not in text]
        score = 1.0 if not required else max(0.0, 1.0 - len(missing) / len(required))
        return {"score": score, "missing_points": missing}

    def _evaluate_bias(self, output: Dict, criteria: Dict) -> Dict:
        text = output.get("text", "").lower()
        bias_terms: List[str] = criteria.get("bias_terms", [])
        found: List[str] = [b for b in bias_terms if b.lower() in text]
        score = 1.0 if not found else max(0.0, 1.0 - 0.1 * len(found))
        return {"score": score, "bias_terms": found}

    def _evaluate_citations(self, output: Dict, criteria: Dict) -> Dict:
        citations: List[str] = output.get("citations", [])
        sources: List[str] = output.get("sources", [])
        invalid: List[str] = [c for c in citations if c not in sources]
        score = 1.0 if not citations else max(0.0, 1.0 - len(invalid) / len(citations))
        return {"score": score, "invalid_citations": invalid}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def evaluate_research_output(self, output: Dict, evaluation_criteria: Dict) -> Dict:
        """Comprehensively evaluate research deliverables."""
        results: Dict[str, Dict] = {}
        for criterion, params in evaluation_criteria.items():
            func = self.evaluation_framework.get(criterion)
            if func:
                results[criterion] = func(output, params)
        return results

    def generate_correction_feedback(self, evaluation_results: Dict) -> Critique:
        """Generate a structured critique object."""

        scores: Dict[str, float] = {}
        feedback_parts: List[str] = []

        for criterion, result in evaluation_results.items():
            score = float(result.get("score", 0))
            scores[criterion] = score
            if score < 1.0:
                feedback_parts.append(f"{criterion}: {result}")

        overall = sum(scores.values()) / len(scores) if scores else 0.0
        text = "; ".join(feedback_parts) if feedback_parts else "All criteria passed."

        critique = Critique(
            overall_score=round(overall, 3),
            criteria_breakdown=scores,
            feedback_text=text,
        )
        critique.validate()
        return critique

    # ------------------------------------------------------------------
    # Factual Verification
    # ------------------------------------------------------------------
    def verify_factual_accuracy(
        self, summary: str, sources: List[str]
    ) -> Dict[str, List[str]]:
        """Check each claim in ``summary`` against ``sources``.

        The summary is split into sentences which are treated as discrete claims.
        For each claim, the ``fact_check_llm`` callable is prompted with the
        sources as context and asked whether the claim is supported. If no LLM
        callable is provided, a simple substring match is used as a fallback.
        """

        if not isinstance(summary, str) or not summary.strip():
            return {"unsupported_facts": []}

        claims = [c.strip() for c in re.split(r"(?<=[.!?])\s+", summary) if c.strip()]
        unsupported: List[str] = []

        combined_sources = "\n".join(sources)
        for claim in claims:
            supported = False
            if self.fact_check_llm is None:
                supported = claim.lower() in combined_sources.lower()
            else:
                prompt = (
                    "You are a factual verifier. Only use the provided sources "
                    "to answer. Respond with 'yes' or 'no'.\n\nSources:\n"
                    f"{combined_sources}\n\nClaim: {claim}"
                )
                try:
                    response = str(self.fact_check_llm(prompt)).strip().lower()
                except Exception:
                    response = "no"
                supported = response.startswith("yes")

            if not supported:
                unsupported.append(claim)

        return {"unsupported_facts": unsupported}
