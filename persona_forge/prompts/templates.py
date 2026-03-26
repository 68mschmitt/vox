"""LLM prompt templates for all phases.

All prompts are centralized here. Each template is a function that accepts
structured data and returns a (system_prompt, user_prompt) tuple.
Plain f-strings, no template engine.

Schema reference: design/PROMPTS.md
"""

from __future__ import annotations

from typing import Any


def seed_interview_questions(
    name: str,
    role: str,
    years_experience: int,
    formatted_interview_answers: str,
) -> tuple[str, str]:
    """Generate follow-up Q&A questions after the structured interview.

    Returns (system_prompt, user_prompt).
    """
    system = (
        "You are a personality analyst specializing in software engineering culture. "
        "Your job is to generate scenario-based questions that reveal how a specific "
        "engineer thinks, communicates, and makes decisions."
    )

    user = f"""Based on the following interview responses from {name} ({role}, {years_experience} years):

Interview Answers:
{formatted_interview_answers}

Generate exactly 2 scenario-based questions that will reveal this person's
distinctive voice and decision-making style. The questions should:
- Be specific technical scenarios (not abstract)
- Target areas where their interview answers suggest strong opinions
- Require a 2-4 sentence answer that would reveal personality

Return as JSON:
{{
  "questions": [
    {{"text": "...", "targets": "what personality trait this question tests"}}
  ]
}}"""

    return system, user


def generate_persona_from_seed(
    name: str,
    role: str,
    formatted_interview_answers: str,
    formatted_qa_pairs: str,
    persona_schema_template: str,
) -> tuple[str, str]:
    """Create the first-draft persona from all seed input.

    Returns (system_prompt, user_prompt).
    """
    system = (
        "You are a persona architect. You create detailed, structured personality "
        "profiles for software engineers based on interview data and example responses.\n\n"
        "Your output must be precise and specific -- never generic. Every trait should "
        "be grounded in evidence from the input data."
    )

    user = f"""Create a structured persona based on the following input from {name} ({role}):

INTERVIEW RESPONSES:
{formatted_interview_answers}

EXAMPLE Q&A PAIRS:
{formatted_qa_pairs}

Generate a persona JSON that captures this person's:
- Communication style (based on how they write)
- Decision-making approach (based on what they prioritize)
- Technical biases (based on their stated preferences)
- Values (based on what they emphasize)
- Frustrations (based on what they complain about)
- Personality quirks (based on distinctive phrasing or attitudes)

The persona should feel like a specific human, not a generic engineer profile.

Return the following JSON structure:
{persona_schema_template}

IMPORTANT:
- Every field must be grounded in the interview data. Do not invent traits
  that aren't supported by the input.
- The "values" list must be ranked by importance based on emphasis in answers.
- Include at least 2 "anti_patterns" -- things this person would clearly never do.
- "decision_heuristics" should be concrete rules, not vague principles."""

    return system, user


def generate_calibration_questions(
    name: str,
    role: str,
    values: list[str],
    communication_tone: str,
    tech_preferences_summary: str,
    round_number: int,
    question_count: int,
    question_distribution_spec: str,
    weakest_dimensions: str = "",
    weakest_categories: str = "",
    previous_question_summaries: str = "",
) -> tuple[str, str]:
    """Generate questions for a calibration round.

    Returns (system_prompt, user_prompt).
    """
    system = (
        "You are a calibration question designer. You create scenario-based questions "
        "that test whether an AI persona matches a real person's voice and judgment."
    )

    context_block = ""
    if round_number > 1:
        context_block = f"""
Previous round weakest dimensions: {weakest_dimensions}
Previous round weakest question categories: {weakest_categories}
Questions already asked (do not repeat): {previous_question_summaries}
"""

    adversarial_note = ""
    if round_number >= 3:
        adversarial_note = (
            "\n- Include 1 adversarial question designed to test character "
            "consistency under pressure"
        )

    user = f"""Generate {question_count} calibration questions for the following persona:

PERSONA SUMMARY:
Name: {name}, Role: {role}
Top values: {", ".join(values[:3])}
Communication style: {communication_tone}
Tech preferences: {tech_preferences_summary}

CALIBRATION CONTEXT:
Round: {round_number}
{context_block}
QUESTION DISTRIBUTION:
{question_distribution_spec}

Requirements:
- Questions must be specific technical scenarios, not abstract
- Each question should naturally reveal personality through HOW the person answers
- Avoid yes/no questions -- require 2-5 sentence answers
- Include the scenario context (team size, tech stack, constraints) to anchor the response{adversarial_note}

Return as JSON:
{{
  "questions": [
    {{
      "id": "q{{n}}",
      "text": "...",
      "category": "architecture|code_review|debugging|conflict|tooling|tradeoff|philosophy",
      "focus_area": "which persona dimension this primarily tests",
      "difficulty": "standard|adversarial"
    }}
  ]
}}"""

    return system, user


