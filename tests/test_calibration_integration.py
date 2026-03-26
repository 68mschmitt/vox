"""Integration tests for the calibration loop with a mock LLM provider.

Tests the full calibration flow without making real API calls.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from persona_forge.calibrate.evaluator import (
    DivergenceReport,
    EvaluationResult,
    evaluate_answer,
    generate_persona_answer_text,
)
from persona_forge.calibrate.questions import generate_questions
from persona_forge.persona.model import Persona, QuestionScore


class MockProvider:
    """Mock LLM provider that returns canned JSON responses."""

    def __init__(self, responses: list[str] | None = None):
        self._responses = responses or []
        self._call_index = 0

    def generate(self, system: str, user: str, temperature: float = 0.7) -> str:
        if self._call_index < len(self._responses):
            response = self._responses[self._call_index]
            self._call_index += 1
            return response
        # Default: return a generic valid response
        return json.dumps({"questions": [], "changes": []})

    @property
    def name(self) -> str:
        return "mock"


MOCK_QUESTIONS_RESPONSE = json.dumps(
    {
        "questions": [
            {
                "id": "q1",
                "text": "Your team needs to pick a database. What do you recommend?",
                "category": "architecture",
                "focus_area": "decision_making",
                "difficulty": "standard",
            },
            {
                "id": "q2",
                "text": "A PR introduces a new ORM. What's your feedback?",
                "category": "code_review",
                "focus_area": "tool_philosophy",
                "difficulty": "standard",
            },
        ]
    }
)

MOCK_PERSONA_ANSWER = "Use PostgreSQL. It handles 99% of use cases."

MOCK_EVALUATION_RESPONSE = json.dumps(
    {
        "content": {"score": 7, "gap": "minor", "trait_signal": "good match"},
        "tone": {"score": 5, "gap": "too formal", "trait_signal": "communication_tone"},
        "priorities": {"score": 7, "gap": "similar", "trait_signal": "values aligned"},
        "specificity": {
            "score": 6,
            "gap": "less specific",
            "trait_signal": "more examples",
        },
    }
)


class TestGenerateQuestions:
    def test_returns_calibration_questions(self, sample_persona: Persona):
        """generate_questions returns CalibrationQuestion objects."""
        provider = MockProvider([MOCK_QUESTIONS_RESPONSE])
        questions = generate_questions(
            sample_persona, provider, round_number=1, count=2
        )

        assert len(questions) == 2
        assert questions[0].id == "q1"
        assert questions[0].category == "architecture"
        assert questions[1].id == "q2"

    def test_empty_questions_raises(self, sample_persona: Persona):
        """Empty question list from LLM raises RuntimeError."""
        provider = MockProvider([json.dumps({"questions": []})])

        import pytest

        with pytest.raises(RuntimeError, match="failed to generate"):
            generate_questions(sample_persona, provider, round_number=1)


class TestGeneratePersonaAnswer:
    def test_returns_string(self, sample_persona: Persona):
        """generate_persona_answer_text returns a string."""
        provider = MockProvider([MOCK_PERSONA_ANSWER])
        answer = generate_persona_answer_text(
            sample_persona,
            "Should we use PostgreSQL?",
            provider,
        )
        assert isinstance(answer, str)
        assert "PostgreSQL" in answer


class TestEvaluateAnswer:
    def test_returns_question_score(self):
        """evaluate_answer returns a QuestionScore."""
        provider = MockProvider([MOCK_EVALUATION_RESPONSE])
        score = evaluate_answer(
            question_text="Pick a database",
            human_answer="Postgres always",
            persona_answer="Use PostgreSQL",
            provider=provider,
        )
        assert isinstance(score, QuestionScore)
        assert score.content == 7.0
        assert score.tone == 5.0
        assert score.priorities == 7.0
        assert score.specificity == 6.0

    def test_clamps_scores_to_range(self):
        """Scores outside 1-10 are clamped."""
        bad_response = json.dumps(
            {
                "content": {"score": 15, "gap": "", "trait_signal": ""},
                "tone": {"score": -2, "gap": "", "trait_signal": ""},
                "priorities": {"score": 7, "gap": "", "trait_signal": ""},
                "specificity": {"score": 0.5, "gap": "", "trait_signal": ""},
            }
        )
        provider = MockProvider([bad_response])
        score = evaluate_answer("q", "h", "p", provider)
        assert score.content == 10.0
        assert score.tone == 1.0
        assert score.specificity == 1.0


class TestCalibrationIntegration:
    def test_full_round_evaluation(self, sample_persona: Persona):
        """Full round: generate questions -> persona answers -> evaluate."""
        responses = [
            # 1) generate_questions
            MOCK_QUESTIONS_RESPONSE,
            # 2) persona answer for q1
            "Use Postgres. Boring, reliable, you know it works.",
            # 3) evaluation for q1
            MOCK_EVALUATION_RESPONSE,
            # 4) persona answer for q2
            "Why do we need an ORM? SQL is fine.",
            # 5) evaluation for q2
            MOCK_EVALUATION_RESPONSE,
        ]
        provider = MockProvider(responses)

        # Step 1: Generate questions
        questions = generate_questions(sample_persona, provider, count=2)
        assert len(questions) == 2

        # Step 2: Simulate human answers
        human_answers = {
            "q1": "Postgres. Don't overthink it.",
            "q2": "Push back. ORMs are usually unnecessary complexity.",
        }

        # Step 3-4: Evaluate each question
        results: list[EvaluationResult] = []
        for q in questions:
            if q.id in human_answers:
                pa = generate_persona_answer_text(sample_persona, q.text, provider)
                score = evaluate_answer(q.text, human_answers[q.id], pa, provider)
                results.append(
                    EvaluationResult(
                        question_id=q.id,
                        question_text=q.text,
                        category=q.category,
                        human_answer=human_answers[q.id],
                        persona_answer=pa,
                        scores=score,
                    )
                )

        # Step 5: Build report
        report = DivergenceReport(results=results)
        assert len(report.results) == 2
        assert report.overall_score > 0
        assert report.weakest_dimension == "tone"
        assert report.strongest_dimension in ("content", "priorities")
