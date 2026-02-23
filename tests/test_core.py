"""Smoke tests for sim_core — loading, data integrity, report generation."""

import json
from pathlib import Path

import pytest

from sim_core import (
    ALL_CATEGORIES,
    APF_CATEGORIES,
    GEN_CATEGORIES,
    SCENARIOS_DIR,
    RunResult,
    Scenario,
    generate_json_report,
    generate_markdown_report,
    load_manifest,
    load_scenarios,
)


# --- Loading ---


def test_load_manifest():
    manifest = load_manifest()
    assert isinstance(manifest, dict)
    assert len(manifest) > 0
    for name, info in manifest.items():
        assert "path" in info, f"Skill '{name}' missing 'path'"
        assert "category" in info, f"Skill '{name}' missing 'category'"


def test_load_scenarios():
    scenarios = load_scenarios()
    assert len(scenarios) > 0
    for s in scenarios:
        assert isinstance(s, Scenario)
        assert s.id
        assert s.name
        assert s.prompt
        assert s.target_skill


def test_scenario_ids_unique():
    scenarios = load_scenarios()
    ids = [s.id for s in scenarios]
    assert len(ids) == len(set(ids)), (
        f"Duplicate IDs: {[x for x in ids if ids.count(x) > 1]}"
    )


def test_all_scenario_skills_in_manifest():
    manifest = load_manifest()
    scenarios = load_scenarios()
    for s in scenarios:
        assert s.target_skill in manifest, (
            f"Scenario '{s.id}' references skill '{s.target_skill}' not in manifest"
        )


# --- Taxonomy integrity ---


def test_gen_categories_structure():
    assert len(GEN_CATEGORIES) == 13
    for cat_id, cat in GEN_CATEGORIES.items():
        assert cat_id.startswith("GEN-")
        assert "name" in cat
        assert "severity" in cat
        assert cat["severity"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")


def test_apf_categories_structure():
    assert len(APF_CATEGORIES) == 11
    for cat_id, cat in APF_CATEGORIES.items():
        assert cat_id.startswith("APF-")
        assert "name" in cat
        assert "severity" in cat
        assert cat["severity"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")


def test_expected_complexities_valid():
    scenarios = load_scenarios()
    for s in scenarios:
        for c in s.expected_complexities:
            assert c in ALL_CATEGORIES, (
                f"Scenario '{s.id}' references unknown category '{c}'"
            )


# --- Report generation ---


@pytest.fixture
def sample_data():
    scenarios = [
        Scenario(
            id="test-1",
            name="Test scenario",
            prompt="Test prompt",
            target_skill="apify-ultimate-scraper",
            expected_complexities=["GEN-1", "APF-1"],
            source_file="test.yaml",
        )
    ]
    results = [
        RunResult(
            scenario_id="test-1",
            model="haiku",
            response="## Approach\nTest response",
            duration_s=1.5,
            cost_info="input=100, output=200",
        )
    ]
    models = ["haiku"]
    return scenarios, results, models


def test_generate_markdown_report(sample_data):
    scenarios, results, models = sample_data
    md = generate_markdown_report(scenarios, results, models)
    assert "# Skill Checker Report" in md
    assert "test-1" in md
    assert "haiku" in md
    assert "Test response" in md


def test_generate_json_report(sample_data):
    scenarios, results, models = sample_data
    report = generate_json_report(scenarios, results, models)
    assert report["scenario_count"] == 1
    assert report["models"] == ["haiku"]
    assert len(report["results"]) == 1
    # Verify it's JSON-serializable
    json.dumps(report)


def test_generate_json_report_with_error():
    scenarios = [
        Scenario(
            id="err-1",
            name="Error scenario",
            prompt="Fail prompt",
            target_skill="apify-ultimate-scraper",
            expected_complexities=[],
            source_file="test.yaml",
        )
    ]
    results = [
        RunResult(
            scenario_id="err-1",
            model="sonnet",
            response="",
            duration_s=0,
            cost_info="",
            error="Connection failed",
        )
    ]
    report = generate_json_report(scenarios, results, ["sonnet"])
    assert report["results"][0]["models"]["sonnet"]["error"] == "Connection failed"
