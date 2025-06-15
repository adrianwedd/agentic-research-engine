# P2-01: Implement Evaluator Agent with Self-Correction
# Location: agents/evaluator.py
"""
Create the quality assurance agent that provides external feedback
and drives the iterative correction cycle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional


class EvaluatorAgent:
    def __init__(
        self, evaluation_framework: Optional[Dict[str, Callable]] = None
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

    def generate_correction_feedback(self, evaluation_results: Dict) -> Dict:
        """Generate actionable feedback for improvement."""
        issues: List[Dict[str, Any]] = []
        scores: List[float] = []

        for criterion, result in evaluation_results.items():
            score = float(result.get("score", 0))
            scores.append(score)
            if score < 1.0:
                issues.append({"criterion": criterion, "details": result})

        overall_score = sum(scores) / len(scores) if scores else 0.0
        feedback = {
            "score": round(overall_score, 3),
            "issues": issues,
        }

        if issues:
            feedback[
                "recommendations"
            ] = "Review the listed issues and revise the output accordingly."
        else:
            feedback["recommendations"] = "No issues detected."
        return feedback
