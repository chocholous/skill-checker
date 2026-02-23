"""Tests for the BP (Best Practices) static linter."""

import pytest

from bp_linter import (
    BPCheckResult,
    run_bp_checks,
    bp_checks_to_run_results,
    _check_bp1_token_budget,
    _check_bp2_poor_description,
    _check_bp3_deep_nesting,
    _check_bp5_no_progressive_disclosure,
    _check_bp6_magic_constants,
    _check_bp8_when_to_read,
)


# --- BP-1: Token budget ---


def test_bp1_short_file():
    content = "# Short skill\nDo something.\n" * 10
    result = _check_bp1_token_budget(content)
    assert not result.triggered
    assert result.check_id == "BP-1"


def test_bp1_long_file():
    content = "Line of instructions\n" * 600
    result = _check_bp1_token_budget(content)
    assert result.triggered
    assert "600" in result.detail


# --- BP-2: Poor description ---


def test_bp2_with_frontmatter():
    content = "---\ndescription: This skill does X\ntrigger: when user asks\n---\n# Skill\nContent"
    result = _check_bp2_poor_description(content)
    assert not result.triggered


def test_bp2_no_frontmatter():
    content = "# Skill\nJust do stuff without any description."
    result = _check_bp2_poor_description(content)
    assert result.triggered
    assert "no YAML frontmatter" in result.detail


def test_bp2_with_description_section():
    content = "# Skill\n## Description\nThis skill handles X when user asks about Y.\n"
    result = _check_bp2_poor_description(content)
    assert not result.triggered


# --- BP-3: Deep nesting ---


def test_bp3_no_nesting():
    content = "Read references/api-docs.md for details."
    result = _check_bp3_deep_nesting(content)
    assert not result.triggered


def test_bp3_deep_nesting():
    content = "Read references/sub/references/deep.md for details."
    result = _check_bp3_deep_nesting(content)
    assert result.triggered


# --- BP-5: No progressive disclosure ---


def test_bp5_short_file():
    content = "# Short\n" * 50
    result = _check_bp5_no_progressive_disclosure(content)
    assert not result.triggered


def test_bp5_long_no_refs():
    content = "Step by step instructions.\n" * 150
    result = _check_bp5_no_progressive_disclosure(content)
    assert result.triggered


def test_bp5_long_with_refs():
    content = "Step by step.\n" * 150 + "\nSee references/details.md for more."
    result = _check_bp5_no_progressive_disclosure(content)
    assert not result.triggered


# --- BP-6: Magic constants ---


def test_bp6_no_magic():
    content = "# Skill\nRun the actor with default settings."
    result = _check_bp6_magic_constants(content)
    assert not result.triggered


def test_bp6_many_magic():
    content = "timeout: 30\nlimit: 100\nmax: 500\nretry: 3\nconcurrency: 5"
    result = _check_bp6_magic_constants(content)
    assert result.triggered


# --- BP-8: When to read ---


def test_bp8_no_references():
    content = "# Skill\nNo references here."
    result = _check_bp8_when_to_read(content)
    assert not result.triggered


def test_bp8_references_with_guidance():
    content = "When configuring proxy, read references/proxy-guide.md\nAlso check references/actors.md"
    result = _check_bp8_when_to_read(content)
    assert not result.triggered


def test_bp8_references_without_guidance():
    content = "references/file1.md\nreferences/file2.md\nreferences/file3.md"
    result = _check_bp8_when_to_read(content)
    assert result.triggered


# --- Integration ---


def test_run_bp_checks_returns_8():
    content = "# Simple Skill\nDo X.\n"
    results = run_bp_checks(content, "test-skill")
    assert len(results) == 8
    assert all(isinstance(r, BPCheckResult) for r in results)
    check_ids = [r.check_id for r in results]
    assert check_ids == ["BP-1", "BP-2", "BP-3", "BP-4", "BP-5", "BP-6", "BP-7", "BP-8"]


def test_bp_checks_to_run_results():
    content = "# Skill\n## Description\nHandles X.\n"
    checks = run_bp_checks(content, "my-skill")
    results = bp_checks_to_run_results(checks, "my-skill")
    assert len(results) == 1
    assert results[0].model == "bp-linter"
    assert results[0].scenario_id == "bp-my-skill"
    assert results[0].cost_info == "static analysis (no API call)"
    assert results[0].error is None
