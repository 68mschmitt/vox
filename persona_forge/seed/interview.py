"""Structured interview flow for the seed phase.

POC scope: 8 hardcoded questions (mix of multiple choice and short answer)
followed by 2 LLM-generated scenario Q&A prompts.

Schema reference: design/CLI-DESIGN.md, design/PROMPTS.md
"""

from __future__ import annotations

from persona_forge.llm.provider import LLMProvider
from persona_forge.llm.parse import extract_json, generate_with_retry
from persona_forge.persona.model import InterviewAnswer, SeedData, SeedQAPair
from persona_forge.prompts.templates import seed_interview_questions
from persona_forge.config import SEED_FOLLOWUP_QUESTION_COUNT
from persona_forge.ui.display import header, info, dim, prompt, prompt_choice


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


def _collect_profile() -> tuple[str, str, int]:
    """Collect basic profile info: name, role, years of experience."""
    header("Step 1/3: Quick Profile")

    name = prompt("What's the persona's name?")
    while not name:
        name = prompt("Name cannot be empty. What's the persona's name?")

    role = prompt(
        "What's their role? (e.g., Senior Software Engineer, Staff Backend Engineer)"
    )
    while not role:
        role = prompt("Role cannot be empty. What's their role?")

    years_str = prompt("Years of experience?")
    while True:
        try:
            years = int(years_str)
            if years < 0:
                raise ValueError
            break
        except ValueError:
            years_str = prompt("Please enter a valid number for years of experience:")

    return name, role, years


def _run_structured_interview() -> list[InterviewAnswer]:
    """Run the 8 hardcoded interview questions."""
    header(f"Step 2/3: Structured Interview ({len(INTERVIEW_QUESTIONS)} questions)")

    answers: list[InterviewAnswer] = []
    for i, q in enumerate(INTERVIEW_QUESTIONS, 1):
        question_text = q["text"]
        assert isinstance(question_text, str)
        info(f"\nQ{i}: {question_text}")

        if q["type"] == "choice":
            options = q["options"]
            assert isinstance(options, list)
            answer = prompt_choice("", options)
        else:
            answer = prompt(">")
            while not answer:
                answer = prompt("Please provide an answer (or type 'skip' to skip):")
            if answer.lower() == "skip":
                answer = "(skipped)"

        answers.append(InterviewAnswer(question=question_text, answer=answer))

    return answers


def _run_followup_qa(
    name: str,
    role: str,
    years_experience: int,
    interview_answers: list[InterviewAnswer],
    provider: LLMProvider,
) -> list[SeedQAPair]:
    """Generate and collect follow-up Q&A pairs using the LLM."""
    header("Step 3/3: Example Q&A (2 questions generated from your answers)")
    info(
        "Based on your answers, here are scenario questions. Answer as you naturally would.\n"
    )

    formatted = format_interview_answers(interview_answers)
    system_prompt, user_prompt = seed_interview_questions(
        name=name,
        role=role,
        years_experience=years_experience,
        formatted_interview_answers=formatted,
    )

    dim("Generating follow-up questions...")
    raw_response = generate_with_retry(
        provider, system_prompt, user_prompt, temperature=0.7
    )
    data = extract_json(raw_response)

    questions = data.get("questions", [])
    if not questions:
        # Fallback: use hardcoded questions if LLM fails
        questions = [
            {
                "text": (
                    "A teammate proposes adding a dependency injection framework "
                    "to your Python service. What do you say?"
                ),
            },
            {
                "text": (
                    "You're asked to choose between PostgreSQL and DynamoDB for "
                    "a new service. How do you decide?"
                ),
            },
        ]

    qa_pairs: list[SeedQAPair] = []
    for q in questions[:SEED_FOLLOWUP_QUESTION_COUNT]:
        q_text = q["text"]
        info(f"\nQ: {q_text}")
        answer = prompt(">")
        while not answer:
            answer = prompt("Please provide an answer:")
        qa_pairs.append(SeedQAPair(question=q_text, answer=answer))

    return qa_pairs


def run_interview(
    provider: LLMProvider,
    name: str | None = None,
    role: str | None = None,
) -> SeedData:
    """Run the full structured interview interactively.

    Collects profile info, runs 8 hardcoded questions, then generates
    2 follow-up Q&A scenario questions via the LLM.

    Args:
        provider: LLM provider for generating follow-up questions.
        name: Optional pre-filled name (from --name flag).
        role: Optional pre-filled role.

    Returns:
        SeedData with all collected input.
    """
    info("Creating a new persona. This will take about 15 minutes.\n")

    if name and role:
        # If both provided via flags, skip profile collection
        years_str = prompt("Years of experience?")
        while True:
            try:
                years_experience = int(years_str)
                if years_experience < 0:
                    raise ValueError
                break
            except ValueError:
                years_str = prompt("Please enter a valid number:")
    elif name:
        header("Step 1/3: Quick Profile")
        info(f"Name: {name}")
        role = prompt("What's their role? (e.g., Senior Software Engineer)")
        while not role:
            role = prompt("Role cannot be empty:")
        years_str = prompt("Years of experience?")
        while True:
            try:
                years_experience = int(years_str)
                if years_experience < 0:
                    raise ValueError
                break
            except ValueError:
                years_str = prompt("Please enter a valid number:")
    else:
        name, role, years_experience = _collect_profile()

    interview_answers = _run_structured_interview()

    qa_pairs = _run_followup_qa(
        name=name,
        role=role,
        years_experience=years_experience,
        interview_answers=interview_answers,
        provider=provider,
    )

    return SeedData(
        name=name,
        role=role,
        years_experience=years_experience,
        interview_answers=interview_answers,
        qa_pairs=qa_pairs,
    )


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
