"""
Skill Checker Core — shared logic for CLI and web server.

All constants, data structures, loading, execution, and reporting functions.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
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


# --- Domain mappings (built dynamically from YAML files) ---


def _build_domain_skill_map() -> dict[str, str]:
    """Build domain->skill mapping by reading target_skill from domain YAML files."""
    result = {}
    for yaml_file in sorted(SCENARIOS_DIR.glob("*.yaml")):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
        domain = data.get("domain")
        target_skill = data.get("target_skill")
        if domain and target_skill:
            result[domain] = target_skill
    return result


DOMAIN_SKILL_MAP: dict[str, str] = _build_domain_skill_map()


def _build_dev_domains() -> set[str]:
    """Dev domains = domains whose skill has category 'dev' in manifest."""
    with open(MANIFEST_PATH) as f:
        manifest = yaml.safe_load(f)["skills"]
    dev_skills = {
        name for name, info in manifest.items() if info.get("category") == "dev"
    }
    return {domain for domain, skill in DOMAIN_SKILL_MAP.items() if skill in dev_skills}


DEV_DOMAINS: set[str] = _build_dev_domains()

DEV_EXCLUDED_CHECKS = [
    "DK-1",
    "DK-2",
    "DK-5",
    "APF-2",
    "APF-4",
    "APF-5",
    "APF-7",
    "APF-8",
    "APF-9",
    "APF-11",
]


# --- 5-Category Taxonomy ---

WF_CATEGORIES = {
    "WF-1": {
        "name": "Missing workflow",
        "severity": "HIGH",
        "description": "Complex task without steps or checklist",
    },
    "WF-2": {
        "name": "No feedback loop",
        "severity": "MEDIUM",
        "description": "Missing validate→fix→retry cycle; no handling of empty/partial results or actor fallback",
    },
    "WF-3": {
        "name": "Wrong degrees of freedom",
        "severity": "HIGH",
        "description": "Too rigid or too loose instructions",
    },
    "WF-4": {
        "name": "Missing examples",
        "severity": "MEDIUM",
        "description": "No input/output examples provided",
    },
    "WF-5": {
        "name": "No scope detection",
        "severity": "MEDIUM",
        "description": "Cannot distinguish docs-only / find-only / full pipeline queries",
    },
    "WF-6": {
        "name": "Linear-only workflow",
        "severity": "MEDIUM",
        "description": "No branching or conditional logic in workflow steps",
    },
}

DK_CATEGORIES = {
    "DK-1": {
        "name": "Actor selection ambiguity",
        "severity": "HIGH",
        "description": "Multiple actors for same task, no selection guidance",
    },
    "DK-2": {
        "name": "Output variability",
        "severity": "MEDIUM",
        "description": "Different actors return different data shapes",
    },
    "DK-3": {
        "name": "Unrealistic expectations",
        "severity": "MEDIUM",
        "description": "Prompt expects capabilities that actors don't have",
    },
    "DK-4": {
        "name": "Time-sensitive content",
        "severity": "MEDIUM",
        "description": "Hardcoded versions, schemas without maintenance plan",
    },
    "DK-5": {
        "name": "No scheduling pattern",
        "severity": "MEDIUM",
        "description": "Only one-shot, no recurring use cases",
    },
    "DK-6": {
        "name": "Missing domain caveats",
        "severity": "HIGH",
        "description": "Missing rate limits, GDPR, data availability warnings",
    },
    "DK-7": {
        "name": "Input correctness validation",
        "severity": "HIGH",
        "description": "No guidance to verify inputs yield correct results — e.g. guessed usernames, wrong URL formats, identifiers that resolve to wrong entities; skill should prompt agent to validate inputs against real service behavior before running paid operations",
    },
    "DK-8": {
        "name": "Data completeness awareness",
        "severity": "MEDIUM",
        "description": "No guidance for detecting incomplete data — missing pagination handling, truncated results, absent fields; agent may deliver partial data without warning user",
    },
}

BP_CATEGORIES = {
    "BP-1": {
        "name": "Token budget exceeded",
        "severity": "HIGH",
        "description": "SKILL.md over 500 lines; unnecessary context bloat",
    },
    "BP-2": {
        "name": "Poor description",
        "severity": "MEDIUM",
        "description": "Missing trigger conditions, not 3rd person, vague",
    },
    "BP-3": {
        "name": "Deep reference nesting",
        "severity": "LOW",
        "description": "References 2+ levels deep",
    },
    "BP-4": {
        "name": "Inconsistent terminology",
        "severity": "LOW",
        "description": "Mixing terms for the same concept",
    },
    "BP-5": {
        "name": "No progressive disclosure",
        "severity": "MEDIUM",
        "description": "Everything in one file, no layered structure",
    },
    "BP-6": {
        "name": "Magic constants",
        "severity": "LOW",
        "description": "Hardcoded values without explanation",
    },
    "BP-7": {
        "name": "Duplication between SKILL.md and references",
        "severity": "MEDIUM",
        "description": "Same content in SKILL.md and referenced files",
    },
    "BP-8": {
        "name": "Missing 'when to read' guidance",
        "severity": "MEDIUM",
        "description": "References lack usage context — agent doesn't know when to read them",
    },
}

APF_CATEGORIES = {
    "APF-1": {
        "name": "Path resolution",
        "severity": "CRITICAL",
        "description": "Skill path doesn't work across setups",
    },
    "APF-2": {
        "name": "Schema drift",
        "severity": "HIGH",
        "description": "Actor schema changed, skill has stale examples",
    },
    "APF-3": {
        "name": "Expected tool not available",
        "severity": "HIGH",
        "description": "Skill assumes tool (mcpc, CLI, MCP server) that isn't available",
    },
    "APF-4": {
        "name": "Input schema gotchas",
        "severity": "HIGH",
        "description": "Destructive defaults, missing min/max limits",
    },
    "APF-5": {
        "name": "No resource budgeting",
        "severity": "MEDIUM",
        "description": "Missing memory, timeout, concurrency, cost guidance",
    },
    "APF-6": {
        "name": "Run observability",
        "severity": "MEDIUM",
        "description": "Missing debugging guidance — logs, console",
    },
    "APF-7": {
        "name": "Output storage confusion",
        "severity": "MEDIUM",
        "description": "Unclear where results go — dataset vs key-value store vs direct output",
    },
    "APF-8": {
        "name": "Store search mismatch",
        "severity": "MEDIUM",
        "description": "Wrong store type or search method for the use case",
    },
    "APF-9": {
        "name": "Actor metadata ignorance",
        "severity": "LOW",
        "description": "Not using actor README, changelog, or maintained status",
    },
    "APF-10": {
        "name": "Proxy unawareness",
        "severity": "MEDIUM",
        "description": "Missing proxy configuration guidance for geo-restricted content",
    },
    "APF-11": {
        "name": "Multi-actor orchestration gap",
        "severity": "MEDIUM",
        "description": "Missing actor chaining guidance",
    },
    "APF-12": {
        "name": "Memory and scaling limits",
        "severity": "MEDIUM",
        "description": "No guidance for Actor memory configuration, large dataset handling, OOM risks; skill should warn about memory limits for high-volume scrapes and suggest appropriate memory/timeout settings",
    },
    "APF-13": {
        "name": "Parallelization patterns",
        "severity": "LOW",
        "description": "No guidance for concurrent Actor execution, batching large inputs, or rate limiting across multiple parallel runs; relevant for orchestration and high-throughput use cases",
    },
}

SEC_CATEGORIES = {
    "SEC-1": {
        "name": "Auth anti-patterns",
        "severity": "HIGH",
        "description": "Token/OAuth anti-patterns, insecure auth handling",
    },
    "SEC-4": {
        "name": "Credential exposure",
        "severity": "MEDIUM",
        "description": "Credentials in logs, outputs, or unprotected storage",
    },
}

ALL_CATEGORIES = {
    **WF_CATEGORIES,
    **DK_CATEGORIES,
    **BP_CATEGORIES,
    **APF_CATEGORIES,
    **SEC_CATEGORIES,
}

# Canonical list of 29 non-BP check IDs (used in LLM scoring prompt)
LLM_CHECK_IDS = sorted(
    [cid for cid in ALL_CATEGORIES if not cid.startswith("BP-")],
    key=lambda x: (x.split("-")[0], int(x.split("-")[1])),
)

CATEGORY_GROUPS = {
    "WF": {
        "name": "Workflow Quality",
        "default_models": ["sonnet"],
        "categories": WF_CATEGORIES,
    },
    "DK": {
        "name": "Domain Knowledge",
        "default_models": ["sonnet", "opus", "haiku"],
        "categories": DK_CATEGORIES,
    },
    "BP": {
        "name": "Best Practices",
        "default_models": ["bp-linter"],
        "categories": BP_CATEGORIES,
    },
    "APF": {
        "name": "Apify Platform Awareness",
        "default_models": ["sonnet", "opus"],
        "categories": APF_CATEGORIES,
    },
    "SEC": {
        "name": "Security",
        "default_models": ["sonnet"],
        "categories": SEC_CATEGORIES,
    },
}


def get_category_type(cat_id: str) -> str:
    """Extract category type prefix from a category ID (e.g. 'APF-3' -> 'APF')."""
    prefix = cat_id.split("-")[0]
    if prefix in CATEGORY_GROUPS:
        return prefix
    return "UNKNOWN"


def _build_category_reference(group_key: str) -> str:
    """Build category reference for a specific group's system prompt."""
    group = CATEGORY_GROUPS[group_key]
    lines = [f"### {group_key} — {group['name']}"]
    for cat_id, cat in group["categories"].items():
        lines.append(
            f"- **{cat_id}** [{cat['severity']}]: {cat['name']} — {cat['description']}"
        )
    return "\n".join(lines)


