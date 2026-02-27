"""
E2E skill behavior tests for apify-mcpc plugin.

Covers:
  A  - apify-mcpc: handles broken/missing mcpc (guides user to set up)
  B  - apify-mcpc: responds correctly with mcpc installed
  C  - apify-mcpc: loads without --dangerously-skip-permissions
  D  - apify-status: loads and shows session/cost info
  D2 - apify-status: loads without --dangerously-skip-permissions

Requires the plugin to be installed (uses installed_plugin fixture from conftest).
"""

import os

from conftest import run_claude


# ---------------------------------------------------------------------------
# A: apify-mcpc with broken/missing mcpc
# ---------------------------------------------------------------------------


def test_apify_mcpc_handles_missing_mcpc(installed_plugin, tmp_path):
    """A: Skill responds meaningfully when mcpc is not set up.

    Simulates a broken mcpc by shadowing it with a failing stub prepended to
    PATH. mcpc and node share the same nvm bin directory, so we can't strip
    PATH entirely — that would hide node and break claude too. claude is
    called via its absolute path so PATH changes don't affect it.

    The stub returns exit 127, which check_apify.sh may interpret as
    "mcpc found but broken" (no OAuth). The skill should respond with setup
    guidance (install or login) or attempt the task. Either is acceptable;
    the key requirement is that the skill loads and responds coherently.
    """
    fake_mcpc = tmp_path / "mcpc"
    fake_mcpc.write_text("#!/bin/sh\nexit 127\n")
    fake_mcpc.chmod(0o755)

    result = run_claude(
        "/apify-mcpc I want to scrape Instagram posts",
        skip_permissions=True,
        path_override=f"{tmp_path}:{os.environ.get('PATH', '')}",
    )
    assert result.returncode == 0, f"claude -p failed:\nstderr: {result.stderr}"

    output = result.stdout.lower()
    # Skill should respond meaningfully: setup guidance OR task keywords
    assert any(
        kw in output
        for kw in [
            "npm",
            "install",
            "login",
            "mcp.apify.com",
            "apify/mcpc",
            "instagram",
            "scrape",
            "actor",
            "apify",
        ]
    ), f"Expected meaningful response.\nResponse: {result.stdout}"


# ---------------------------------------------------------------------------
# B: apify-mcpc with mcpc installed
# ---------------------------------------------------------------------------


def test_apify_mcpc_responds_with_use_cases(installed_plugin):
    """B: Skill loads and lists use cases when mcpc is installed."""
    result = run_claude(
        "/apify-mcpc what use cases do you support? list them briefly",
        skip_permissions=True,
    )
    assert result.returncode == 0, f"claude -p failed:\nstderr: {result.stderr}"

    output = result.stdout.lower()
    skill_keywords = [
        "audience",
        "brand",
        "competitor",
        "lead",
        "influencer",
        "market",
        "trend",
    ]
    matches = [kw for kw in skill_keywords if kw in output]
    assert len(matches) >= 3, (
        f"Skill doesn't appear to have loaded — expected use case keywords.\n"
        f"Matched: {matches}\nResponse: {result.stdout}"
    )


# ---------------------------------------------------------------------------
# C: apify-mcpc without --dangerously-skip-permissions
# ---------------------------------------------------------------------------


def test_apify_mcpc_loads_without_skip_permissions(installed_plugin):
    """C: Skill loads without --dangerously-skip-permissions.

    Regression test for the compound !-backtick command bug:
    Before fix: `!`mcpc --version 2>/dev/null || echo "..."`` was blocked.
    After fix: `!`mcpc --version`` is auto-approved via Bash(mcpc *).
    """
    result = run_claude(
        "/apify-mcpc what is your purpose?",
        skip_permissions=False,
    )
    assert result.returncode == 0, (
        f"Skill failed to load without --dangerously-skip-permissions.\n"
        f"Likely cause: compound shell operators in !-backtick commands in SKILL.md.\n"
        f"stderr: {result.stderr}"
    )

    output = result.stdout.lower()
    assert any(w in output for w in ["apify", "actor", "scrape", "skill"]), (
        f"Skill may not have loaded.\nResponse: {result.stdout}"
    )


# ---------------------------------------------------------------------------
# D: /apify-status skill
# ---------------------------------------------------------------------------


def test_apify_status_responds(installed_plugin):
    """D: /apify-status loads and responds with session/cost information."""
    result = run_claude(
        "/apify-status",
        skip_permissions=True,
    )
    assert result.returncode == 0, f"claude -p failed:\nstderr: {result.stderr}"

    output = result.stdout.lower()
    assert any(
        w in output for w in ["session", "mcpc", "cost", "log", "actor", "apify"]
    ), f"apify-status skill may not have loaded.\nResponse: {result.stdout}"


def test_apify_status_loads_without_skip_permissions(installed_plugin):
    """D2: /apify-status loads without --dangerously-skip-permissions.

    The skill has no !-backtick commands. All commands (mcpc, tail, awk) are
    in allowed-tools, so no permission prompts should appear.
    """
    result = run_claude(
        "/apify-status",
        skip_permissions=False,
    )
    assert result.returncode == 0, (
        f"apify-status failed without --dangerously-skip-permissions.\n"
        f"stderr: {result.stderr}"
    )

    output = result.stdout.lower()
    assert any(w in output for w in ["session", "mcpc", "cost", "log", "apify"]), (
        f"apify-status skill may not have loaded.\nResponse: {result.stdout}"
    )
