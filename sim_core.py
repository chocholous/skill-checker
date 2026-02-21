"""
Skill Checker Core — shared logic for CLI and web server.

All constants, data structures, loading, execution, and reporting functions.
"""

import asyncio
import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator, Callable

import yaml


# --- Constants ---

ROOT = Path(__file__).parent
MANIFEST_PATH = ROOT / "skills_manifest.yaml"
SCENARIOS_DIR = ROOT / "scenarios"
REPORTS_DIR = ROOT / "reports"

DEFAULT_MODELS = ["sonnet", "opus", "haiku"]
DEFAULT_CONCURRENCY = 3

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
SEVERITY_BADGE = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}

GEN_CATEGORIES = {
    "GEN-1":  {"name": "Token budget exceeded", "severity": "HIGH", "description": "SKILL.md over 500 lines; unnecessary context bloat"},
    "GEN-2":  {"name": "Poor description", "severity": "MEDIUM", "description": "Missing trigger conditions, not 3rd person, vague"},
    "GEN-3":  {"name": "Missing workflow", "severity": "HIGH", "description": "Complex task without steps or checklist"},
    "GEN-4":  {"name": "No feedback loop", "severity": "MEDIUM", "description": "Missing validate→fix→retry cycle"},
    "GEN-5":  {"name": "Wrong degrees of freedom", "severity": "HIGH", "description": "Too rigid or too loose instructions"},
    "GEN-6":  {"name": "Deep reference nesting", "severity": "LOW", "description": "References 2+ levels deep"},
    "GEN-7":  {"name": "Time-sensitive content", "severity": "MEDIUM", "description": "Hardcoded versions, schemas without maintenance plan"},
    "GEN-8":  {"name": "Inconsistent terminology", "severity": "LOW", "description": "Mixing terms for the same concept"},
    "GEN-9":  {"name": "Unverified dependencies", "severity": "HIGH", "description": "Assumes installed tools without checking"},
    "GEN-10": {"name": "No progressive disclosure", "severity": "MEDIUM", "description": "Everything in one file, no layered structure"},
    "GEN-11": {"name": "Missing examples", "severity": "MEDIUM", "description": "No input/output examples provided"},
    "GEN-12": {"name": "Scripts punt errors", "severity": "HIGH", "description": "Scripts fail without explanation or recovery"},
    "GEN-13": {"name": "Magic constants", "severity": "LOW", "description": "Hardcoded values without explanation"},
}

APF_CATEGORIES = {
    "APF-1":  {"name": "Path resolution", "severity": "CRITICAL", "description": "Skill path doesn't work across setups"},
    "APF-2":  {"name": "Schema drift", "severity": "HIGH", "description": "Actor schema changed, skill has stale examples"},
    "APF-3":  {"name": "Expected tool not available", "severity": "HIGH", "description": "Skill assumes tool (mcpc, CLI, MCP server) that isn't available"},
    "APF-4":  {"name": "Input validation gaps", "severity": "HIGH", "description": "Destructive defaults, missing min/max limits"},
    "APF-5":  {"name": "Actor selection ambiguity", "severity": "HIGH", "description": "Multiple actors for same task, no selection guidance"},
    "APF-6":  {"name": "No resource budgeting", "severity": "MEDIUM", "description": "Missing memory, timeout, concurrency, cost guidance"},
    "APF-7":  {"name": "Run observability", "severity": "MEDIUM", "description": "Missing debugging guidance — logs, console"},
    "APF-8":  {"name": "Auth management", "severity": "MEDIUM", "description": "Token/OAuth anti-patterns"},
    "APF-9":  {"name": "Output variability", "severity": "LOW", "description": "Different actors return different data shapes"},
    "APF-10": {"name": "No scheduling pattern", "severity": "MEDIUM", "description": "Only one-shot, no recurring use cases"},
    "APF-11": {"name": "Multi-actor orchestration", "severity": "MEDIUM", "description": "Missing actor chaining guidance"},
}

ALL_CATEGORIES = {**GEN_CATEGORIES, **APF_CATEGORIES}


def _build_category_reference() -> str:
    """Build category reference table for the system prompt."""
    lines = ["### GEN — General Skill Quality Issues"]
    for cat_id, cat in GEN_CATEGORIES.items():
        lines.append(f"- **{cat_id}** [{cat['severity']}]: {cat['name']} — {cat['description']}")
    lines.append("")
    lines.append("### APF — Apify Platform Pitfalls")
    for cat_id, cat in APF_CATEGORIES.items():
        lines.append(f"- **{cat_id}** [{cat['severity']}]: {cat['name']} — {cat['description']}")
    return "\n".join(lines)