def _build_all_category_reference() -> str:
    """Build full category reference table (all non-BP groups)."""
    lines = []
    for group_key in CATEGORY_GROUPS:
        if group_key == "BP":
            continue
        lines.append(_build_category_reference(group_key))
        lines.append("")
    return "\n".join(lines)


_COMMON_OUTPUT_FORMAT = """\
Provide a detailed reasoning summary with these EXACT sections:

## Approach
How would an agent following this SKILL.md handle the prompt? Step by step.

## Complexities Identified
List every complexity, edge case, gap, or potential failure point you find.
For each, reference the relevant category code and explain:
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
Do not try to access them. Focus purely on analyzing the instructions as written."""


_CATEGORY_SYSTEM_PROMPTS: dict[str, str] = {
    "WF": f"""\
You are a **workflow quality auditor**. You will receive:
1. A SKILL.md file — instructions for an AI agent skill
2. A user prompt — a task that a user might ask the skill to handle

Your job is to analyze the WORKFLOW aspects of how the SKILL.md prepares the agent.
Focus specifically on: step completeness, feedback loops, error recovery, branching logic,
scope detection (docs-only vs full pipeline), degrees of freedom, and example coverage.

Use this taxonomy to classify workflow issues:

{_build_category_reference("WF")}

{_COMMON_OUTPUT_FORMAT}""",
    "DK": f"""\
You are a **domain knowledge auditor**. You will receive:
1. A SKILL.md file — instructions for an AI agent skill
2. A user prompt — a task that a user might ask the skill to handle

Your job is to analyze whether the SKILL.md provides adequate DOMAIN KNOWLEDGE for the agent.
Focus specifically on: actor selection guidance when multiple options exist, output format
variability between actors, realistic vs unrealistic prompt expectations, time-sensitive data
handling, scheduling patterns for recurring tasks, and domain-specific caveats (rate limits,
GDPR, data availability).

Use this taxonomy to classify domain knowledge issues:

{_build_category_reference("DK")}

{_COMMON_OUTPUT_FORMAT}""",
    "APF": f"""\
You are an **Apify platform awareness auditor**. You will receive:
1. A SKILL.md file — instructions for an AI agent skill
2. A user prompt — a task that a user might ask the skill to handle

Your job is to analyze PLATFORM-SPECIFIC issues in how the SKILL.md prepares the agent.
Focus specifically on: file path resolution across setups, actor schema staleness, tool
availability assumptions (mcpc, CLI, MCP servers), input schema gotchas (destructive defaults,
missing limits), resource budgeting, run observability, output storage patterns, proxy
configuration, and multi-actor orchestration.

Use this taxonomy to classify platform issues:

{_build_category_reference("APF")}

{_COMMON_OUTPUT_FORMAT}""",
    "SEC": f"""\
You are a **security auditor**. You will receive:
1. A SKILL.md file — instructions for an AI agent skill
2. A user prompt — a task that a user might ask the skill to handle

Your job is to analyze SECURITY aspects of how the SKILL.md handles authentication and credentials.
Focus specifically on: auth anti-patterns (token handling, OAuth flows, cookie-based auth),
credential exposure risks (credentials in logs, outputs, unprotected storage), and secure
handling of user-provided secrets.

Use this taxonomy to classify security issues:

{_build_category_reference("SEC")}

{_COMMON_OUTPUT_FORMAT}""",
}

