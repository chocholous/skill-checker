"""
Install / uninstall tests for apify-mcpc plugin.

Verifies:
  - Plugin installs from skill-checker marketplace without errors
  - Plugin uninstalls cleanly and disappears from plugin list
"""

from conftest import PLUGIN_NAME, MARKETPLACE, run_plugin


def test_install_from_marketplace():
    """Plugin installs from skill-checker marketplace without errors."""
    run_plugin("uninstall", PLUGIN_NAME)

    result = run_plugin("install", f"{PLUGIN_NAME}@{MARKETPLACE}")
    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "error" not in result.stdout.lower(), result.stdout

    list_result = run_plugin("list")
    assert PLUGIN_NAME in list_result.stdout, (
        f"Plugin not found in list after install:\n{list_result.stdout}"
    )

    run_plugin("uninstall", PLUGIN_NAME)


def test_uninstall_removes_plugin(installed_plugin):
    """Plugin uninstalls cleanly and disappears from plugin list.

    Note: installed_plugin fixture installs first; this test uninstalls and
    the fixture teardown calls uninstall again (idempotent, that's fine).
    """
    result = run_plugin("uninstall", PLUGIN_NAME)
    assert result.returncode == 0, (
        f"Uninstall failed.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    list_result = run_plugin("list")
    assert PLUGIN_NAME not in list_result.stdout, (
        f"Plugin still present after uninstall:\n{list_result.stdout}"
    )
    # Re-install so module-scoped fixture teardown doesn't fail
    run_plugin("install", f"{PLUGIN_NAME}@{MARKETPLACE}")