SYSTEM_PROMPT = f"""\
You are a skill quality auditor. You will receive:
1. A SKILL.md file — instructions for an AI agent skill
2. A user prompt — a task that a user might ask the skill to handle

Your job is to analyze how well the SKILL.md prepares the agent to handle this prompt.

Use the following complexity taxonomy to classify issues you find:

{_build_category_reference()}

Provide a detailed reasoning summary with these EXACT sections:

## Approach
How would an agent following this SKILL.md handle the prompt? Step by step.

## Complexities Identified
List every complexity, edge case, gap, or potential failure point you find.
For each, reference the relevant category code (GEN-* or APF-*) and explain:
- What the issue is
- Why it matters
- Whether the SKILL.md addresses it

## Missing Guidance
What should the SKILL.md say but doesn't? What would trip up an agent?

## Risk Assessment
Rate the overall risk: LOW / MEDIUM / HIGH / CRITICAL
Explain your rating.

## Verdict
One-paragraph summary: Is this skill ready for this prompt? What's the #1 thing to fix?

IMPORTANT: The SKILL.md references files and tools that are NOT available to you.
Do not try to access them. Focus purely on analyzing the instructions as written.\
"""


# --- Data Structures ---

@dataclass
class Scenario:
    id: str
    name: str
    prompt: str
    target_skill: str
    expected_complexities: list[str]
    source_file: str


@dataclass
class RunResult:
    scenario_id: str
    model: str
    response: str
    duration_s: float
    cost_info: str
    error: str | None = None


# --- Loading ---

def load_manifest() -> dict:
    with open(MANIFEST_PATH) as f:
        return yaml.safe_load(f)["skills"]


def load_scenarios() -> list[Scenario]:
    scenarios = []
    for yaml_file in sorted(SCENARIOS_DIR.glob("*.yaml")):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)

        file_level_skill = data.get("target_skill")
        for s in data["scenarios"]:
            scenarios.append(Scenario(
                id=s["id"],
                name=s["name"],
                prompt=s["prompt"],
                target_skill=s.get("target_skill", file_level_skill),
                expected_complexities=s.get("expected_complexities", []),
                source_file=yaml_file.name,
            ))
    return scenarios


def read_skill(manifest: dict, skill_name: str) -> str:
    skill_info = manifest.get(skill_name)
    if not skill_info:
        raise ValueError(f"Skill '{skill_name}' not found in manifest")
    path = Path(skill_info["path"])
    if not path.exists():
        raise FileNotFoundError(f"SKILL.md not found: {path}")
    return path.read_text()


# --- Execution ---

async def run_claude(
    model: str,
    system_prompt: str,
    user_prompt: str,
    semaphore: asyncio.Semaphore,
) -> tuple[str, float, str]:
    """Run claude -p and return (response, duration_s, cost_info)."""
    async with semaphore:
        cmd = [
            "claude", "-p",
            "--model", model,
            "--system-prompt", system_prompt,
            "--output-format", "json",
            "--no-session-persistence",
        ]

        start = time.monotonic()
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "CLAUDECODE": ""},  # unset to avoid nesting error
        )
        stdout, stderr = await proc.communicate(user_prompt.encode())
        duration = time.monotonic() - start

        if proc.returncode != 0:
            raise RuntimeError(
                f"claude -p exited with {proc.returncode}: {stderr.decode()[:500]}"
            )

        raw = stdout.decode()
        try:
            data = json.loads(raw)
            response = data.get("result", raw)
            cost_info = f"input={data.get('input_tokens', '?')}, output={data.get('output_tokens', '?')}"
        except json.JSONDecodeError:
            response = raw
            cost_info = "unknown (non-JSON output)"

        return response, duration, cost_info