# Fallback generic prompt for unknown categories
SYSTEM_PROMPT = f"""\
You are a skill quality auditor. You will receive:
1. A SKILL.md file — instructions for an AI agent skill
2. A user prompt — a task that a user might ask the skill to handle

Your job is to analyze how well the SKILL.md prepares the agent to handle this prompt.

Use the following complexity taxonomy to classify issues you find:

{_build_all_category_reference()}

{_COMMON_OUTPUT_FORMAT}"""


def _build_scoring_check_reference() -> str:
    """Build check reference for the scoring system prompt (all non-BP checks)."""
    lines = []
    for group_key in ("WF", "DK", "APF", "SEC"):
        group = CATEGORY_GROUPS[group_key]
        lines.append(f"### {group_key} — {group['name']}")
        for cat_id, cat in group["categories"].items():
            lines.append(
                f"- **{cat_id}** [{cat['severity']}]: {cat['name']} — {cat['description']}"
            )
        lines.append("")
    return "\n".join(lines)


SCORING_SYSTEM_PROMPT = f"""\
You are a **skill quality auditor** performing structured scoring. You will receive:
1. A SKILL.md file — instructions for an AI agent skill
2. A user prompt — a task that a user might ask the skill to handle

Your job is to:
1. Analyze how well the SKILL.md prepares the agent to handle this prompt
2. Provide a detailed markdown analysis
3. Score each check as pass/fail/unclear

## Check Taxonomy (29 checks)

{_build_scoring_check_reference()}

## Output Format

First, provide your detailed analysis in markdown with these sections:

## Approach
How would an agent following this SKILL.md handle the prompt? Step by step.

## Complexities Identified
For each relevant check, explain what you found.

## Risk Assessment
Rate the overall risk: LOW / MEDIUM / HIGH / CRITICAL

## Verdict
One-paragraph summary.

IMPORTANT: The SKILL.md references files and tools that are NOT available to you.
Do not try to access them. Focus purely on analyzing the instructions as written.

Then, at the very end of your response, output a structured JSON block wrapped in \
```json fences with your per-check scoring:

```json
{{
  "checks": {{
    "WF-1": {{"result": "pass", "evidence": "Skill provides step-by-step workflow", "summary": "Workflow present"}},
    "WF-2": {{"result": "fail", "evidence": "No retry or fallback logic found", "summary": "Missing feedback loop"}},
    ...
  }},
  "risk_level": "HIGH"
}}
```

Rules for scoring:
- **pass**: The SKILL.md adequately addresses this check for the given prompt
- **fail**: The SKILL.md has a clear gap or issue for this check
- **unclear**: Not enough information to determine, or partially addressed
- You MUST include ALL 29 check IDs in the JSON (WF-1 through WF-6, DK-1 through DK-8, \
APF-1 through APF-13, SEC-1, SEC-4)
- The JSON block MUST be the last thing in your response"""


