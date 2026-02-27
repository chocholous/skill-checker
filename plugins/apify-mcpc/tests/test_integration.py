"""
Integration tests using spy mcpc.

These tests replace the real mcpc with a spy binary that:
  - Records every mcpc call to a log file (for command-sequence assertions)
  - Returns canned JSON responses matching real mcpc output shape
  - Returns _meta.usageTotalUsd in call-actor --json (for hook assertions)
  - Returns RUNNING status for async:=true calls (for resume pattern tests)

Four test categories:
  1. Hook fires     — PostToolUse hook wiring: plugin.json → track-cost.sh → cost log
  2. mcpc commands  — Claude calls the right mcpc commands in the right order
  3. Use-case refs  — Claude reads reference files and suggests correct actors
  4. Data handling  — Claude cleans/validates input data before running actors
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


def test_search_precedes_fetch_in_workflow_order(installed_plugin, tmp_path):
    """Skill calls search-actors strictly before fetch-actor-details.

    The SKILL.md Step 1 → Step 2 order must be respected: Claude may not
    fetch actor details before first performing a search.
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

    search_indices = [i for i, c in enumerate(calls) if "search-actors" in c]
    fetch_indices = [i for i, c in enumerate(calls) if "fetch-actor-details" in c]

    assert search_indices, (
        "Expected search-actors to be called.\nRecorded calls:\n" + "\n".join(calls)
    )
    assert fetch_indices, (
        "Expected fetch-actor-details to be called.\nRecorded calls:\n"
        + "\n".join(calls)
    )
    assert search_indices[0] < fetch_indices[0], (
        f"search-actors (call #{search_indices[0]}) must precede "
        f"fetch-actor-details (call #{fetch_indices[0]}).\n"
        "Recorded calls:\n" + "\n".join(f"  {i}: {c}" for i, c in enumerate(calls))
    )


