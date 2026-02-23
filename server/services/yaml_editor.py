"""
YAML editor service — validates and writes scenario YAML files.
"""

import re
import shutil
from pathlib import Path

import yaml

from sim_core import CATEGORY_GROUPS, SCENARIOS_DIR


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

    file_domain = data.get("domain", "")
    file_level_skill = data.get("target_skill")
    file_category = data.get("category", "")

    # Validate domain-based format
    if file_domain:
        if not data.get("target_skill"):
            errors.append("Domain format requires 'target_skill' at file level")

        for i, s in enumerate(data["scenarios"]):
            prefix = f"scenarios[{i}]"
            for required in ("id", "name", "prompt"):
                if required not in s:
                    errors.append(f"{prefix}: missing '{required}'")

        return errors

    # Validate file-level category if present (category-based format)
    if file_category and file_category not in CATEGORY_GROUPS:
        errors.append(
            f"Unknown file-level category '{file_category}' (valid: {', '.join(CATEGORY_GROUPS.keys())})"
        )

    for i, s in enumerate(data["scenarios"]):
        prefix = f"scenarios[{i}]"

        for required in ("id", "name", "prompt"):
            if required not in s:
                errors.append(f"{prefix}: missing '{required}'")

        skill = s.get("target_skill", file_level_skill)
        if not skill:
            errors.append(
                f"{prefix}: no target_skill (neither file-level nor scenario-level)"
            )

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


_FILENAME_RE = re.compile(r"^[a-z0-9_-]+\.yaml$")


def create_scenario_yaml(filename: str, content: str) -> None:
    """Validate and write a new scenario YAML file (must not exist yet)."""
    if not _FILENAME_RE.match(filename):
        raise YamlValidationError(
            [
                "Invalid filename — only lowercase alphanumeric, hyphens, "
                "underscores allowed, must end with .yaml"
            ]
        )

    path = SCENARIOS_DIR / filename
    if path.exists():
        raise FileExistsError(f"Scenario file already exists: {filename}")

    errors = validate_scenario_yaml(content)
    if errors:
        raise YamlValidationError(errors)

    path.write_text(content)


def delete_scenario_yaml(source_file: str) -> None:
    """Delete a scenario YAML file after creating a .bak backup."""
    path = SCENARIOS_DIR / source_file
    if not path.exists():
        raise FileNotFoundError(f"Scenario file not found: {source_file}")

    # Backup before deletion
    backup = path.with_suffix(".yaml.bak")
    shutil.copy2(path, backup)

    path.unlink()
