"""Calibration loop orchestration.

POC scope: single-round calibration only.
- Generate 6 broad coverage questions
- Collect human answers
- Generate persona answers + evaluate divergence
- Propose trait changes via LLM
- Human accepts/rejects each change
- Save updated persona

Alpha: multi-round with convergence and stall detection.

Schema reference: design/CALIBRATION-LOOP.md
"""

from __future__ import annotations

import json
from copy import deepcopy

from persona_forge.calibrate.evaluator import (
    DivergenceReport,
    EvaluationResult,
    evaluate_answer,
    generate_persona_answer_text,
)
from persona_forge.calibrate.questions import generate_questions
from persona_forge.config import (
    MAX_TRAIT_CHANGES_PER_ROUND,
    OSCILLATION_LOOKBACK,
    QUESTIONS_PER_ROUND,
)
from persona_forge.llm.parse import extract_json, generate_with_retry
from persona_forge.llm.provider import LLMProvider
from persona_forge.persona.model import (
    Persona,
    Trait,
    TraitChange,
    utc_now,
)
from persona_forge.persona.store import save_persona
from persona_forge.prompts.templates import propose_trait_changes
from persona_forge.ui.display import (
    dim,
    divider,
    error,
    header,
    info,
    prompt,
    prompt_choice,
    score_display,
    success,
    warning,
)


def _collect_human_answers(
    questions: list,
) -> dict[str, str]:
    """Collect human answers for each calibration question.

    Returns a dict of question_id -> answer text.
    Allows skipping with 'skip'.
    """
    answers: dict[str, str] = {}

    for i, q in enumerate(questions, 1):
        info(f"\nQuestion {i}/{len(questions)} [{q.category}]")
        info(q.text)

        answer = prompt("\nYour answer (or 'skip'):")
        while not answer:
            answer = prompt("Please provide an answer (or 'skip'):")

        if answer.lower() == "skip":
            dim("  (skipped)")
            continue

        answers[q.id] = answer

    return answers


def _evaluate_round(
    persona: Persona,
    questions: list,
    human_answers: dict[str, str],
    provider: LLMProvider,
) -> DivergenceReport:
    """Generate persona answers, evaluate divergence, build report."""
    results: list[EvaluationResult] = []

    for q in questions:
        if q.id not in human_answers:
            continue  # skipped question

        dim(f"\n  Evaluating [{q.category}]...")

        # Generate persona's answer
        persona_answer = generate_persona_answer_text(persona, q.text, provider)

        # Score the divergence
        scores = evaluate_answer(
            question_text=q.text,
            human_answer=human_answers[q.id],
            persona_answer=persona_answer,
            provider=provider,
        )

        results.append(
            EvaluationResult(
                question_id=q.id,
                question_text=q.text,
                category=q.category,
                human_answer=human_answers[q.id],
                persona_answer=persona_answer,
                scores=scores,
            )
        )

    return DivergenceReport(results=results)


def _display_results(report: DivergenceReport) -> None:
    """Display the divergence report to the user."""
    header("Results")

    for r in report.results:
        info(
            f"  {r.question_id.upper()} {r.category:15s}  "
            f"Content {r.scores.content:.0f} | "
            f"Tone {r.scores.tone:.0f} | "
            f"Priorities {r.scores.priorities:.0f} | "
            f"Specificity {r.scores.specificity:.0f}"
        )

    divider()
    avgs = report.dimension_averages
    info(f"\n  Overall: {report.overall_score:.1f} / 10")
    info(
        f"  Weakest:  {report.weakest_dimension} ({avgs[report.weakest_dimension]:.1f} avg)"
    )
    info(
        f"  Strongest: {report.strongest_dimension} ({avgs[report.strongest_dimension]:.1f} avg)"
    )