def test_async_run_followed_by_get_actor_run(installed_plugin, tmp_path):
    """Skill follows async resume pattern: call-actor then get-actor-run.

    When a run is started with async:=true the spy returns status RUNNING
    with only a runId (no items). Claude should detect the RUNNING state
    and call get-actor-run to poll/check the status — as documented in
    the SKILL.md async resume section.
    """
    spy = make_spy_mcpc(tmp_path)

    result = run_claude(
        "/apify-mcpc Start an Instagram scrape for username 'nasa' asynchronously "
        "using async:=true so it runs in the background, then immediately check "
        "the run status. I confirm the input — please proceed.",
        skip_permissions=True,
        path_override=spy.path_override,
        extra_env=spy.env,
    )

    assert result.returncode == 0, f"claude -p failed:\nstderr: {result.stderr}"
    calls = spy.calls()
    assert any("call-actor" in c for c in calls), (
        "Expected call-actor to be called.\nRecorded calls:\n" + "\n".join(calls)
    )
    assert any("get-actor-run" in c for c in calls), (
        "Expected get-actor-run to be called after async call-actor.\n"
        "The skill should poll run status when async:=true is used.\n"
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


def test_competitor_intelligence_use_case_reads_reference(installed_plugin, tmp_path):
    """Skill reads competitor-intelligence.md and lists relevant actors.

    Docs-only query. competitor-intelligence.md lists actors for Instagram,
    YouTube, TikTok competitor analysis. The spy returns generic actors —
    if the response mentions competitor-specific actors or keywords,
    Claude read the reference file.
    """
    spy = make_spy_mcpc(tmp_path)

    result = run_claude(
        "/apify-mcpc What actors do you recommend for competitor analysis on Instagram and TikTok? Just list them briefly, don't run anything.",
        skip_permissions=True,
        path_override=spy.path_override,
        extra_env=spy.env,
    )

    assert result.returncode == 0, f"claude -p failed:\nstderr: {result.stderr}"
    output = result.stdout.lower()
    assert any(
        kw in output
        for kw in [
            "competitor",
            "instagram-followers",
            "tiktok-profile",
            "youtube-channel",
            "benchmark",
            "poidata",
        ]
    ), (
        f"Expected competitor analysis guidance from competitor-intelligence.md.\n"
        f"Response: {result.stdout}"
    )


def test_lead_generation_use_case_reads_reference(installed_plugin, tmp_path):
    """Skill reads lead-generation.md and suggests email/contact extractors.

    Docs-only query. lead-generation.md lists poidata/google-maps-email-extractor
    and apify/google-search-scraper as key actors. The spy returns generic
    Instagram/TikTok actors — if response mentions leads or email extraction,
    Claude read the reference file.
    """
    spy = make_spy_mcpc(tmp_path)

    result = run_claude(
        "/apify-mcpc What actors do you recommend for B2B lead generation from Google Maps? Just list them briefly, don't run anything.",
        skip_permissions=True,
        path_override=spy.path_override,
        extra_env=spy.env,
    )

    assert result.returncode == 0, f"claude -p failed:\nstderr: {result.stderr}"
    output = result.stdout.lower()
    assert any(
        kw in output
        for kw in [
            "lead",
            "email",
            "poidata",
            "google-maps-email",
            "contact",
            "google maps",
        ]
    ), (
        f"Expected lead generation guidance from lead-generation.md reference file.\n"
        f"Response: {result.stdout}"
    )


def test_trend_analysis_use_case_reads_reference(installed_plugin, tmp_path):
    """Skill reads trend-analysis.md and suggests Google Trends + TikTok actors.

    Docs-only query. trend-analysis.md lists apify/google-trends-scraper and
    clockworks/tiktok-trends-scraper as primary actors. The spy returns generic
    actors — if response mentions trends or google-trends, Claude read the file.
    """
    spy = make_spy_mcpc(tmp_path)

    result = run_claude(
        "/apify-mcpc What actors do you recommend for tracking TikTok trends? Just list them briefly, don't run anything.",
        skip_permissions=True,
        path_override=spy.path_override,
        extra_env=spy.env,
    )

    assert result.returncode == 0, f"claude -p failed:\nstderr: {result.stderr}"
    output = result.stdout.lower()
    assert any(
        kw in output
        for kw in [
            "google trends",
            "tiktok-trends",
            "clockworks",
            "trending",
            "viral",
            "hashtag",
        ]
    ), (
        f"Expected trend analysis guidance from trend-analysis.md reference file.\n"
        f"Response: {result.stdout}"
    )


# ---------------------------------------------------------------------------
# 4. Data handling — input validation and social handle normalization
# ---------------------------------------------------------------------------


def test_at_prefix_stripped_from_instagram_username(installed_plugin, tmp_path):
    """Skill strips @ prefix from Instagram usernames before calling actor.

    The instagram-post-scraper README (returned by spy fetch-actor-details) states
    'Input: username (list, no @)'. The SKILL.md Step 4 validation requires
    verifying input correctness. When the user provides '@nasa', the agent
    must pass 'nasa' (without @) in the call-actor input.

    Failure here means the skill is not validating/cleaning input handles.
    """
    spy = make_spy_mcpc(tmp_path)

    result = run_claude(
        "/apify-mcpc Scrape the latest Instagram posts from @nasa — go ahead and run it, I confirm the input.",
        skip_permissions=True,
        path_override=spy.path_override,
        extra_env=spy.env,
    )

    assert result.returncode == 0, f"claude -p failed:\nstderr: {result.stderr}"
    calls = spy.calls()
    call_actor_calls = [c for c in calls if "call-actor" in c]

    if not call_actor_calls:
        # Claude stopped at the gate — check response instead
        output = result.stdout.lower()
        assert "nasa" in output, (
            f"Expected 'nasa' in response (with or without @).\nResponse: {result.stdout}"
        )
        # If actor was not called, verify @ was not mentioned as correct format
        assert (
            "@nasa" not in result.stdout or "no @" in output or "without @" in output
        ), (
            f"Response may be validating '@nasa' as correct input — skill should warn about @ prefix.\n"
            f"Response: {result.stdout}"
        )
    else:
        # Actor was called — verify @ was stripped
        call_cmd = " ".join(call_actor_calls)
        assert "@nasa" not in call_cmd, (
            "call-actor was called with '@nasa' — @ prefix should be stripped.\n"
            "call-actor calls:\n" + "\n".join(call_actor_calls)
        )
        assert "nasa" in call_cmd, (
            "Expected 'nasa' in call-actor input.\ncall-actor calls:\n"
            + "\n".join(call_actor_calls)
        )