def parse_scoring_response(raw: str) -> tuple[str, dict[str, CheckResult], str]:
    """Extract markdown + structured JSON from a scoring response.

    Returns (markdown, checks_dict, risk_level).
    """
    # Try to find JSON block at end of response
    json_pattern = r"```json\s*\n(.*?)\n\s*```"
    matches = list(re.finditer(json_pattern, raw, re.DOTALL))

    if not matches:
        # Fallback: all checks unclear
        checks = {
            cid: CheckResult(
                check_id=cid,
                result="unclear",
                evidence="No structured scoring in response",
            )
            for cid in LLM_CHECK_IDS
        }
        return raw, checks, "UNKNOWN"

    last_match = matches[-1]
    json_str = last_match.group(1)
    markdown = raw[: last_match.start()].rstrip()

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        checks = {
            cid: CheckResult(
                check_id=cid, result="unclear", evidence="JSON parse error in response"
            )
            for cid in LLM_CHECK_IDS
        }
        return raw, checks, "UNKNOWN"

    risk_level = data.get("risk_level", "UNKNOWN")
    raw_checks = data.get("checks", {})
    checks: dict[str, CheckResult] = {}
    for cid in LLM_CHECK_IDS:
        if cid in raw_checks:
            c = raw_checks[cid]
            result_val = c.get("result", "unclear")
            if result_val not in ("pass", "fail", "unclear", "na"):
                result_val = "unclear"
            checks[cid] = CheckResult(
                check_id=cid,
                result=result_val,
                evidence=c.get("evidence", ""),
                summary=c.get("summary", ""),
            )
        else:
            checks[cid] = CheckResult(
                check_id=cid, result="unclear", evidence="Not scored by model"
            )

    return markdown, checks, risk_level