def _propose_and_apply_changes(
    persona: Persona,
    report: DivergenceReport,
    provider: LLMProvider,
    base_dir=None,
) -> Persona:
    """Propose trait changes via LLM, let user accept/reject each one.

    Returns the updated persona (new version if changes were accepted).
    """
    header("Proposed Changes")
    dim("Analyzing divergence and proposing trait adjustments...")

    persona_json = json.dumps(persona.to_dict(), indent=2)
    divergence_text = report.format_for_prompt()

    system_prompt, user_prompt = propose_trait_changes(
        formatted_persona_json=persona_json,
        formatted_divergence_report=divergence_text,
        # TODO(Alpha): Pass actual trait_change_log from persona state.
        # Currently hardcoded for POC single-round. When multi-round is added,
        # the log needs to come from the versioned state file so the LLM can
        # detect oscillation and avoid reversing recent changes.
        formatted_trait_change_log="(No previous changes -- this is the first calibration round)",
        max_changes=MAX_TRAIT_CHANGES_PER_ROUND,
        lookback=OSCILLATION_LOOKBACK,
    )

    raw_response = generate_with_retry(
        provider, system_prompt, user_prompt, temperature=0.5
    )
    data = extract_json(raw_response)

    changes_data = data.get("changes", [])
    if not changes_data:
        info("\nNo trait changes proposed. The persona may already be well-aligned,")
        info("or the divergence didn't suggest clear adjustments.")
        return persona

    # Parse and present each change
    accepted_changes: list[TraitChange] = []
    info("")

    for i, c in enumerate(changes_data, 1):
        trait_name = c.get("trait", "unknown")
        from_val = c.get("from", "")
        to_val = c.get("to", "")
        confidence = c.get("confidence", "medium").upper()
        rationale = c.get("rationale", "")

        info(f'  {i}. {trait_name}: "{from_val}" -> "{to_val}"')
        info(f"     Confidence: {confidence}")
        info(f"     Rationale: {rationale}")

        choice = prompt_choice(
            "     Action:",
            ["Accept", "Reject", "Edit"],
        )

        if choice == "Accept":
            accepted_changes.append(
                TraitChange(
                    trait=trait_name,
                    from_value=from_val,
                    to_value=to_val,
                    confidence=c.get("confidence", "medium"),
                    rationale=rationale,
                    accepted=True,
                )
            )
            success(f"     Accepted.")
        elif choice == "Edit":
            new_val = prompt(f"     New value for {trait_name}:")
            if new_val:
                accepted_changes.append(
                    TraitChange(
                        trait=trait_name,
                        from_value=from_val,
                        to_value=new_val,
                        confidence=c.get("confidence", "medium"),
                        rationale=f"(Edited by user) {rationale}",
                        accepted=True,
                    )
                )
                success(f"     Accepted (edited).")
            else:
                dim(f"     Rejected (no value provided).")
        else:
            dim(f"     Rejected.")
        info("")

    if not accepted_changes:
        info("No changes accepted. Persona unchanged.")
        return persona

    # Apply changes to persona
    updated = deepcopy(persona)
    updated.version += 1
    updated.updated_at = utc_now()

    for change in accepted_changes:
        trait = updated.traits.get(change.trait)
        if trait is not None:
            trait.value = change.to_value
            trait.calibrated = True
        elif change.trait == "response_patterns.structure":
            updated.response_patterns.structure = change.to_value
        elif change.trait == "response_patterns.length_preference":
            updated.response_patterns.length_preference = change.to_value
        elif change.trait == "response_patterns.code_vs_prose":
            updated.response_patterns.code_vs_prose = change.to_value
        else:
            warning(f"Unknown trait '{change.trait}' -- skipping.")

    info(f"\nApplied {len(accepted_changes)} changes -> Persona v{updated.version}")

    # Save updated persona
    save_path = save_persona(updated, base_dir=base_dir)
    success(f"Saved to: {save_path}")

    return updated


def run_calibration(
    persona: Persona,
    provider: LLMProvider,
    max_rounds: int = 1,
    base_dir=None,
) -> Persona:
    """Run the calibration loop on a persona.

    POC: single round only.
    1. Generate 6 broad coverage questions
    2. Collect human answers
    3. Generate persona answers + evaluate divergence
    4. Display divergence report
    5. Propose trait changes, human accepts/rejects
    6. Save updated persona

    Args:
        persona: The persona to calibrate.
        provider: LLM provider.
        max_rounds: Maximum calibration rounds (1 for POC).
        base_dir: Optional storage directory override.

    Returns:
        The (possibly updated) persona.
    """
    info(f"Loading persona: {persona.name} (v{persona.version})")
    info("Starting calibration session.\n")

    header(f"Round 1 of {max_rounds} -- Broad Coverage")

    # Step 1: Generate questions
    questions = generate_questions(persona, provider, round_number=1)

    # Step 2: Collect human answers
    header("Answer the following questions as you naturally would")
    human_answers = _collect_human_answers(questions)

    if not human_answers:
        warning("No questions answered. Calibration requires at least 1 answer.")
        return persona

    # Step 3-4: Evaluate divergence
    header("Evaluating")
    dim("Generating persona answers and scoring divergence...")
    report = _evaluate_round(persona, questions, human_answers, provider)

    # Display results
    _display_results(report)

    # Step 5-6: Propose and apply trait changes
    updated = _propose_and_apply_changes(persona, report, provider, base_dir=base_dir)

    divider()
    info(f"\nCalibration round complete. Persona is now v{updated.version}.")
    info(
        f"Next step: Run `persona-forge export {updated.id}` to render as system prompt."
    )

    return updated
