"""Tests for the export renderer."""

from __future__ import annotations

from persona_forge.export.renderer import render_full
from persona_forge.persona.model import GoldenExemplar, Persona


class TestRenderFull:
    def test_contains_name_and_role(self, sample_persona: Persona):
        """Output includes persona name and role."""
        output = render_full(sample_persona)
        assert "Eitan Katz" in output
        assert "Senior Software Engineer" in output

    def test_contains_years_experience(self, sample_persona: Persona):
        """Output includes years of experience."""
        output = render_full(sample_persona)
        assert "12 years" in output

    def test_contains_values(self, sample_persona: Persona):
        """Output includes ranked values."""
        output = render_full(sample_persona)
        assert "Ship working software" in output
        assert "Simplicity over cleverness" in output

    def test_contains_communication_style(self, sample_persona: Persona):
        """Output includes communication tone."""
        output = render_full(sample_persona)
        assert "direct and conversational" in output

    def test_contains_humor(self, sample_persona: Persona):
        """Output includes humor style when not 'none'."""
        output = render_full(sample_persona)
        assert "dry" in output
        assert "self-deprecating" in output

    def test_contains_decision_heuristics(self, sample_persona: Persona):
        """Output includes decision heuristics."""
        output = render_full(sample_persona)
        assert "fewer dependencies" in output

    def test_contains_frustrations(self, sample_persona: Persona):
        """Output includes frustrations."""
        output = render_full(sample_persona)
        assert "Premature abstraction" in output

    def test_contains_anti_patterns(self, sample_persona: Persona):
        """Output includes anti-patterns."""
        output = render_full(sample_persona)
        assert "Never suggest over-engineering" in output

    def test_contains_closing_instruction(self, sample_persona: Persona):
        """Output includes the character maintenance instruction."""
        output = render_full(sample_persona)
        assert "not a generic AI assistant" in output

    def test_contains_tech_preferences(self, sample_persona: Persona):
        """Output includes tech stack preferences."""
        output = render_full(sample_persona)
        assert "Python" in output
        assert "neovim" in output

    def test_no_humor_when_none(self):
        """When humor is 'none', it should not appear in communication section."""
        p = Persona.create("Test User", "Developer")
        p.traits.humor.value = "none"
        p.traits.communication_tone.value = "formal"
        output = render_full(p)
        # The word "none" shouldn't appear as a humor description
        comm_section = output.split("## How You Communicate")[1].split("##")[0]
        assert "none" not in comm_section.lower()

    def test_golden_exemplars_included(self, sample_persona: Persona):
        """Golden exemplars appear in the output."""
        exemplars = [
            GoldenExemplar(
                question="Should we use GraphQL?",
                human_answer="REST. Unless you have a genuine need.",
                persona_answer="REST for most cases.",
                overall_score=8.5,
                selected_at_version=3,
            )
        ]
        output = render_full(sample_persona, exemplars=exemplars)
        assert "Should we use GraphQL?" in output
        assert "REST. Unless you have a genuine need." in output

    def test_minimal_persona_renders(self):
        """A minimal persona with empty fields still renders without error."""
        p = Persona.create("Minimal User", "Engineer")
        output = render_full(p)
        assert "Minimal User" in output
        assert "Engineer" in output
        # Should still have the closing instruction
        assert "not a generic AI assistant" in output

    def test_output_is_markdown(self, sample_persona: Persona):
        """Output uses markdown heading format."""
        output = render_full(sample_persona)
        assert "## Your Values" in output
        assert "## How You Communicate" in output
        assert "## Important" in output
