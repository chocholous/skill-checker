"""
BP (Best Practices) static linter — runs structural checks on SKILL.md files
without calling Claude API. Emits RunResult-compatible output with model="bp-linter".
"""

import re
from dataclasses import dataclass

from sim_core import BP_CATEGORIES, RunResult

# Threshold for BP-1 (token budget exceeded)
LINE_LIMIT = 500

# Patterns that suggest magic constants (BP-6)
_MAGIC_NUMBER_PATTERN = re.compile(
    r"(?:timeout|delay|limit|max|min|retry|retries|concurrency|wait|sleep|interval|budget|cost)\s*[:=]\s*\d+",
    re.IGNORECASE,
)
_HARDCODED_URL_PATTERN = re.compile(
    r"https?://(?!example\.com|localhost|127\.0\.0\.1)\S+",
)


@dataclass
class BPCheckResult:
    check_id: str
    triggered: bool
    severity: str
    name: str
    detail: str


def _check_bp1_token_budget(content: str) -> BPCheckResult:
    """BP-1: SKILL.md over LINE_LIMIT lines."""
    lines = content.splitlines()
    line_count = len(lines)
    return BPCheckResult(
        check_id="BP-1",
        triggered=line_count > LINE_LIMIT,
        severity=BP_CATEGORIES["BP-1"]["severity"],
        name=BP_CATEGORIES["BP-1"]["name"],
        detail=f"SKILL.md has {line_count} lines (limit: {LINE_LIMIT})",
    )


def _check_bp2_poor_description(content: str) -> BPCheckResult:
    """BP-2: Missing/poor frontmatter description."""
    # Check for YAML frontmatter with description
    has_frontmatter = content.startswith("---")
    has_description = False
    has_trigger = False

    if has_frontmatter:
        end = content.find("---", 3)
        if end > 0:
            fm = content[3:end].lower()
            has_description = "description" in fm
            has_trigger = any(kw in fm for kw in ["trigger", "when", "activate"])

    # Also check first 20 lines for a clear description section
    first_lines = "\n".join(content.splitlines()[:20]).lower()
    has_desc_section = "## description" in first_lines or "# description" in first_lines

    triggered = not (has_description or has_desc_section)
    detail_parts = []
    if not has_frontmatter:
        detail_parts.append("no YAML frontmatter")
    elif not has_description:
        detail_parts.append("frontmatter missing 'description'")
    if not has_trigger and not any(
        kw in first_lines for kw in ["trigger", "when to use", "activate"]
    ):
        detail_parts.append("no trigger conditions found")

    return BPCheckResult(
        check_id="BP-2",
        triggered=triggered,
        severity=BP_CATEGORIES["BP-2"]["severity"],
        name=BP_CATEGORIES["BP-2"]["name"],
        detail="; ".join(detail_parts)
        if detail_parts
        else "Description looks adequate",
    )


def _check_bp3_deep_nesting(content: str) -> BPCheckResult:
    """BP-3: References nested 2+ levels deep."""
    # Look for patterns like `references/*/references/` or nested file includes
    ref_pattern = re.compile(r"references?/", re.IGNORECASE)
    refs = ref_pattern.findall(content)
    # Check for double-nested references (reference inside reference)
    nested = re.findall(r"references?/\S+/references?/", content, re.IGNORECASE)
    triggered = len(nested) > 0

    return BPCheckResult(
        check_id="BP-3",
        triggered=triggered,
        severity=BP_CATEGORIES["BP-3"]["severity"],
        name=BP_CATEGORIES["BP-3"]["name"],
        detail=f"Found {len(nested)} nested reference paths"
        if triggered
        else f"Found {len(refs)} reference mentions, no deep nesting",
    )


def _check_bp4_inconsistent_terminology(content: str) -> BPCheckResult:
    """BP-4: Inconsistent terminology — mixing terms for same concept."""
    term_groups = [
        (["actor", "scraper", "crawler"], "actor/scraper/crawler"),
        (["run", "execution", "job"], "run/execution/job"),
        (["dataset", "results", "output"], "dataset/results/output"),
    ]

    inconsistencies = []
    content_lower = content.lower()
    for terms, label in term_groups:
        found = [t for t in terms if t in content_lower]
        if len(found) >= 3:
            inconsistencies.append(label)

    triggered = len(inconsistencies) > 0
    return BPCheckResult(
        check_id="BP-4",
        triggered=triggered,
        severity=BP_CATEGORIES["BP-4"]["severity"],
        name=BP_CATEGORIES["BP-4"]["name"],
        detail=f"Mixed terminology groups: {', '.join(inconsistencies)}"
        if triggered
        else "Terminology appears consistent",
    )


