"""Smoke tests for sim_core — loading, data integrity, report generation."""

import json
from pathlib import Path

import pytest

from sim_core import (
    ALL_CATEGORIES,
    APF_CATEGORIES,
    BP_CATEGORIES,
    CATEGORY_GROUPS,
    DEV_DOMAINS,
    DEV_EXCLUDED_CHECKS,
    DK_CATEGORIES,
    DOMAIN_SKILL_MAP,
    LLM_CHECK_IDS,
    SCENARIOS_DIR,
    SEC_CATEGORIES,
    WF_CATEGORIES,
    CheckResult,
    RunResult,
    Scenario,
    ScoredRun,
    generate_json_report,
    generate_markdown_report,
    get_category_type,
    get_scenario_models,
    get_target_skills,
    load_all_scored_reports,
    load_domain_scenarios,
    load_manifest,
    load_scored_report,
    load_scenarios,
    parse_scoring_response,
    save_scored_report_incremental,
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


# --- 5-Category Taxonomy integrity ---


def test_wf_categories_structure():
    assert len(WF_CATEGORIES) == 6
    for cat_id, cat in WF_CATEGORIES.items():
        assert cat_id.startswith("WF-")
        assert "name" in cat
        assert "severity" in cat
        assert cat["severity"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")


def test_dk_categories_structure():
    assert len(DK_CATEGORIES) == 8
    for cat_id, cat in DK_CATEGORIES.items():
        assert cat_id.startswith("DK-")
        assert "name" in cat
        assert "severity" in cat
        assert cat["severity"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")


def test_bp_categories_structure():
    assert len(BP_CATEGORIES) == 8
    for cat_id, cat in BP_CATEGORIES.items():
        assert cat_id.startswith("BP-")
        assert "name" in cat
        assert "severity" in cat
        assert cat["severity"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")


def test_apf_categories_structure():
    assert len(APF_CATEGORIES) == 13
    for cat_id, cat in APF_CATEGORIES.items():
        assert cat_id.startswith("APF-")
        assert "name" in cat
        assert "severity" in cat
        assert cat["severity"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")


def test_sec_categories_structure():
    assert len(SEC_CATEGORIES) == 2
    for cat_id, cat in SEC_CATEGORIES.items():
        assert cat_id.startswith("SEC-")
        assert "name" in cat
        assert "severity" in cat
        assert cat["severity"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")


def test_all_categories_total():
    assert len(ALL_CATEGORIES) == 37


def test_category_groups():
    assert set(CATEGORY_GROUPS.keys()) == {"WF", "DK", "BP", "APF", "SEC"}
    for group_key, group in CATEGORY_GROUPS.items():
        assert "name" in group
        assert "default_models" in group
        assert "categories" in group
        assert isinstance(group["default_models"], list)
        assert len(group["default_models"]) > 0
        # All categories in group have correct prefix
        for cat_id in group["categories"]:
            assert cat_id.startswith(f"{group_key}-"), (
                f"Category '{cat_id}' in group '{group_key}' has wrong prefix"
            )


def test_get_category_type():
    assert get_category_type("WF-1") == "WF"
    assert get_category_type("DK-3") == "DK"
    assert get_category_type("BP-1") == "BP"
    assert get_category_type("APF-11") == "APF"
    assert get_category_type("SEC-1") == "SEC"
    assert get_category_type("UNKNOWN-99") == "UNKNOWN"


# --- get_scenario_models ---


def test_get_scenario_models_cli_override():
    s = Scenario(
        id="t",
        name="t",
        prompt="p",
        target_skill="s",
        source_file="t.yaml",
        category="WF",
    )
    assert get_scenario_models(s, cli_override=["haiku"]) == ["haiku"]


def test_get_scenario_models_scenario_override():
    s = Scenario(
        id="t",
        name="t",
        prompt="p",
        target_skill="s",
        source_file="t.yaml",
        category="WF",
        models=["opus"],
    )
    assert get_scenario_models(s) == ["opus"]


def test_get_scenario_models_category_default():
    s = Scenario(
        id="t",
        name="t",
        prompt="p",
        target_skill="s",
        source_file="t.yaml",
        category="WF",
    )
    assert get_scenario_models(s) == ["sonnet"]


def test_get_scenario_models_dk_default():
    s = Scenario(
        id="t",
        name="t",
        prompt="p",
        target_skill="s",
        source_file="t.yaml",
        category="DK",
    )
    assert get_scenario_models(s) == ["sonnet", "opus", "haiku"]


# --- Report generation ---


@pytest.fixture
def sample_data():
    scenarios = [
        Scenario(
            id="test-1",
            name="Test scenario",
            prompt="Test prompt",
            target_skill="apify-ultimate-scraper",
            source_file="test.yaml",
            category="WF",
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
    assert "Prompt" in md


def test_generate_json_report(sample_data):
    scenarios, results, models = sample_data
    report = generate_json_report(scenarios, results, models)
    assert report["scenario_count"] == 1
    assert report["models"] == ["haiku"]
    assert len(report["results"]) == 1
    assert "category" in report["results"][0]
    # Verify it's JSON-serializable
    json.dumps(report)


def test_generate_json_report_with_error():
    scenarios = [
        Scenario(
            id="err-1",
            name="Error scenario",
            prompt="Fail prompt",
            target_skill="apify-ultimate-scraper",
            source_file="test.yaml",
            category="APF",
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


# --- Domain / Heatmap constants ---


def test_domain_skill_map():
    # Map is now built dynamically from YAML files
    assert len(DOMAIN_SKILL_MAP) == 12
    for domain_id, skill_name in DOMAIN_SKILL_MAP.items():
        assert isinstance(domain_id, str)
        assert isinstance(skill_name, str)
        assert skill_name.startswith("apify-")
    # Verify specific mappings survived the migration
    assert (
        DOMAIN_SKILL_MAP["competitive-intelligence"] == "apify-competitor-intelligence"
    )
    assert DOMAIN_SKILL_MAP["actor-development"] == "apify-actor-development"
    assert DOMAIN_SKILL_MAP["ecommerce"] == "apify-ecommerce"


def test_dev_domains():
    # DEV_DOMAINS is now built dynamically from manifest category='dev'
    assert "actor-development" in DEV_DOMAINS
    assert "actorization" in DEV_DOMAINS
    assert len(DEV_DOMAINS) == 2
    # All dev domains must exist in DOMAIN_SKILL_MAP
    for d in DEV_DOMAINS:
        assert d in DOMAIN_SKILL_MAP


def test_dev_excluded_checks():
    assert len(DEV_EXCLUDED_CHECKS) == 10
    for check_id in DEV_EXCLUDED_CHECKS:
        assert check_id in ALL_CATEGORIES, (
            f"DEV_EXCLUDED_CHECKS has unknown '{check_id}'"
        )
        # None should be BP
        assert not check_id.startswith("BP-")


def test_llm_check_ids():
    assert len(LLM_CHECK_IDS) == 29
    for check_id in LLM_CHECK_IDS:
        assert not check_id.startswith("BP-"), f"LLM check '{check_id}' is BP"
        assert check_id in ALL_CATEGORIES, f"LLM check '{check_id}' unknown"


# --- Domain scenarios ---


def test_load_domain_scenarios():
    ds = load_domain_scenarios()
    assert len(ds) > 0
    for domain_id, scenarios in ds.items():
        assert domain_id in DOMAIN_SKILL_MAP, (
            f"Domain '{domain_id}' not in DOMAIN_SKILL_MAP"
        )
        assert len(scenarios) > 0
        for s in scenarios:
            assert s.domain == domain_id
            assert s.target_skill, f"Scenario '{s.id}' has no target_skill"
            assert s.target_skill == DOMAIN_SKILL_MAP[domain_id]


def test_domain_scenario_ids_unique():
    ds = load_domain_scenarios()
    all_ids = [s.id for scenarios in ds.values() for s in scenarios]
    assert len(all_ids) == len(set(all_ids)), (
        f"Duplicate domain scenario IDs: {[x for x in all_ids if all_ids.count(x) > 1]}"
    )


def test_get_target_skills_non_dev():
    manifest = load_manifest()
    s = Scenario(
        id="t",
        name="t",
        prompt="p",
        target_skill="apify-competitor-intelligence",
        source_file="t.yaml",
        domain="competitive-intelligence",
    )
    skills = get_target_skills(s, manifest)
    assert "apify-competitor-intelligence" in skills
    # Non-dev should include generalist skills if in manifest
    if "apify-mcpc" in manifest:
        assert "apify-mcpc" in skills
    if "apify-ultimate-scraper" in manifest:
        assert "apify-ultimate-scraper" in skills


def test_get_target_skills_dev():
    manifest = load_manifest()
    s = Scenario(
        id="t",
        name="t",
        prompt="p",
        target_skill="apify-actor-development",
        source_file="t.yaml",
        domain="actor-development",
    )
    skills = get_target_skills(s, manifest)
    assert "apify-actor-development" in skills
    assert "apify-mcpc" not in skills
    assert "apify-ultimate-scraper" not in skills


def test_get_target_skills_dedup():
    """When specialist IS a generalist, don't duplicate it."""
    manifest = load_manifest()
    s = Scenario(
        id="t",
        name="t",
        prompt="p",
        target_skill="apify-ultimate-scraper",
        source_file="t.yaml",
        domain="ultimate-scraper",
    )
    skills = get_target_skills(s, manifest)
    assert skills.count("apify-ultimate-scraper") == 1
    if "apify-mcpc" in manifest:
        assert "apify-mcpc" in skills


# --- Scoring ---


def test_parse_scoring_response_valid():
    raw = """## Analysis
Some analysis text here.

```json
{"checks": {"WF-1": {"result": "pass", "evidence": "Good workflow", "summary": "Has steps"}, "WF-2": {"result": "fail", "evidence": "No loop", "summary": "Missing retry"}}, "risk_level": "MEDIUM"}
```
"""
    markdown, checks, risk = parse_scoring_response(raw)
    assert "Analysis" in markdown
    # All 25 LLM checks are returned — 2 from JSON, rest as "unclear"
    assert len(checks) == 29
    assert checks["WF-1"].result == "pass"
    assert checks["WF-1"].evidence == "Good workflow"
    assert checks["WF-2"].result == "fail"
    # Unscored checks are "unclear"
    assert checks["WF-3"].result == "unclear"
    assert risk == "MEDIUM"


def test_parse_scoring_response_no_json():
    raw = "Just some markdown analysis without JSON block"
    markdown, checks, risk = parse_scoring_response(raw)
    assert markdown == raw
    # All 25 checks are "unclear" as fallback
    assert len(checks) == 29
    assert all(c.result == "unclear" for c in checks.values())
    assert risk == "UNKNOWN"


def test_parse_scoring_response_malformed_json():
    raw = """## Analysis
```json
{not valid json}
```
"""
    markdown, checks, risk = parse_scoring_response(raw)
    assert len(checks) == 29
    assert all(c.result == "unclear" for c in checks.values())
    assert risk == "UNKNOWN"


def test_check_result_dataclass():
    cr = CheckResult(check_id="WF-1", result="pass", evidence="Good", summary="OK")
    assert cr.check_id == "WF-1"
    assert cr.result == "pass"
    assert cr.evidence == "Good"
    assert cr.summary == "OK"


def test_scored_run_dataclass():
    sr = ScoredRun(
        scenario_id="ci-1",
        skill="apify-competitor-intelligence",
        model="sonnet",
        checks=[CheckResult(check_id="WF-1", result="pass", evidence="", summary="")],
        risk_level="LOW",
        markdown_response="# Analysis",
        duration_s=5.0,
        cost_info="input=1000, output=2000",
    )
    assert sr.scenario_id == "ci-1"
    assert len(sr.checks) == 1
    assert sr.error is None


# --- Incremental save ---


def _make_scored_run(
    scenario_id: str = "ci-1",
    skill: str = "apify-competitor-intelligence",
    model: str = "sonnet",
) -> ScoredRun:
    """Helper to create a ScoredRun with realistic data for testing."""
    return ScoredRun(
        scenario_id=scenario_id,
        skill=skill,
        model=model,
        checks=[
            CheckResult(
                check_id="WF-1",
                result="pass",
                evidence="Has workflow steps",
                summary="Workflow present",
            ),
            CheckResult(
                check_id="DK-1",
                result="fail",
                evidence="No actor selection guidance",
                summary="Missing guidance",
            ),
        ],
        risk_level="MEDIUM",
        markdown_response="## Analysis\nDetailed analysis here.",
        duration_s=3.7,
        cost_info="input=500, output=1200",
        error=None,
    )


def test_save_scored_report_incremental_creates_file(tmp_path, monkeypatch):
    """save_scored_report_incremental writes scored_run_{run_id}.json."""
    monkeypatch.setattr("sim_core.REPORTS_DIR", tmp_path)
    run_id = "test_run_abc"
    results = [_make_scored_run()]
    metadata = {"model": "sonnet", "domains": ["competitive-intelligence"]}

    path = save_scored_report_incremental(run_id, results, metadata)

    assert path == tmp_path / "scored_run_test_run_abc.json"
    assert path.exists()


def test_save_scored_report_incremental_valid_json(tmp_path, monkeypatch):
    """save_scored_report_incremental produces valid JSON."""
    monkeypatch.setattr("sim_core.REPORTS_DIR", tmp_path)
    results = [_make_scored_run()]
    metadata = {"model": "sonnet"}

    path = save_scored_report_incremental("run123", results, metadata)

    data = json.loads(path.read_text())
    assert data["type"] == "scored"
    assert "generated" in data
    assert data["run_id"] == "run123"
    assert data["result_count"] == 1
    assert len(data["results"]) == 1


def test_save_scored_report_incremental_json_structure(tmp_path, monkeypatch):
    """The JSON structure matches the same schema as save_scored_report."""
    monkeypatch.setattr("sim_core.REPORTS_DIR", tmp_path)
    run = _make_scored_run(
        scenario_id="ci-1", skill="apify-competitor-intelligence", model="sonnet"
    )
    metadata = {"model": "sonnet", "domains": ["competitive-intelligence"]}

    path = save_scored_report_incremental("struct_test", [run], metadata)

    data = json.loads(path.read_text())
    result = data["results"][0]

    assert result["scenario_id"] == "ci-1"
    assert result["skill"] == "apify-competitor-intelligence"
    assert result["model"] == "sonnet"
    assert result["risk_level"] == "MEDIUM"
    assert result["duration_s"] == 3.7
    assert result["cost_info"] == "input=500, output=1200"
    assert result["error"] is None
    assert result["markdown_response"] == "## Analysis\nDetailed analysis here."

    checks = result["checks"]
    assert len(checks) == 2
    wf1 = next(c for c in checks if c["check_id"] == "WF-1")
    assert wf1["result"] == "pass"
    assert wf1["evidence"] == "Has workflow steps"
    assert wf1["summary"] == "Workflow present"


def test_save_scored_report_incremental_run_id_in_filename(tmp_path, monkeypatch):
    """File name contains the run_id exactly."""
    monkeypatch.setattr("sim_core.REPORTS_DIR", tmp_path)
    run_id = "my_unique_run_42"

    path = save_scored_report_incremental(run_id, [], {"model": "sonnet"})

    assert path.name == f"scored_run_{run_id}.json"


def test_save_scored_report_incremental_atomic_no_tmp_left(tmp_path, monkeypatch):
    """After a successful write, no .json.tmp file remains."""
    monkeypatch.setattr("sim_core.REPORTS_DIR", tmp_path)

    save_scored_report_incremental(
        "atomic_run", [_make_scored_run()], {"model": "sonnet"}
    )

    tmp_files = list(tmp_path.glob("*.json.tmp"))
    assert tmp_files == [], f"Unexpected tmp files: {tmp_files}"
    json_files = list(tmp_path.glob("*.json"))
    assert len(json_files) == 1


def test_save_scored_report_incremental_overwrites_on_second_call(
    tmp_path, monkeypatch
):
    """Calling save_scored_report_incremental twice with same run_id overwrites the file."""
    monkeypatch.setattr("sim_core.REPORTS_DIR", tmp_path)
    run_id = "overwrite_run"

    save_scored_report_incremental(run_id, [_make_scored_run()], {"model": "sonnet"})
    first_path = tmp_path / f"scored_run_{run_id}.json"
    first_data = json.loads(first_path.read_text())
    assert first_data["result_count"] == 1

    second_run = _make_scored_run(scenario_id="ci-2")
    save_scored_report_incremental(
        run_id, [_make_scored_run(), second_run], {"model": "sonnet"}
    )

    second_data = json.loads(first_path.read_text())
    assert second_data["result_count"] == 2
    assert len(second_data["results"]) == 2


def test_save_scored_report_incremental_metadata_included(tmp_path, monkeypatch):
    """Metadata fields are included at the top level of the JSON."""
    monkeypatch.setattr("sim_core.REPORTS_DIR", tmp_path)
    metadata = {
        "model": "haiku",
        "domains": ["ecommerce", "social-media"],
        "concurrency": 3,
    }

    path = save_scored_report_incremental("meta_run", [], metadata)
    data = json.loads(path.read_text())

    assert data["model"] == "haiku"
    assert data["domains"] == ["ecommerce", "social-media"]
    assert data["concurrency"] == 3


def test_load_all_scored_reports_matches_incremental_files(tmp_path, monkeypatch):
    """load_all_scored_reports() correctly loads files created by save_scored_report_incremental."""
    monkeypatch.setattr("sim_core.REPORTS_DIR", tmp_path)

    run = _make_scored_run()
    save_scored_report_incremental("inc_run_001", [run], {"model": "sonnet"})

    reports = load_all_scored_reports()
    assert len(reports) == 1

    loaded_metadata, loaded_runs = reports[0]
    assert loaded_metadata["run_id"] == "inc_run_001"
    assert loaded_metadata["type"] == "scored"
    assert len(loaded_runs) == 1
    assert loaded_runs[0].scenario_id == "ci-1"
    assert loaded_runs[0].skill == "apify-competitor-intelligence"
    assert loaded_runs[0].model == "sonnet"
    assert loaded_runs[0].risk_level == "MEDIUM"


def test_save_scored_report_incremental_creates_reports_dir(tmp_path, monkeypatch):
    """save_scored_report_incremental creates REPORTS_DIR if it doesn't exist."""
    new_dir = tmp_path / "reports_new"
    assert not new_dir.exists()
    monkeypatch.setattr("sim_core.REPORTS_DIR", new_dir)

    save_scored_report_incremental("dir_test", [], {"model": "sonnet"})

    assert new_dir.exists()
    assert (new_dir / "scored_run_dir_test.json").exists()
