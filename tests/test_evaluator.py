"""Tests for calibration evaluator and related data types."""

from __future__ import annotations

from persona_forge.calibrate.evaluator import DivergenceReport, EvaluationResult
from persona_forge.persona.model import QuestionScore


class TestEvaluationResult:
    def test_to_dict(self):
        """EvaluationResult serializes to dict."""
        result = EvaluationResult(
            question_id="q1",
            question_text="Test question?",
            category="architecture",
            human_answer="My answer",
            persona_answer="Persona answer",
            scores=QuestionScore(
                content=7.0, tone=5.0, priorities=6.0, specificity=7.0
            ),
        )
        d = result.to_dict()
        assert d["question_id"] == "q1"
        assert d["scores"]["content"] == 7.0


class TestDivergenceReport:
    def _make_report(
        self, scores: list[tuple[float, float, float, float]]
    ) -> DivergenceReport:
        results = []
        for i, (c, t, p, s) in enumerate(scores):
            results.append(
                EvaluationResult(
                    question_id=f"q{i + 1}",
                    question_text=f"Question {i + 1}",
                    category="test",
                    human_answer="human",
                    persona_answer="persona",
                    scores=QuestionScore(
                        content=c, tone=t, priorities=p, specificity=s
                    ),
                )
            )
        return DivergenceReport(results=results)

    def test_overall_score(self):
        """Overall score is the mean of per-question overall scores."""
        report = self._make_report(
            [
                (8.0, 6.0, 7.0, 5.0),  # overall = 8*0.3 + 6*0.3 + 7*0.25 + 5*0.15 = 6.7
                (6.0, 8.0, 5.0, 7.0),  # overall = 6*0.3 + 8*0.3 + 5*0.25 + 7*0.15 = 6.5
            ]
        )
        assert abs(report.overall_score - 6.6) < 0.1

    def test_dimension_averages(self):
        """Dimension averages are correct."""
        report = self._make_report(
            [
                (8.0, 6.0, 7.0, 5.0),
                (6.0, 4.0, 7.0, 9.0),
            ]
        )
        avgs = report.dimension_averages
        assert avgs["content"] == 7.0
        assert avgs["tone"] == 5.0
        assert avgs["priorities"] == 7.0
        assert avgs["specificity"] == 7.0

    def test_weakest_dimension(self):
        """Weakest dimension is correctly identified."""
        report = self._make_report(
            [
                (8.0, 3.0, 7.0, 5.0),
                (7.0, 4.0, 6.0, 6.0),
            ]
        )
        assert report.weakest_dimension == "tone"

    def test_strongest_dimension(self):
        """Strongest dimension is correctly identified."""
        report = self._make_report(
            [
                (8.0, 3.0, 7.0, 5.0),
                (9.0, 4.0, 6.0, 6.0),
            ]
        )
        assert report.strongest_dimension == "content"

    def test_empty_report(self):
        """Empty report returns zero scores."""
        report = DivergenceReport(results=[])
        assert report.overall_score == 0.0
        assert report.dimension_averages["content"] == 0

    def test_format_for_prompt(self):
        """Format produces readable text for LLM consumption."""
        report = self._make_report(
            [
                (7.0, 5.0, 6.0, 7.0),
            ]
        )
        text = report.format_for_prompt()
        assert "Overall Score" in text
        assert "content" in text
        assert "Weakest" in text
