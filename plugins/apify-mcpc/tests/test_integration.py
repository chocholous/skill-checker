"""
Integration tests using spy mcpc.

These tests replace the real mcpc with a spy binary that:
  - Records every mcpc call to a log file (for command-sequence assertions)
  - Returns canned JSON responses matching real mcpc output shape
  - Returns _meta.usageTotalUsd in call-actor --json (for hook assertions)

Three test categories:
  1. Hook fires     — PostToolUse hook wiring: plugin.json → track-cost.sh → cost log
  2. mcpc commands  — Claude calls the right mcpc commands in the right order
  3. Use-case refs  — Claude reads reference files and suggests correct actors
"""

from conftest import make_spy_mcpc, run_claude


# ---------------------------------------------------------------------------
# 1. Hook fires in a real Claude session
# ---------------------------------------------------------------------------


def test_hook_fires_when_call_actor_json_runs(installed_plugin, tmp_path):
    """Hook integration: PostToolUse hook fires and writes to cost log.

    Asks Claude to run a specific call-actor --json command. The spy mcpc
    returns _meta.usageTotalUsd. If the hook is properly wired in plugin.json,
    track-cost.sh will fire and write to APIFY_COST_LOG.

    Failure here means the hook is not registered (plugin.json) or the script
    path is wrong, even though the unit tests in test_hook.py pass.
    """
    spy = make_spy_mcpc(tmp_path)

    result = run_claude(
        "Run this bash command: mcpc @apify tools-call call-actor actor:=\"apify/test\" input:='{}' --json",
        skip_permissions=True,
        path_override=spy.path_override,
        extra_env=spy.env,
    )

    assert result.returncode == 0, f"claude -p failed:\nstderr: {result.stderr}"
    assert spy.cost_log.exists(), (
        "Cost log was not created — PostToolUse hook may not have fired.\n"
        "Check: plugin.json hooks config, ${CLAUDE_PLUGIN_ROOT} expansion, script permissions.\n"
        f"Response: {result.stdout}"
    )
    assert "usd=0.0042" in spy.cost_log.read_text(), spy.cost_log.read_text()


# ---------------------------------------------------------------------------
# 2. mcpc command sequence
# ---------------------------------------------------------------------------


def test_search_actors_called_on_scraping_request(installed_plugin, tmp_path):
    """Skill calls search-actors when user asks to scrape a platform.

    Step 1 of the workflow must always search. This verifies that Claude
    follows the SKILL.md instruction: ALWAYS do at least two searches.
    """
    spy = make_spy_mcpc(tmp_path)

    result = run_claude(
        "/apify-mcpc I want to scrape Instagram posts, just find me the best actor",
        skip_permissions=True,
        path_override=spy.path_override,
        extra_env=spy.env,
    )

    assert result.returncode == 0, f"claude -p failed:\nstderr: {result.stderr}"
    calls = spy.calls()
    assert any("search-actors" in c for c in calls), (
        "Expected search-actors to be called.\nRecorded calls:\n" + "\n".join(calls)
    )


def test_fetch_actor_details_called_after_search(installed_plugin, tmp_path):
    """Skill calls fetch-actor-details after search (Step 2 of workflow).

    After finding candidates, Claude must fetch details and input schema
    before presenting a recommendation. This verifies Step 2 is followed.
    """
    spy = make_spy_mcpc(tmp_path)

    result = run_claude(
        "/apify-mcpc find and compare the best Instagram scrapers for me",
        skip_permissions=True,
        path_override=spy.path_override,
        extra_env=spy.env,
    )

    assert result.returncode == 0, f"claude -p failed:\nstderr: {result.stderr}"
    calls = spy.calls()
    assert any("fetch-actor-details" in c for c in calls), (
        "Expected fetch-actor-details to be called after search.\n"
        "Recorded calls:\n" + "\n".join(calls)
    )


# ---------------------------------------------------------------------------
# 3. Use-case reference files
# ---------------------------------------------------------------------------


def test_influencer_use_case_reads_reference_and_suggests_tiktok(
    installed_plugin, tmp_path
):
    """Skill reads influencer-discovery.md and lists TikTok actors.

    Docs-only query (no scraping) — avoids the full workflow and gates.
    The reference file lists clockworks/tiktok-scraper for TikTok.
    """
    spy = make_spy_mcpc(tmp_path)

    result = run_claude(
        "/apify-mcpc What actors do you recommend for TikTok influencer discovery? Just list them briefly, don't run anything.",
        skip_permissions=True,
        path_override=spy.path_override,
        extra_env=spy.env,
    )

    assert result.returncode == 0, f"claude -p failed:\nstderr: {result.stderr}"
    output = result.stdout.lower()
    assert any(
        kw in output
        for kw in ["tiktok", "clockworks", "influencer", "hashtag", "engagement"]
    ), (
        f"Expected TikTok influencer guidance from reference file.\nResponse: {result.stdout}"
    )


def test_brand_monitoring_use_case_reads_reference_and_suggests_review_scrapers(
    installed_plugin, tmp_path
):
    """Skill reads brand-monitoring.md and lists review actors.

    Docs-only query (no scraping) — avoids the full workflow and gates.
    brand-monitoring.md mentions compass/Google-Maps-Reviews-Scraper.
    The spy search-actors returns Instagram/TikTok only — NOT review scrapers.
    If the response mentions reviews or Google Maps, Claude read the reference file.
    """
    spy = make_spy_mcpc(tmp_path)

    result = run_claude(
        "/apify-mcpc What actors do you recommend for Google Maps review monitoring? Just list them briefly, don't run anything.",
        skip_permissions=True,
        path_override=spy.path_override,
        extra_env=spy.env,
    )

    assert result.returncode == 0, f"claude -p failed:\nstderr: {result.stderr}"
    output = result.stdout.lower()
    assert any(
        kw in output
        for kw in [
            "google maps",
            "reviews",
            "compass",
            "tripadvisor",
            "booking",
        ]
    ), (
        f"Expected review scraper guidance from brand-monitoring.md reference file.\n"
        f"Response: {result.stdout}"
    )