def generate_persona_answer(
    name: str,
    role: str,
    formatted_persona_json: str,
    communication_tone: str,
    humor: str,
    decision_making: str,
    risk_tolerance: str,
    response_structure: str,
    question_text: str,
    golden_exemplars: list[dict[str, str]] | None = None,
) -> tuple[str, str]:
    """Generate a persona's in-character answer to a question.

    Returns (system_prompt, user_prompt).
    """
    exemplar_block = ""
    if golden_exemplars:
        exemplar_block = "\nEXAMPLES OF YOUR VOICE:\n"
        for ex in golden_exemplars[:3]:
            exemplar_block += f"Q: {ex['question']}\nA: {ex['human_answer']}\n\n"

    system = f"""You are {name}, a {role}. You must answer the following question exactly as
this person would -- matching their voice, priorities, and decision-making style.

PERSONA PROFILE:
{formatted_persona_json}

KEY TRAITS TO EMBODY:
- Communication: {communication_tone}
- Humor: {humor}
- Decision style: {decision_making}
- Risk tolerance: {risk_tolerance}
- Response pattern: {response_structure}
{exemplar_block}
IMPORTANT:
- Stay in character completely. You ARE this person.
- Match the length and detail level shown in the examples.
- Let biases and strong opinions show. Do not hedge unless {name} would hedge.
- Use the same register (formal/casual) as the examples.
- Do NOT start with "As {name}" or break the fourth wall."""

    return system, question_text


def evaluate_divergence(
    question_text: str,
    human_answer: str,
    persona_answer: str,
) -> tuple[str, str]:
    """Score a persona answer against the human's answer.

    Returns (system_prompt, user_prompt).
    """
    system = (
        "You are an expert writing analyst specializing in voice matching and "
        "personality consistency. You are STRICT -- do not give generous scores. "
        'A 7 means "noticeably similar." An 8 means "very hard to tell apart." '
        'A 10 means "indistinguishable." Most comparisons should score 4-7.'
    )

    user = f"""Compare these two answers to the same question. ANSWER A is the reference
(ground truth). ANSWER B is being evaluated against it.

QUESTION: {question_text}

ANSWER A (reference):
{human_answer}

ANSWER B (evaluate this):
{persona_answer}

Score ANSWER B on these 4 dimensions (1-10 each):

1. CONTENT: Does B reach the same conclusions and recommendations as A?
   - 1-3: Fundamentally different recommendation
   - 4-6: Same direction, different specifics
   - 7-8: Nearly identical technical content
   - 9-10: Indistinguishable content

2. TONE: Does B sound like the same person as A?
   - 1-3: Completely different voice
   - 4-6: Similar register, different personality
   - 7-8: Consistent voice with minor tells
   - 9-10: Indistinguishable voice

3. PRIORITIES: Does B emphasize the same things as A?
   - 1-3: Different primary concern
   - 4-6: Same concerns, different ordering
   - 7-8: Nearly identical priority structure
   - 9-10: Identical emphasis

4. SPECIFICITY: Does B match A's level of detail?
   - 1-3: Vastly different detail level
   - 4-6: Similar scope, different depth
   - 7-8: Matching depth with different examples
   - 9-10: Indistinguishable specificity

IMPORTANT:
- Be STRICT. Most real comparisons score in the 4-7 range.
- A score of 8+ should be rare and only when the similarity is striking.
- Do NOT round up. If it's between 6 and 7, give 6.
- Identify the specific trait that would need to change to close each gap.

Return as JSON:
{{
  "content": {{"score": N, "gap": "...", "trait_signal": "..."}},
  "tone": {{"score": N, "gap": "...", "trait_signal": "..."}},
  "priorities": {{"score": N, "gap": "...", "trait_signal": "..."}},
  "specificity": {{"score": N, "gap": "...", "trait_signal": "..."}}
}}"""

    return system, user