async def run_scenario(
    scenario: Scenario,
    model: str,
    manifest: dict,
    semaphore: asyncio.Semaphore,
    on_complete: Callable[[str, str, bool], None] | None = None,
) -> RunResult:
    """Run a single scenario on a single model. Optional callback on_complete(scenario_id, model, success)."""
    skill_content = read_skill(manifest, scenario.target_skill)

    user_prompt = f"""# SKILL.md Content

```markdown
{skill_content}
```

# User Prompt

{scenario.prompt}
"""

    try:
        response, duration, cost_info = await run_claude(
            model=model,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            semaphore=semaphore,
        )
        result = RunResult(
            scenario_id=scenario.id,
            model=model,
            response=response,
            duration_s=round(duration, 1),
            cost_info=cost_info,
        )
        if on_complete:
            on_complete(scenario.id, model, True)
        return result
    except Exception as e:
        result = RunResult(
            scenario_id=scenario.id,
            model=model,
            response="",
            duration_s=0,
            cost_info="",
            error=str(e),
        )
        if on_complete:
            on_complete(scenario.id, model, False)
        return result


# --- Reporting ---

def generate_markdown_report(
    scenarios: list[Scenario],
    results: list[RunResult],
    models: list[str],
) -> str:
    """Generate a Markdown comparison report."""
    lines = [
        f"# Skill Checker Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Models: {', '.join(models)}",
        f"Scenarios: {len(scenarios)}",
        "",
    ]

    # Build lookup: (scenario_id, model) -> RunResult
    lookup = {(r.scenario_id, r.model): r for r in results}

    for scenario in scenarios:
        lines.append(f"---\n")
        lines.append(f"## [{scenario.id}] {scenario.name}")
        lines.append(f"**Skill**: `{scenario.target_skill}` | **Source**: `{scenario.source_file}`")
        lines.append(f"**Prompt**: _{scenario.prompt}_")
        lines.append(f"**Expected complexities**: {', '.join(scenario.expected_complexities)}")
        lines.append("")

        for cat in scenario.expected_complexities:
            info = ALL_CATEGORIES.get(cat)
            if info:
                badge = SEVERITY_BADGE.get(info["severity"], "")
                lines.append(f"  - {badge} **{cat}** [{info['severity']}]: {info['name']} — {info['description']}")
            else:
                lines.append(f"  - **{cat}**: _unknown category_")
        lines.append("")

        for model in models:
            result = lookup.get((scenario.id, model))
            if not result:
                lines.append(f"### {model}: _not run_\n")
                continue

            if result.error:
                lines.append(f"### {model}: ERROR")
                lines.append(f"```\n{result.error}\n```\n")
                continue

            lines.append(f"### {model} ({result.duration_s}s, {result.cost_info})")
            lines.append("")
            lines.append(result.response)
            lines.append("")

    return "\n".join(lines)


def generate_json_report(
    scenarios: list[Scenario],
    results: list[RunResult],
    models: list[str],
) -> dict:
    """Generate a structured JSON report."""
    lookup = {(r.scenario_id, r.model): r for r in results}
    return {
        "generated": datetime.now().isoformat(),
        "models": models,
        "scenario_count": len(scenarios),
        "results": [
            {
                "scenario_id": s.id,
                "scenario_name": s.name,
                "target_skill": s.target_skill,
                "prompt": s.prompt,
                "expected_complexities": [
                    {
                        "id": c,
                        "type": "GEN" if c.startswith("GEN-") else "APF" if c.startswith("APF-") else "UNKNOWN",
                        "severity": ALL_CATEGORIES[c]["severity"] if c in ALL_CATEGORIES else None,
                        "name": ALL_CATEGORIES[c]["name"] if c in ALL_CATEGORIES else None,
                    }
                    for c in s.expected_complexities
                ],
                "models": {
                    m: {
                        "response": r.response if r else None,
                        "duration_s": r.duration_s if r else None,
                        "cost_info": r.cost_info if r else None,
                        "error": r.error if r else None,
                    }
                    for m in models
                    for r in [lookup.get((s.id, m))]
                },
            }
            for s in scenarios
        ],
    }


def save_reports(
    scenarios: list[Scenario],
    results: list[RunResult],
    models: list[str],
    output_path: Path | None = None,
) -> tuple[Path, Path]:
    """Generate and save both reports. Returns (md_path, json_path)."""
    REPORTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    md_path = output_path or (REPORTS_DIR / f"report_{timestamp}.md")
    json_path = md_path.with_suffix(".json")

    md_report = generate_markdown_report(scenarios, results, models)
    md_path.write_text(md_report)

    json_report = generate_json_report(scenarios, results, models)
    json_path.write_text(json.dumps(json_report, indent=2, ensure_ascii=False))

    return md_path, json_path
