# P2-01: Implement Evaluator Agent with Self-Correction
# Location: agents/evaluator.py
"""
Create the quality assurance agent that provides external feedback
and drives the iterative correction cycle.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

import yaml

from agents.critique import Critique
from services.monitoring.events import EvaluationCompletedEvent, publish_event


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
        self.evaluation_framework.setdefault("coherence", self._evaluate_coherence)
        self.evaluation_framework.setdefault("bias", self._evaluate_bias)
        self.evaluation_framework.setdefault("citations", self._evaluate_citations)
        self.evaluation_framework.setdefault(
            "source_quality", self._evaluate_source_quality
        )

        # Optional callable for verifying individual claims against provided
        # sources. The callable should accept a prompt string and return a
        # textual response such as "yes" or "no".
        self.fact_check_llm = fact_check_llm

        config = self._load_source_quality_config()
        self.allowlist = set(config.get("allowlist", []))
        self.blocklist = set(config.get("blocklist", []))

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

    def _evaluate_coherence(self, output: Dict, criteria: Dict) -> Dict:
        text = output.get("text", "")
        if not text.strip():
            return {"score": 0.0}
        sentences = [s for s in re.split(r"[.!?]", text) if s.strip()]
        lengths = [len(s.split()) for s in sentences]
        if not lengths:
            return {"score": 1.0}
        avg_len = sum(lengths) / len(lengths)
        score = max(0.0, min(1.0, 1.0 - abs(avg_len - 20) / 20))
        return {"score": round(score, 3)}

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

    def _load_source_quality_config(self) -> Dict[str, List[str]]:
        path = (
            Path(__file__).resolve().parent
            / "evaluator"
            / "config"
            / "source_quality.yml"
        )
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as f:
            try:
                return yaml.safe_load(f) or {}
            except Exception:
                return {}

    def _evaluate_source_quality(self, output: Dict, criteria: Dict) -> Dict:
        sources: List[str] = output.get("sources", [])
        scores: Dict[str, float] = {}
        for src in sources:
            domain = urlparse(src).netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            score = 0.0
            if domain in self.allowlist:
                score += 1.0
            if domain in self.blocklist:
                score -= 1.0
            if self.fact_check_llm:
                prompt = (
                    "Rate the trustworthiness of the domain '{domain}' on a scale of 1-5 "
                    '(5 highest). Provide JSON {{"rating": <1-5>, "reason": "..."}}.'
                ).format(domain=domain)
                try:
                    response = self.fact_check_llm(prompt)
                    data = json.loads(str(response))
                    rating = int(data.get("rating", 3))
                    score += (rating - 3) / 2.0
                except Exception:
                    pass
            scores[src] = round(score, 3)

        avg = sum(scores.values()) / len(scores) if scores else 0.0
        return {"score": round(avg, 3), "scores": scores}

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

    def build_performance_vector(
        self, results: Dict[str, Dict], metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Convert raw evaluation results and metadata to the performance vector schema."""
        meta = metadata or {}
        return {
            "accuracy_score": float(results.get("accuracy", {}).get("score", 0.0)),
            "completeness_score": float(
                results.get("completeness", {}).get("score", 0.0)
            ),
            "coherence_score": float(results.get("coherence", {}).get("score", 0.0)),
            "citation_score": float(results.get("citations", {}).get("score", 0.0)),
            "source_quality_score": float(
                results.get("source_quality", {}).get("score", 0.0)
            ),
            "token_cost": float(meta.get("token_cost", 0.0)),
            "completion_time_sec": float(meta.get("completion_time_sec", 0.0)),
            "tool_success_rate": float(meta.get("tool_success_rate", 0.0)),
        }

    def evaluate_and_publish(
        self,
        output: Dict,
        evaluation_criteria: Dict,
        *,
        task_id: str,
        worker_agent_id: str,
        evaluator_id: str,
        task_type: str | None = None,
        is_final: bool = False,
        metadata: Dict[str, Any] | None = None,
    ) -> Dict:
        """Evaluate output and publish an EvaluationCompletedEvent.

        Returns the structured performance vector."""

        results = self.evaluate_research_output(output, evaluation_criteria)
        vector = self.build_performance_vector(results, metadata)
        event = EvaluationCompletedEvent(
            task_id=task_id,
            worker_agent_id=worker_agent_id,
            evaluator_id=evaluator_id,
            performance_vector=vector,
            task_type=task_type,
            is_final=is_final,
            metadata=metadata or {},
        )
        publish_event(event)
        return vector

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
