"""
YAML editor service — validates and writes scenario YAML files.
"""

import shutil
from pathlib import Path

import yaml

from sim_core import ALL_CATEGORIES, SCENARIOS_DIR


class YamlValidationError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(f"YAML validation failed: {'; '.join(errors)}")


def validate_scenario_yaml(content: str) -> list[str]:
    """Validate YAML content. Returns list of error strings (empty = valid)."""
    errors = []

    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        return [f"YAML parse error: {e}"]

    if not isinstance(data, dict):
        return ["Root must be a mapping"]

    if "scenarios" not in data:
        return ["Missing 'scenarios' key"]

    if not isinstance(data["scenarios"], list):
        return ["'scenarios' must be a list"]

    file_level_skill = data.get("target_skill")

    for i, s in enumerate(data["scenarios"]):
        prefix = f"scenarios[{i}]"

        for required in ("id", "name", "prompt"):
            if required not in s:
                errors.append(f"{prefix}: missing '{required}'")

        skill = s.get("target_skill", file_level_skill)
        if not skill:
            errors.append(f"{prefix}: no target_skill (neither file-level nor scenario-level)")

        for cat in s.get("expected_complexities", []):
            if cat not in ALL_CATEGORIES:
                errors.append(f"{prefix}: unknown category '{cat}'")

    return errors


def save_scenario_yaml(source_file: str, content: str) -> None:
    """Validate and write YAML. Creates .bak backup first."""
    errors = validate_scenario_yaml(content)
    if errors:
        raise YamlValidationError(errors)

    path = SCENARIOS_DIR / source_file
    if not path.exists():
        raise FileNotFoundError(f"Scenario file not found: {source_file}")

    # Backup
    backup = path.with_suffix(".yaml.bak")
    shutil.copy2(path, backup)

    path.write_text(content)