# --- Data Structures ---


@dataclass
class Scenario:
    id: str
    name: str
    prompt: str
    target_skill: str
    source_file: str
    category: str = ""
    domain: str = ""
    models: list[str] | None = None


@dataclass
class RunResult:
    scenario_id: str
    model: str
    response: str
    duration_s: float
    cost_info: str
    error: str | None = None


@dataclass
class CheckResult:
    check_id: str
    result: str  # "pass" | "fail" | "unclear" | "na"
    evidence: str
    summary: str = ""


@dataclass
class ScoredRun:
    scenario_id: str
    skill: str
    model: str
    checks: list[CheckResult]
    risk_level: str
    markdown_response: str
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

        # Domain-based YAMLs: load with target_skill from YAML
        file_domain = data.get("domain", "")
        if file_domain:
            file_level_skill = data.get("target_skill", "")
            file_category = ""
            file_models = data.get("default_models")
            for s in data["scenarios"]:
                scenario_models = s.get("models")
                if scenario_models is None and file_models is not None:
                    scenario_models = file_models
                target_skill = s.get("target_skill", file_level_skill)
                scenarios.append(
                    Scenario(
                        id=s["id"],
                        name=s["name"],
                        prompt=s["prompt"],
                        target_skill=target_skill,
                        source_file=yaml_file.name,
                        domain=file_domain,
                        models=scenario_models if scenario_models else None,
                    )
                )
            continue

        # Category-based YAMLs (original format)
        file_level_skill = data.get("target_skill")
        file_category = data.get("category", "")
        file_models = data.get("default_models")
        for s in data["scenarios"]:
            category = s.get("category", file_category)

            scenario_models = s.get("models")
            if scenario_models is None and file_models is not None:
                scenario_models = file_models

            scenarios.append(
                Scenario(
                    id=s["id"],
                    name=s["name"],
                    prompt=s["prompt"],
                    target_skill=s.get("target_skill", file_level_skill),
                    source_file=yaml_file.name,
                    category=category,
                    models=scenario_models if scenario_models else None,
                )
            )
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


def get_scenario_models(
    scenario: Scenario, cli_override: list[str] | None = None
) -> list[str]:
    """Determine which models to run for a scenario.

    Priority: CLI override > scenario.models > category default_models > DEFAULT_MODELS.
    """
    if cli_override:
        return cli_override
    if scenario.models:
        return scenario.models
    if scenario.category and scenario.category in CATEGORY_GROUPS:
        return CATEGORY_GROUPS[scenario.category]["default_models"]
    return DEFAULT_MODELS


def build_system_prompt(category: str) -> str:
    """Build a category-specific system prompt. Falls back to generic SYSTEM_PROMPT."""
    return _CATEGORY_SYSTEM_PROMPTS.get(category, SYSTEM_PROMPT)


