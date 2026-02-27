"""
E2E installation tests for apify-mcpc plugin.

Covers:
  - install from skill-checker marketplace
  - uninstall
  - A: skill loads and guides user when mcpc is not installed
  - B: skill loads and responds correctly when mcpc is installed
  - C: skill loads without --dangerously-skip-permissions (no compound !commands)

IMPORTANT: Run outside an active Claude Code session:
    CLAUDECODE= pytest plugins/apify-mcpc/tests/ -v

These tests modify your user-scope plugin installation. They clean up after
themselves, but if interrupted mid-run, manually uninstall with:
    claude plugin uninstall apify-mcpc
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

PLUGIN_DIR = Path(__file__).parent.parent
SKILL_MD = PLUGIN_DIR / "skills" / "apify-mcpc" / "SKILL.md"
MARKETPLACE = "skill-checker"
PLUGIN_NAME = "apify-mcpc"

# Unset CLAUDECODE so claude -p can be called from within a Claude Code session
_ENV = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

# Resolve claude binary once at import time — used as explicit executable so
# PATH overrides in individual tests don't accidentally hide it
_CLAUDE_BIN = shutil.which("claude") or "claude"


def _run_plugin(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [_CLAUDE_BIN, "plugin", *args],
        capture_output=True,
        text=True,
        env=_ENV,
        timeout=60,
    )


def _run_claude(
    prompt: str, *, skip_permissions: bool = True, path_override: str | None = None
) -> subprocess.CompletedProcess:
    cmd = [_CLAUDE_BIN, "-p", "--output-format", "json", "--no-session-persistence"]
    if skip_permissions:
        cmd.append("--dangerously-skip-permissions")
    env = _ENV.copy()
    if path_override is not None:
        env["PATH"] = path_override
    return subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def installed_plugin():
    """Install apify-mcpc from marketplace, yield, then uninstall."""
    # Clean slate — ignore errors if not installed
    _run_plugin("uninstall", PLUGIN_NAME)

    result = _run_plugin("install", f"{PLUGIN_NAME}@{MARKETPLACE}")
    assert result.returncode == 0, (
        f"Plugin install failed.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    yield
    _run_plugin("uninstall", PLUGIN_NAME)


# ---------------------------------------------------------------------------
# Install / Uninstall
# ---------------------------------------------------------------------------


def test_install_from_marketplace():
    """Plugin installs from skill-checker marketplace without errors."""
    _run_plugin("uninstall", PLUGIN_NAME)

    result = _run_plugin("install", f"{PLUGIN_NAME}@{MARKETPLACE}")
    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "error" not in result.stdout.lower(), result.stdout

    list_result = _run_plugin("list")
    assert PLUGIN_NAME in list_result.stdout, (
        f"Plugin not found in list after install:\n{list_result.stdout}"
    )

    _run_plugin("uninstall", PLUGIN_NAME)


def test_uninstall_removes_plugin(installed_plugin):
    """Plugin uninstalls cleanly and disappears from plugin list.

    Note: installed_plugin fixture installs first; this test uninstalls and
    the fixture teardown calls uninstall again (idempotent, that's fine).
    """
    result = _run_plugin("uninstall", PLUGIN_NAME)
    assert result.returncode == 0, (
        f"Uninstall failed.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    list_result = _run_plugin("list")
    assert PLUGIN_NAME not in list_result.stdout, (
        f"Plugin still present after uninstall:\n{list_result.stdout}"
    )
    # Re-install so module-scoped fixture teardown doesn't fail
    _run_plugin("install", f"{PLUGIN_NAME}@{MARKETPLACE}")


# ---------------------------------------------------------------------------
# A: User without mcpc
# ---------------------------------------------------------------------------


def test_skill_guides_user_without_mcpc(installed_plugin, tmp_path):
    """A: Skill loads and explains how to install mcpc when it's missing.

    Simulates a user who installed the plugin but hasn't set up mcpc yet.
    mcpc and node live in the same directory (e.g. nvm bin), so we can't
    strip PATH entirely — that would hide node and break claude too. Instead,
    we shadow mcpc with a failing stub prepended to PATH. claude is called via
    its absolute path (_CLAUDE_BIN) so PATH changes don't affect it.
    """
    fake_mcpc = tmp_path / "mcpc"
    fake_mcpc.write_text("#!/bin/sh\nexit 127\n")
    fake_mcpc.chmod(0o755)

    result = _run_claude(
        "/apify-mcpc I want to scrape Instagram posts",
        skip_permissions=True,
        path_override=f"{tmp_path}:{os.environ.get('PATH', '')}",
    )
    assert result.returncode == 0, f"claude -p failed:\nstderr: {result.stderr}"

    output = result.stdout.lower()
    assert "npm" in output or "install" in output, (
        f"Expected mcpc install guidance in response.\nResponse: {result.stdout}"
    )


# ---------------------------------------------------------------------------
# B: User with mcpc installed
# ---------------------------------------------------------------------------


def test_skill_responds_correctly_with_mcpc(installed_plugin):
    """B: Skill loads and describes its workflow when mcpc is installed.

    Uses actual mcpc in PATH (if present) or falls back to checking that the
    skill at minimum loads and responds with skill-relevant content.
    """
    result = _run_claude(
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
# C: User without --dangerously-skip-permissions
# ---------------------------------------------------------------------------


def test_skill_loads_without_skip_permissions(installed_plugin):
    """C: Skill loads without --dangerously-skip-permissions.

    Verifies the fix for the compound !-backtick command bug:
    Before fix: `!`mcpc --version 2>/dev/null || echo "..."`` contained || which
    the permission system treated as multiple operations, blocking skill loading.
    After fix: `!`mcpc --version`` is a single command, auto-approved via
    allowed-tools: Bash(mcpc *).

    If this test fails with a timeout or permission error, check SKILL.md for
    pipe operators (|, ||, &&) in !-backtick commands.
    """
    result = _run_claude(
        "/apify-mcpc what is your purpose?",
        skip_permissions=False,  # <-- no --dangerously-skip-permissions
    )
    assert result.returncode == 0, (
        f"Skill failed to load without --dangerously-skip-permissions.\n"
        f"Likely cause: compound shell operators in !-backtick commands in SKILL.md.\n"
        f"stderr: {result.stderr}"
    )

    output = result.stdout.lower()
    assert any(w in output for w in ["apify", "actor", "scrape", "skill"]), (
        f"Skill may not have loaded — response lacks expected keywords.\n"
        f"Response: {result.stdout}"
    )