def _check_bp5_no_progressive_disclosure(content: str) -> BPCheckResult:
    """BP-5: Everything in one file, no layered structure."""
    has_references = bool(re.search(r"references?/", content, re.IGNORECASE))
    has_includes = bool(re.search(r"\{%\s*include", content, re.IGNORECASE))
    has_see_also = bool(
        re.search(r"see also|for more details|read more", content, re.IGNORECASE)
    )

    lines = content.splitlines()
    triggered = len(lines) > 100 and not (
        has_references or has_includes or has_see_also
    )

    return BPCheckResult(
        check_id="BP-5",
        triggered=triggered,
        severity=BP_CATEGORIES["BP-5"]["severity"],
        name=BP_CATEGORIES["BP-5"]["name"],
        detail="Long file with no references or progressive disclosure"
        if triggered
        else "File uses references or is compact enough",
    )


def _check_bp6_magic_constants(content: str) -> BPCheckResult:
    """BP-6: Hardcoded values without explanation."""
    magic_numbers = _MAGIC_NUMBER_PATTERN.findall(content)
    # Filter out common false positives
    real_magic = [
        m
        for m in magic_numbers
        if not any(fp in m.lower() for fp in ["example", "e.g.", "default"])
    ]

    triggered = len(real_magic) > 2
    return BPCheckResult(
        check_id="BP-6",
        triggered=triggered,
        severity=BP_CATEGORIES["BP-6"]["severity"],
        name=BP_CATEGORIES["BP-6"]["name"],
        detail=f"Found {len(real_magic)} magic constants: {', '.join(real_magic[:5])}"
        if triggered
        else f"Found {len(real_magic)} potential magic constants (within threshold)",
    )


def _check_bp7_duplication(content: str) -> BPCheckResult:
    """BP-7: Duplication between SKILL.md and references.

    Heuristic: if the SKILL.md mentions the same instructions that would be in
    referenced files (detected by large inline code blocks alongside reference paths).
    """
    has_references = bool(re.search(r"references?/", content, re.IGNORECASE))
    # Count large code blocks (>10 lines) — these might be duplicated from references
    code_blocks = re.findall(r"```[\s\S]*?```", content)
    large_blocks = [b for b in code_blocks if b.count("\n") > 10]

    triggered = has_references and len(large_blocks) >= 2
    return BPCheckResult(
        check_id="BP-7",
        triggered=triggered,
        severity=BP_CATEGORIES["BP-7"]["severity"],
        name=BP_CATEGORIES["BP-7"]["name"],
        detail=f"Has references + {len(large_blocks)} large code blocks (potential duplication)"
        if triggered
        else "No obvious duplication detected",
    )


def _check_bp8_when_to_read(content: str) -> BPCheckResult:
    """BP-8: References without 'when to read' guidance."""
    ref_mentions = re.findall(r"references?/\S+", content, re.IGNORECASE)
    if not ref_mentions:
        return BPCheckResult(
            check_id="BP-8",
            triggered=False,
            severity=BP_CATEGORIES["BP-8"]["severity"],
            name=BP_CATEGORIES["BP-8"]["name"],
            detail="No reference files mentioned",
        )

    # Check for guidance patterns near references
    has_guidance = bool(
        re.search(
            r"(read|consult|check|refer to|use)\s+\S*references?/",
            content,
            re.IGNORECASE,
        )
    )
    has_when = bool(
        re.search(
            r"(when|if|before|after|for)\s+.{0,40}references?/",
            content,
            re.IGNORECASE,
        )
    )

    triggered = not (has_guidance or has_when) and len(ref_mentions) >= 2
    return BPCheckResult(
        check_id="BP-8",
        triggered=triggered,
        severity=BP_CATEGORIES["BP-8"]["severity"],
        name=BP_CATEGORIES["BP-8"]["name"],
        detail=f"{len(ref_mentions)} references without usage guidance"
        if triggered
        else "References have adequate context",
    )


def run_bp_checks(skill_content: str, skill_name: str) -> list[BPCheckResult]:
    """Run all BP checks on a SKILL.md file. Returns list of BPCheckResult."""
    checks = [
        _check_bp1_token_budget,
        _check_bp2_poor_description,
        _check_bp3_deep_nesting,
        _check_bp4_inconsistent_terminology,
        _check_bp5_no_progressive_disclosure,
        _check_bp6_magic_constants,
        _check_bp7_duplication,
        _check_bp8_when_to_read,
    ]
    return [check(skill_content) for check in checks]


def bp_checks_to_run_results(
    checks: list[BPCheckResult],
    skill_name: str,
) -> list[RunResult]:
    """Convert BP check results to RunResult objects for the report pipeline."""
    triggered = [c for c in checks if c.triggered]
    if not triggered:
        summary = "All BP checks passed — no structural issues found."
    else:
        summary_lines = [f"**{len(triggered)}/{len(checks)} BP checks triggered:**\n"]
        for c in checks:
            status = "TRIGGERED" if c.triggered else "OK"
            badge = "🟠" if c.triggered else "🟢"
            summary_lines.append(
                f"- {badge} **{c.check_id}** [{c.severity}] {c.name}: {status} — {c.detail}"
            )
        summary = "\n".join(summary_lines)

    return [
        RunResult(
            scenario_id=f"bp-{skill_name}",
            model="bp-linter",
            response=summary,
            duration_s=0.0,
            cost_info="static analysis (no API call)",
        )
    ]