async def run_claude(
    model: str,
    system_prompt: str,
    user_prompt: str,
    semaphore: asyncio.Semaphore,
) -> tuple[str, float, str]:
    """Run claude -p and return (response, duration_s, cost_info)."""
    async with semaphore:
        cmd = [
            "claude",
            "-p",
            "--model",
            model,
            "--system-prompt",
            system_prompt,
            "--output-format",
            "json",
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
        system_prompt = build_system_prompt(scenario.category)
        response, duration, cost_info = await run_claude(
            model=model,
            system_prompt=system_prompt,
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
        "# Skill Checker Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Models: {', '.join(models)}",
        f"Scenarios: {len(scenarios)}",
        "",
    ]

    # Build lookup: (scenario_id, model) -> RunResult
    lookup = {(r.scenario_id, r.model): r for r in results}

    for scenario in scenarios:
        lines.append("---\n")
        lines.append(f"## [{scenario.id}] {scenario.name}")
        lines.append(
            f"**Skill**: `{scenario.target_skill}` | **Source**: `{scenario.source_file}`"
        )
        if scenario.category:
            lines.append(f"**Category**: {scenario.category}")
        lines.append(f"**Prompt**: _{scenario.prompt}_")
        lines.append("")

        # Use scenario-specific models if available, otherwise fall back to provided models
        scenario_models = models
        for model in scenario_models:
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
                "category": s.category,
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


# --- Domain-based scenario loading ---


def load_domain_scenarios() -> dict[str, list[Scenario]]:
    """Load ONLY domain-based YAMLs (those with a 'domain' field).

    Returns {domain: [scenarios]}.
    """
    result: dict[str, list[Scenario]] = {}
    for yaml_file in sorted(SCENARIOS_DIR.glob("*.yaml")):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)

        domain = data.get("domain")
        if not domain:
            continue  # Skip category-based YAMLs

        file_level_skill = data.get("target_skill", "")
        if not file_level_skill:
            raise ValueError(
                f"Domain YAML '{yaml_file.name}' missing 'target_skill' at file level"
            )

        scenarios = []
        for s in data["scenarios"]:
            target_skill = s.get("target_skill", file_level_skill)
            scenarios.append(
                Scenario(
                    id=s["id"],
                    name=s["name"],
                    prompt=s["prompt"],
                    target_skill=target_skill,
                    source_file=yaml_file.name,
                    domain=domain,
                )
            )
        result[domain] = scenarios

    return result


def get_target_skills(scenario: Scenario, manifest: dict) -> list[str]:
    """Get target skill(s) for a scenario.

    Dev domains → only specialist skill.
    Others → [specialist, "apify-mcpc", "apify-ultimate-scraper"].
    Deduplicates: if specialist IS one of the generalists, don't add it twice.
    """
    domain = scenario.domain
    if not domain:
        return [scenario.target_skill]

    specialist = scenario.target_skill
    if domain in DEV_DOMAINS:
        return [specialist]

    # Non-dev: specialist + generalist skills (mcpc, ultimate-scraper)
    generalists = ["apify-mcpc", "apify-ultimate-scraper"]
    skills = [specialist]
    for g in generalists:
        if g in manifest and g != specialist:
            skills.append(g)
    return skills


# --- Scored execution ---


async def run_scored_scenario(
    scenario: Scenario,
    skill_name: str,
    model: str,
    manifest: dict,
    semaphore: asyncio.Semaphore,
) -> ScoredRun:
    """Run a scenario with scoring system prompt against a specific skill.

    Returns ScoredRun with per-check results.
    """
    try:
        skill_content = read_skill(manifest, skill_name)

        user_prompt = f"""# SKILL.md Content

```markdown
{skill_content}
```

# User Prompt

{scenario.prompt}
"""

        response, duration, cost_info = await run_claude(
            model=model,
            system_prompt=SCORING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            semaphore=semaphore,
        )

        markdown, checks_dict, risk_level = parse_scoring_response(response)

        # Mark dev-excluded checks as "na" for dev domains
        if scenario.domain in DEV_DOMAINS:
            for cid in DEV_EXCLUDED_CHECKS:
                if cid in checks_dict:
                    checks_dict[cid] = CheckResult(
                        check_id=cid,
                        result="na",
                        evidence="Not applicable for dev skills",
                    )

        return ScoredRun(
            scenario_id=scenario.id,
            skill=skill_name,
            model=model,
            checks=list(checks_dict.values()),
            risk_level=risk_level,
            markdown_response=markdown,
            duration_s=round(duration, 1),
            cost_info=cost_info,
        )

    except Exception as e:
        # On error, return ScoredRun with all checks unclear
        checks = [
            CheckResult(check_id=cid, result="unclear", evidence=f"Error: {e}")
            for cid in LLM_CHECK_IDS
        ]
        return ScoredRun(
            scenario_id=scenario.id,
            skill=skill_name,
            model=model,
            checks=checks,
            risk_level="UNKNOWN",
            markdown_response="",
            duration_s=0,
            cost_info="",
            error=str(e),
        )


# --- Scored report save/load ---


