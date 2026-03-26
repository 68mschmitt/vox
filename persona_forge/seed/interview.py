"""Structured interview flow for the seed phase.

POC scope: 8 hardcoded questions (mix of multiple choice and short answer)
followed by 2 LLM-generated scenario Q&A prompts.

Schema reference: design/CLI-DESIGN.md, design/PROMPTS.md
"""

from __future__ import annotations

from persona_forge.persona.model import InterviewAnswer, SeedData, SeedQAPair


# The 8 hardcoded interview questions (from CLI-DESIGN.md)
INTERVIEW_QUESTIONS: list[dict[str, str | list[str]]] = [
    {
        "text": "When a junior engineer proposes using a new framework, your default reaction is:",
        "type": "choice",
        "options": [
            "Show me the benchmarks",
            "What problem does this solve that X doesn't?",
            "Let's prototype it",
            "Here's why that's a bad idea",
        ],
    },
    {
        "text": "Describe a technical hill you'd die on (1-2 sentences):",
        "type": "freetext",
    },
    {
        "text": "When you're debugging a production issue, you start by:",
        "type": "choice",
        "options": [
            "Reading the logs",
            "Checking recent deployments",
            "Reproducing locally",
            "Asking who changed what",
        ],
    },
    {
        "text": "Your code review style is best described as:",
        "type": "choice",
        "options": [
            "Thorough -- I comment on everything",
            "Focused -- I flag blockers and skip style",
            "Mentoring -- I explain the why behind suggestions",
            "Fast -- approve if it works, comment if it doesn't",
        ],
    },
    {
        "text": 'How do you feel about "best practices"?',
        "type": "freetext",
    },
    {
        "text": "When estimating a task, you tend to:",
        "type": "choice",
        "options": [
            "Pad generously -- surprises always happen",
            "Give a tight estimate with explicit risk callouts",
            "Refuse to estimate until I've spiked it",
            "Give a range -- best case / worst case",
        ],
    },
    {
        "text": "What frustrates you most in a codebase?",
        "type": "freetext",
    },
    {
        "text": "Your go-to tool/language and why (1-2 sentences):",
        "type": "freetext",
    },
]


def run_interview(name: str, role: str, years_experience: int) -> SeedData:
    """Run the structured interview interactively.

    Stub — will be implemented in Phase 1 (POC).
    """
    raise NotImplementedError("Interview flow not yet implemented (Phase 1)")


def format_interview_answers(answers: list[InterviewAnswer]) -> str:
    """Format interview answers for use in LLM prompts."""
    lines = []
    for i, a in enumerate(answers, 1):
        lines.append(f"Q{i}: {a.question}")
        lines.append(f"A{i}: {a.answer}")
        lines.append("")
    return "\n".join(lines)


def format_qa_pairs(pairs: list[SeedQAPair]) -> str:
    """Format Q&A pairs for use in LLM prompts."""
    lines = []
    for i, p in enumerate(pairs, 1):
        lines.append(f"Q: {p.question}")
        lines.append(f"A: {p.answer}")
        lines.append("")
    return "\n".join(lines)
