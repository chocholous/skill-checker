#!/usr/bin/env python3
"""
Skill Checker — CLI tool that sends SKILL.md + test prompts to Claude models
and compares their reasoning about complexities, edge cases, and approach.

Usage:
    python sim.py                           # Run all scenarios on all models
    python sim.py --scenario dc-1           # Run single scenario
    python sim.py --model sonnet            # Single model
    python sim.py --dry-run                 # Show what would run
    python sim.py --list                    # List all scenarios
    python sim.py --concurrency 5           # Max parallel calls (default: 3)
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml


# --- Constants ---

ROOT = Path(__file__).parent
MANIFEST_PATH = ROOT / "skills_manifest.yaml"
SCENARIOS_DIR = ROOT / "scenarios"
REPORTS_DIR = ROOT / "reports"

DEFAULT_MODELS = ["sonnet", "opus", "haiku"]
DEFAULT_CONCURRENCY = 3

COMPLEXITY_LABELS = {
    "CAT-1": "${CLAUDE_PLUGIN_ROOT} undefined — breaks run_actor.js path",
    "CAT-2": "Dynamic schema via mcpc — adds latency + hard dependency",
    "CAT-3": "No resource management (--memory, concurrency) in dispatcher skills",
    "CAT-4": "No parallel actor guidance",
    "CAT-5": "Actor duplicity — same actor in 6-8 skills with different descriptions",
    "CAT-6": "No input validation (tweet-scraper min 50, extractFullText=true = 100x slower)",
    "CAT-7": "mcpc not installed by default, but skills say 'no need to check upfront'",
    "CAT-8": "Token extraction anti-pattern (export $(grep APIFY_TOKEN .env | xargs))",
    "CAT-9": "Ecommerce outlier — inline schema may become stale",
    "CAT-10": "Dev skills have references/, dispatcher skills don't",
}

SYSTEM_PROMPT = """\
You are a skill quality auditor. You will receive:
1. A SKILL.md file — instructions for an AI agent skill
2. A user prompt — a task that a user might ask the skill to handle

Your job is to analyze how well the SKILL.md prepares the agent to handle this prompt.

Provide a detailed reasoning summary with these EXACT sections:

## Approach
How would an agent following this SKILL.md handle the prompt? Step by step.

## Complexities Identified
List every complexity, edge case, gap, or potential failure point you find.
For each, explain:
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
) -> RunResult:
    """Run a single scenario on a single model."""
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
        return RunResult(
            scenario_id=scenario.id,
            model=model,
            response=response,
            duration_s=round(duration, 1),
            cost_info=cost_info,
        )
    except Exception as e:
        return RunResult(
            scenario_id=scenario.id,
            model=model,
            response="",
            duration_s=0,
            cost_info="",
            error=str(e),
        )


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
            label = COMPLEXITY_LABELS.get(cat, cat)
            lines.append(f"  - **{cat}**: {label}")
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
                "expected_complexities": s.expected_complexities,
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


# --- CLI ---

def list_scenarios(scenarios: list[Scenario]) -> None:
    """Print scenario list."""
    print(f"{'ID':<8} {'Skill':<35} {'Name'}")
    print("-" * 80)
    for s in scenarios:
        print(f"{s.id:<8} {s.target_skill:<35} {s.name}")
    print(f"\nTotal: {len(scenarios)} scenarios")


def dry_run(scenarios: list[Scenario], models: list[str]) -> None:
    """Print what would be executed."""
    total = len(scenarios) * len(models)
    print(f"Dry run: {len(scenarios)} scenarios × {len(models)} models = {total} calls\n")
    for s in scenarios:
        for m in models:
            print(f"  [{s.id}] {s.name} → {m}")
    est_low = total * 0.05
    est_high = total * 0.15
    print(f"\nEstimated cost: ${est_low:.2f} - ${est_high:.2f}")


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Skill Checker — test SKILL.md quality with Claude models"
    )
    parser.add_argument("--scenario", "-s", help="Run specific scenario by ID")
    parser.add_argument(
        "--model", "-m", action="append",
        help=f"Model to use (repeat for multiple). Default: {', '.join(DEFAULT_MODELS)}",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would run")
    parser.add_argument("--list", action="store_true", help="List all scenarios")
    parser.add_argument(
        "--concurrency", "-c", type=int, default=DEFAULT_CONCURRENCY,
        help=f"Max concurrent claude -p calls (default: {DEFAULT_CONCURRENCY})",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path (auto-generated if not set)",
    )
    args = parser.parse_args()

    # Load data
    all_scenarios = load_scenarios()
    manifest = load_manifest()
    models = args.model or DEFAULT_MODELS

    # List mode
    if args.list:
        list_scenarios(all_scenarios)
        return

    # Filter scenarios
    if args.scenario:
        scenarios = [s for s in all_scenarios if s.id == args.scenario]
        if not scenarios:
            print(f"Error: scenario '{args.scenario}' not found", file=sys.stderr)
            list_scenarios(all_scenarios)
            sys.exit(1)
    else:
        scenarios = all_scenarios

    # Dry run
    if args.dry_run:
        dry_run(scenarios, models)
        return

    # Validate skills exist
    for s in scenarios:
        try:
            read_skill(manifest, s.target_skill)
        except (ValueError, FileNotFoundError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    # Execute
    semaphore = asyncio.Semaphore(args.concurrency)
    total = len(scenarios) * len(models)
    print(f"Running {total} calls ({len(scenarios)} scenarios × {len(models)} models, concurrency={args.concurrency})")
    print()

    tasks = []
    for scenario in scenarios:
        for model in models:
            tasks.append(run_scenario(scenario, model, manifest, semaphore))

    completed = 0
    results = []
    for coro in asyncio.as_completed(tasks):
        result = await coro
        completed += 1
        status = "OK" if not result.error else "ERR"
        print(f"  [{completed}/{total}] {result.scenario_id} × {result.model}: {status} ({result.duration_s}s)")
        results.append(result)

    # Generate reports
    REPORTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    if args.output:
        md_path = Path(args.output)
    else:
        md_path = REPORTS_DIR / f"report_{timestamp}.md"

    json_path = md_path.with_suffix(".json")

    md_report = generate_markdown_report(scenarios, results, models)
    md_path.write_text(md_report)

    json_report = generate_json_report(scenarios, results, models)
    json_path.write_text(json.dumps(json_report, indent=2, ensure_ascii=False))

    print(f"\nReports saved:")
    print(f"  Markdown: {md_path}")
    print(f"  JSON:     {json_path}")

    # Summary
    errors = [r for r in results if r.error]
    if errors:
        print(f"\n{len(errors)} errors:")
        for e in errors:
            print(f"  [{e.scenario_id}] {e.model}: {e.error[:100]}")


if __name__ == "__main__":
    asyncio.run(main())