def save_scored_report(results: list[ScoredRun], metadata: dict) -> Path:
    """Save scored run results to reports/scored_{timestamp}.json."""
    REPORTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    path = REPORTS_DIR / f"scored_{timestamp}.json"

    data = {
        "type": "scored",
        "generated": datetime.now().isoformat(),
        **metadata,
        "results": [
            {
                "scenario_id": r.scenario_id,
                "skill": r.skill,
                "model": r.model,
                "risk_level": r.risk_level,
                "duration_s": r.duration_s,
                "cost_info": r.cost_info,
                "error": r.error,
                "markdown_response": r.markdown_response,
                "checks": [
                    {
                        "check_id": c.check_id,
                        "result": c.result,
                        "evidence": c.evidence,
                        "summary": c.summary,
                    }
                    for c in r.checks
                ],
            }
            for r in results
        ],
    }

    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return path


def load_scored_report(path: Path) -> tuple[dict, list[ScoredRun]]:
    """Load a scored report from JSON. Returns (metadata, runs)."""
    data = json.loads(path.read_text())
    runs = []
    for r in data.get("results", []):
        checks = [
            CheckResult(
                check_id=c["check_id"],
                result=c["result"],
                evidence=c["evidence"],
                summary=c.get("summary", ""),
            )
            for c in r.get("checks", [])
        ]
        runs.append(
            ScoredRun(
                scenario_id=r["scenario_id"],
                skill=r["skill"],
                model=r["model"],
                checks=checks,
                risk_level=r["risk_level"],
                markdown_response=r.get("markdown_response", ""),
                duration_s=r["duration_s"],
                cost_info=r["cost_info"],
                error=r.get("error"),
            )
        )

    metadata = {k: v for k, v in data.items() if k != "results"}
    return metadata, runs


def load_latest_scored_report() -> tuple[dict, list[ScoredRun]] | None:
    """Find and load the newest scored_*.json report."""
    if not REPORTS_DIR.exists():
        return None
    scored_files = sorted(REPORTS_DIR.glob("scored_*.json"), reverse=True)
    if not scored_files:
        return None
    return load_scored_report(scored_files[0])


def save_scored_report_incremental(
    run_id: str,
    results: list[ScoredRun],
    metadata: dict,
) -> Path:
    """Overwrite the run's report file with current results (atomic).

    Writes to reports/scored_run_{run_id}.json using a tmp file + os.rename()
    to prevent partial reads if the process is interrupted mid-write.
    """
    REPORTS_DIR.mkdir(exist_ok=True)
    path = REPORTS_DIR / f"scored_run_{run_id}.json"
    tmp_path = path.with_suffix(".json.tmp")

    data = {
        "type": "scored",
        "generated": datetime.now().isoformat(),
        "run_id": run_id,
        **metadata,
        "result_count": len(results),
        "results": [
            {
                "scenario_id": r.scenario_id,
                "skill": r.skill,
                "model": r.model,
                "risk_level": r.risk_level,
                "duration_s": r.duration_s,
                "cost_info": r.cost_info,
                "error": r.error,
                "markdown_response": r.markdown_response,
                "checks": [
                    {
                        "check_id": c.check_id,
                        "result": c.result,
                        "evidence": c.evidence,
                        "summary": c.summary,
                    }
                    for c in r.checks
                ],
            }
            for r in results
        ],
    }

    tmp_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    tmp_path.rename(path)  # atomic on same filesystem
    return path


def load_all_scored_reports() -> list[tuple[dict, list[ScoredRun]]]:
    """Load ALL scored_*.json reports, newest first."""
    if not REPORTS_DIR.exists():
        return []
    scored_files = sorted(REPORTS_DIR.glob("scored_*.json"), reverse=True)
    results = []
    for f in scored_files:
        try:
            results.append(load_scored_report(f))
        except (json.JSONDecodeError, KeyError):
            continue
    return results


def merge_scored_runs(
    all_reports: list[tuple[dict, list[ScoredRun]]],
) -> tuple[list[str], dict[tuple[str, str, str], ScoredRun]]:
    """Merge runs from multiple reports. Index by (scenario_id, skill, model).

    For duplicates keeps newest (first in list since reports are newest-first).
    Returns (sorted_models, index).
    """
    index: dict[tuple[str, str, str], ScoredRun] = {}
    models_set: set[str] = set()

    for _metadata, runs in all_reports:
        for run in runs:
            key = (run.scenario_id, run.skill, run.model)
            if key not in index:
                index[key] = run
            models_set.add(run.model)

    sorted_models = sorted(models_set)
    return sorted_models, index
