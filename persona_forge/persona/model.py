"""Persona data model and supporting types.

Central data structures for Persona Forge. The persona is stored as
structured JSON and rendered to natural language only at export time.

POC scope: 8 core traits + values + frustrations.
Forward-compatible optional fields included for Alpha (decision_heuristics,
tech_preferences, anti_patterns).

Schema reference: design/DATA-MODEL.md
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ---------------------------------------------------------------------------
# Supporting types
# ---------------------------------------------------------------------------


@dataclass
class Trait:
    """A single persona trait with calibration metadata.

    The spectrum defines the axis for directional mutation.
    The calibrated flag tracks whether this trait has been tested
    in the calibration loop vs. still a seed-phase default.
    """

    value: str
    spectrum: tuple[str, str]
    calibrated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "spectrum": list(self.spectrum),
            "calibrated": self.calibrated,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Trait:
        return cls(
            value=data["value"],
            spectrum=tuple(data["spectrum"]),
            calibrated=data.get("calibrated", False),
        )


@dataclass
class Identity:
    """Professional background and context."""

    background: str
    daily_workflow: str
    years_experience: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "background": self.background,
            "daily_workflow": self.daily_workflow,
            "years_experience": self.years_experience,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Identity:
        return cls(
            background=data["background"],
            daily_workflow=data["daily_workflow"],
            years_experience=data["years_experience"],
        )


@dataclass
class ResponsePatterns:
    """How the persona structures responses."""

    structure: str  # e.g. "Direct answer first, then reasoning"
    length_preference: str  # e.g. "Concise unless asked for detail"
    code_vs_prose: str  # e.g. "Prefers code examples over prose"

    def to_dict(self) -> dict[str, Any]:
        return {
            "structure": self.structure,
            "length_preference": self.length_preference,
            "code_vs_prose": self.code_vs_prose,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResponsePatterns:
        return cls(
            structure=data["structure"],
            length_preference=data["length_preference"],
            code_vs_prose=data["code_vs_prose"],
        )


@dataclass
class TechPreferences:
    """Technical tool and language preferences.

    Forward-compatible field — optional in POC, populated in Alpha.
    """

    languages: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    philosophy: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "languages": self.languages,
            "frameworks": self.frameworks,
            "tools": self.tools,
            "philosophy": self.philosophy,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TechPreferences:
        return cls(
            languages=data.get("languages", []),
            frameworks=data.get("frameworks", []),
            tools=data.get("tools", []),
            philosophy=data.get("philosophy", ""),
        )


@dataclass
class Traits:
    """The 8 core persona traits."""

    communication_tone: Trait
    technical_depth: Trait
    risk_tolerance: Trait
    conflict_style: Trait
    decision_making: Trait
    humor: Trait
    teaching_approach: Trait
    tool_philosophy: Trait

    def to_dict(self) -> dict[str, Any]:
        return {
            "communication_tone": self.communication_tone.to_dict(),
            "technical_depth": self.technical_depth.to_dict(),
            "risk_tolerance": self.risk_tolerance.to_dict(),
            "conflict_style": self.conflict_style.to_dict(),
            "decision_making": self.decision_making.to_dict(),
            "humor": self.humor.to_dict(),
            "teaching_approach": self.teaching_approach.to_dict(),
            "tool_philosophy": self.tool_philosophy.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Traits:
        return cls(
            communication_tone=Trait.from_dict(data["communication_tone"]),
            technical_depth=Trait.from_dict(data["technical_depth"]),
            risk_tolerance=Trait.from_dict(data["risk_tolerance"]),
            conflict_style=Trait.from_dict(data["conflict_style"]),
            decision_making=Trait.from_dict(data["decision_making"]),
            humor=Trait.from_dict(data["humor"]),
            teaching_approach=Trait.from_dict(data["teaching_approach"]),
            tool_philosophy=Trait.from_dict(data["tool_philosophy"]),
        )

    def get(self, name: str) -> Trait | None:
        """Get a trait by name."""
        return getattr(self, name, None)

    def set(self, name: str, trait: Trait) -> None:
        """Set a trait by name."""
        if hasattr(self, name):
            setattr(self, name, trait)
        else:
            raise ValueError(f"Unknown trait: {name}")

    def names(self) -> list[str]:
        """Return all trait names."""
        return [f.name for f in self.__dataclass_fields__.values()]


# ---------------------------------------------------------------------------
# Seed data (input to persona generation)
# ---------------------------------------------------------------------------


@dataclass
class InterviewAnswer:
    """A single interview question/answer pair."""

    question: str
    answer: str


@dataclass
class SeedQAPair:
    """A scenario Q&A pair from the seed phase (Step 3)."""

    question: str
    answer: str


@dataclass
class SeedData:
    """All input collected during the seed phase.

    This is the input to the persona generator.
    """

    name: str
    role: str
    years_experience: int
    interview_answers: list[InterviewAnswer] = field(default_factory=list)
    qa_pairs: list[SeedQAPair] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "years_experience": self.years_experience,
            "interview_answers": [
                {"question": a.question, "answer": a.answer}
                for a in self.interview_answers
            ],
            "qa_pairs": [
                {"question": q.question, "answer": q.answer} for q in self.qa_pairs
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SeedData:
        return cls(
            name=data["name"],
            role=data["role"],
            years_experience=data["years_experience"],
            interview_answers=[
                InterviewAnswer(question=a["question"], answer=a["answer"])
                for a in data.get("interview_answers", [])
            ],
            qa_pairs=[
                SeedQAPair(question=q["question"], answer=q["answer"])
                for q in data.get("qa_pairs", [])
            ],
        )


# ---------------------------------------------------------------------------
# Core persona
# ---------------------------------------------------------------------------


def slugify(name: str) -> str:
    """Convert a name to a URL/filesystem-safe slug.

    Lowercase, hyphens, no special chars.
    """
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def utc_now() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


# Backward compat alias
_utc_now = utc_now


@dataclass
class Persona:
    """The central persona data structure.

    Stored as structured JSON; rendered to natural language only at export.

    POC fields: id, name, role, version, timestamps, identity, traits,
    values, frustrations, response_patterns, personality_quirks, biases.

    Forward-compatible (optional): decision_heuristics, tech_preferences,
    anti_patterns.
    """

    # Core identity
    id: str
    name: str
    role: str
    version: int = 1
    created_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)

    # Structured data
    identity: Identity = field(
        default_factory=lambda: Identity(
            background="", daily_workflow="", years_experience=0
        )
    )
    traits: Traits = field(
        default_factory=lambda: Traits(
            communication_tone=Trait("", ("formal", "casual")),
            technical_depth=Trait("", ("high-level", "deep-dive")),
            risk_tolerance=Trait("", ("conservative", "experimental")),
            conflict_style=Trait("", ("diplomatic", "blunt")),
            decision_making=Trait("", ("data-driven", "intuition")),
            humor=Trait("none", ("none", "frequent")),
            teaching_approach=Trait("", ("socratic", "prescriptive")),
            tool_philosophy=Trait("", ("proven", "cutting-edge")),
        )
    )

    # POC fields
    values: list[str] = field(default_factory=list)
    frustrations: list[str] = field(default_factory=list)
    biases: list[str] = field(default_factory=list)
    personality_quirks: list[str] = field(default_factory=list)
    response_patterns: ResponsePatterns = field(
        default_factory=lambda: ResponsePatterns(
            structure="", length_preference="", code_vs_prose=""
        )
    )

    # Forward-compatible optional fields (Alpha scope)
    decision_heuristics: list[str] = field(default_factory=list)
    tech_preferences: TechPreferences = field(default_factory=TechPreferences)
    anti_patterns: list[str] = field(default_factory=list)

    @classmethod
    def create(cls, name: str, role: str) -> Persona:
        """Create a new persona with generated ID and timestamps."""
        return cls(
            id=slugify(name),
            name=name,
            role=role,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "identity": self.identity.to_dict(),
            "traits": self.traits.to_dict(),
            "values": self.values,
            "frustrations": self.frustrations,
            "biases": self.biases,
            "personality_quirks": self.personality_quirks,
            "response_patterns": self.response_patterns.to_dict(),
            "decision_heuristics": self.decision_heuristics,
            "tech_preferences": self.tech_preferences.to_dict(),
            "anti_patterns": self.anti_patterns,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Persona:
        """Deserialize from a JSON-compatible dict."""
        return cls(
            id=data["id"],
            name=data["name"],
            role=data["role"],
            version=data.get("version", 1),
            created_at=data.get("created_at", _utc_now()),
            updated_at=data.get("updated_at", _utc_now()),
            identity=Identity.from_dict(data["identity"]),
            traits=Traits.from_dict(data["traits"]),
            values=data.get("values", []),
            frustrations=data.get("frustrations", []),
            biases=data.get("biases", []),
            personality_quirks=data.get("personality_quirks", []),
            response_patterns=ResponsePatterns.from_dict(data["response_patterns"]),
            decision_heuristics=data.get("decision_heuristics", []),
            tech_preferences=TechPreferences.from_dict(
                data.get("tech_preferences", {})
            ),
            anti_patterns=data.get("anti_patterns", []),
        )


# ---------------------------------------------------------------------------
# Calibration data types (used by calibrate/ and evaluation)
# ---------------------------------------------------------------------------


@dataclass
class QuestionScore:
    """4-dimension score for a single Q&A comparison."""

    content: float
    tone: float
    priorities: float
    specificity: float

    @property
    def overall(self) -> float:
        """Weighted average per EVALUATION.md."""
        from persona_forge.config import (
            CONTENT_WEIGHT,
            PRIORITIES_WEIGHT,
            SPECIFICITY_WEIGHT,
            TONE_WEIGHT,
        )

        return (
            self.content * CONTENT_WEIGHT
            + self.tone * TONE_WEIGHT
            + self.priorities * PRIORITIES_WEIGHT
            + self.specificity * SPECIFICITY_WEIGHT
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "tone": self.tone,
            "priorities": self.priorities,
            "specificity": self.specificity,
            "overall": round(self.overall, 2),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QuestionScore:
        return cls(
            content=data["content"],
            tone=data["tone"],
            priorities=data["priorities"],
            specificity=data["specificity"],
        )


@dataclass
class CalibrationQuestion:
    """A single calibration question with metadata."""

    id: str
    text: str
    category: str  # architecture, code_review, debugging, etc.
    focus_area: str  # which persona dimension this primarily tests
    difficulty: str = "standard"  # standard | adversarial

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "category": self.category,
            "focus_area": self.focus_area,
            "difficulty": self.difficulty,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CalibrationQuestion:
        return cls(
            id=data["id"],
            text=data["text"],
            category=data["category"],
            focus_area=data["focus_area"],
            difficulty=data.get("difficulty", "standard"),
        )


@dataclass
class TraitChange:
    """A proposed or applied trait change."""

    trait: str
    from_value: str
    to_value: str
    confidence: str  # high | medium | low
    rationale: str
    accepted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "trait": self.trait,
            "from": self.from_value,
            "to": self.to_value,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "accepted": self.accepted,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TraitChange:
        return cls(
            trait=data["trait"],
            from_value=data["from"],
            to_value=data["to"],
            confidence=data["confidence"],
            rationale=data["rationale"],
            accepted=data.get("accepted", False),
        )


@dataclass
class GoldenExemplar:
    """A high-scoring Q&A pair used as few-shot examples in export."""

    question: str
    human_answer: str
    persona_answer: str
    overall_score: float
    selected_at_version: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "human_answer": self.human_answer,
            "persona_answer": self.persona_answer,
            "overall_score": self.overall_score,
            "selected_at_version": self.selected_at_version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GoldenExemplar:
        return cls(
            question=data["question"],
            human_answer=data["human_answer"],
            persona_answer=data["persona_answer"],
            overall_score=data["overall_score"],
            selected_at_version=data["selected_at_version"],
        )