def propose_trait_changes(
    formatted_persona_json: str,
    formatted_divergence_report: str,
    formatted_trait_change_log: str,
    max_changes: int,
    lookback: int,
) -> tuple[str, str]:
    """Generate trait mutation proposals based on the divergence report.

    Returns (system_prompt, user_prompt).
    """
    system = (
        "You are a persona calibration engineer. You analyze divergence between "
        "a persona's answers and a human's answers, then propose specific, "
        "targeted trait changes to close the gap.\n\n"
        "You must be SURGICAL -- change only what the evidence supports. "
        "Do not propose changes to traits that scored well."
    )

    user = f"""CURRENT PERSONA:
{formatted_persona_json}

DIVERGENCE REPORT:
{formatted_divergence_report}

TRAIT CHANGE HISTORY (last {lookback} versions):
{formatted_trait_change_log}

CONSTRAINTS:
- Maximum {max_changes} trait changes this round
- Do NOT propose changes to traits that scored >= 8.0 on their primary dimension
- Do NOT propose changes that reverse a change made in the last 2 versions
  (oscillation detected -- suggest splitting the trait instead)
- If a trait needs to move in different directions for different contexts,
  propose a NEW context-specific trait instead of changing the existing one

For each proposed change, provide:
1. The trait name
2. Current value
3. Proposed new value
4. Confidence (high/medium/low) based on how many questions support this change
5. Specific evidence (which question answers demonstrate this gap)
6. Rationale (why this change will improve alignment)

Return as JSON:
{{
  "changes": [
    {{
      "trait": "...",
      "from": "...",
      "to": "...",
      "confidence": "high|medium|low",
      "evidence_questions": ["q1", "q3"],
      "rationale": "..."
    }}
  ],
  "no_change_traits": ["trait names that are working well"],
  "new_trait_proposals": [
    {{
      "name": "...",
      "value": "...",
      "rationale": "...",
      "replaces": "existing trait name, if splitting"
    }}
  ]
}}"""

    return system, user


def get_persona_schema_template() -> str:
    """Return the JSON schema template for persona generation prompts."""
    return """{
  "id": "string (slug)",
  "name": "string",
  "role": "string",
  "identity": {
    "background": "string (2-3 sentences)",
    "daily_workflow": "string",
    "years_experience": integer
  },
  "traits": {
    "communication_tone": {"value": "string", "spectrum": ["formal", "casual"], "calibrated": false},
    "technical_depth": {"value": "string", "spectrum": ["high-level", "deep-dive"], "calibrated": false},
    "risk_tolerance": {"value": "string", "spectrum": ["conservative", "experimental"], "calibrated": false},
    "conflict_style": {"value": "string", "spectrum": ["diplomatic", "blunt"], "calibrated": false},
    "decision_making": {"value": "string", "spectrum": ["data-driven", "intuition"], "calibrated": false},
    "humor": {"value": "string or 'none'", "spectrum": ["none", "frequent"], "calibrated": false},
    "teaching_approach": {"value": "string", "spectrum": ["socratic", "prescriptive"], "calibrated": false},
    "tool_philosophy": {"value": "string", "spectrum": ["proven", "cutting-edge"], "calibrated": false}
  },
  "decision_heuristics": ["string (concrete rules)"],
  "tech_preferences": {
    "languages": ["string"],
    "frameworks": ["string"],
    "tools": ["string"],
    "philosophy": "string"
  },
  "values": ["string (ranked, most important first)"],
  "frustrations": ["string"],
  "biases": ["string"],
  "personality_quirks": ["string (2-3 specific behaviors)"],
  "response_patterns": {
    "structure": "string",
    "length_preference": "string",
    "code_vs_prose": "string"
  },
  "anti_patterns": ["string (things this persona would NEVER do)"]
}"""
