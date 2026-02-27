#!/usr/bin/env python3
"""
Skill Checker — CLI tool that sends SKILL.md + test prompts to Claude models
and compares their reasoning about complexities, edge cases, and approach.

Usage:
    python sim.py                           # Run all scenarios on all models
    python sim.py --scenario dc-1           # Run single scenario
    python sim.py --model sonnet            # Single model (overrides per-category defaults)
    python sim.py --dry-run                 # Show what would run
    python sim.py --list                    # List all scenarios
    python sim.py --concurrency 5           # Max parallel calls (default: 3)
"""

import argparse
import asyncio
import sys
import uuid
from pathlib import Path

from bp_linter import bp_checks_to_run_results, run_bp_checks
from sim_core import (
    DEFAULT_CONCURRENCY,
    Scenario,
    create_run_snapshot,
    get_scenario_models,
    get_target_skills,
    load_domain_scenarios,
    load_manifest,
    load_scenarios,
    read_skill,
    run_scenario,
    run_scored_scenario,
    save_reports,
    save_scored_report,
    snapshot_to_metadata,
)


# --- CLI ---


def list_scenarios(scenarios: list[Scenario]) -> None:
    """Print scenario list."""
    print(f"{'ID':<16} {'Cat':<5} {'Skill':<35} {'Name'}")
    print("-" * 100)
    for s in scenarios:
        print(f"{s.id:<16} {s.category:<5} {s.target_skill:<35} {s.name}")
    print(f"\nTotal: {len(scenarios)} scenarios")


def dry_run(
    scenarios: list[Scenario],
    cli_models: list[str] | None,
    manifest: dict,
) -> None:
    """Print what would be executed."""
    api_calls = 0
    bp_calls = 0

    for s in scenarios:
        models = get_scenario_models(s, cli_models)
        for m in models:
            if m == "bp-linter":
                continue  # BP linter doesn't count as API call
            print(f"  [{s.id}] ({s.category}) {s.name} → {m}")
            api_calls += 1

    # BP linter runs per-skill
    skills_in_scenarios = {s.target_skill for s in scenarios}
    for skill_name in sorted(skills_in_scenarios):
        print(f"  [bp-{skill_name}] (BP) Best Practices linter → bp-linter")
        bp_calls += 1

    total = api_calls + bp_calls
    print(
        f"\nDry run: {len(scenarios)} scenarios + {bp_calls} BP checks = {total} total ({api_calls} API calls, {bp_calls} static)"
    )
    est_low = api_calls * 0.05
    est_high = api_calls * 0.15
    print(f"Estimated cost: ${est_low:.2f} - ${est_high:.2f} (BP checks are free)")


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Skill Checker — test SKILL.md quality with Claude models"
    )
    parser.add_argument(
        "--scenario",
        "-s",
        action="append",
        dest="scenarios",
        metavar="SCENARIO_ID",
        help="Run specific scenario by ID (repeat for multiple)",
    )
    parser.add_argument(
        "--model",
        "-m",
        action="append",
        help="Model override (repeat for multiple). Overrides per-category defaults.",
    )
    parser.add_argument("--skill", help="Filter scenarios by target_skill")
    parser.add_argument("--dry-run", action="store_true", help="Show what would run")
    parser.add_argument("--list", action="store_true", help="List all scenarios")
    parser.add_argument(
        "--concurrency",
        "-c",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help=f"Max concurrent claude -p calls (default: {DEFAULT_CONCURRENCY})",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path (auto-generated if not set)",
    )
    parser.add_argument(
        "--scored",
        action="store_true",
        help="Run domain-based scored analysis (heatmap mode)",
    )
    parser.add_argument(
        "--domain",
        "-d",
        help="Filter by domain (only with --scored)",
    )
    args = parser.parse_args()

    # --- Scored mode (domain-based heatmap) ---
    if args.scored:
        manifest = load_manifest()
        domain_scenarios = load_domain_scenarios()
        model = args.model[0] if args.model else "sonnet"

        if args.domain:
            if args.domain not in domain_scenarios:
                print(
                    f"Error: domain '{args.domain}' not found. Available: {', '.join(sorted(domain_scenarios.keys()))}",
                    file=sys.stderr,
                )
                sys.exit(1)
            domain_scenarios = {args.domain: domain_scenarios[args.domain]}

        # Build task list
        task_list: list[tuple[Scenario, str]] = []
        for domain_id, scenarios_list in domain_scenarios.items():
            for scenario in scenarios_list:
                target_skills = get_target_skills(scenario, manifest)
                for skill_name in target_skills:
                    task_list.append((scenario, skill_name))

        total = len(task_list)

        # Create snapshot
        run_id = uuid.uuid4().hex[:12]
        skill_names_used = sorted({sk for _, sk in task_list})
        scenario_files_used = sorted({s.source_file for s, _ in task_list})
        snapshot = create_run_snapshot(
            run_id, manifest, skill_names_used, scenario_files_used
        )

        print(
            f"Scored run: {total} tasks, model={model}, concurrency={args.concurrency}"
        )

        semaphore = asyncio.Semaphore(args.concurrency)
        scored_results = []
        completed = 0
        for coro in asyncio.as_completed(
            [
                run_scored_scenario(s, sk, model, manifest, semaphore)
                for s, sk in task_list
            ]
        ):
            result = await coro
            completed += 1
            status = "OK" if not result.error else "ERR"
            print(
                f"  [{completed}/{total}] {result.scenario_id} × {result.skill}: {status} ({result.duration_s:.1f}s)"
            )
            scored_results.append(result)

        metadata = {
            "model": model,
            "domains": list(domain_scenarios.keys()),
            "concurrency": args.concurrency,
            "snapshot": snapshot_to_metadata(snapshot),
        }
        report_path = save_scored_report(scored_results, metadata)
        print(f"\nScored report saved: {report_path}")

        # Summary
        pass_count = sum(
            1 for r in scored_results for c in r.checks if c.result == "pass"
        )
        fail_count = sum(
            1 for r in scored_results for c in r.checks if c.result == "fail"
        )
        unclear_count = sum(
            1 for r in scored_results for c in r.checks if c.result == "unclear"
        )
        print(f"Results: {pass_count} pass, {fail_count} fail, {unclear_count} unclear")
        return

    # --- Standard mode ---

    # Load data
    all_scenarios = load_scenarios()
    manifest = load_manifest()
    cli_models = args.model  # None if not specified = use per-category defaults

    # Filter scenarios
    scenarios = all_scenarios
    if args.skill:
        scenarios = [s for s in scenarios if s.target_skill == args.skill]
        if not scenarios:
            print(
                f"Error: no scenarios found for skill '{args.skill}'", file=sys.stderr
            )
            list_scenarios(all_scenarios)
            sys.exit(1)
    if args.scenarios:
        selected_ids = set(args.scenarios)
        scenarios = [s for s in scenarios if s.id in selected_ids]
        missing = selected_ids - {s.id for s in scenarios}
        if missing:
            print(
                f"Error: scenario(s) not found: {', '.join(sorted(missing))}",
                file=sys.stderr,
            )
            list_scenarios(all_scenarios)
            sys.exit(1)

    # List mode
    if args.list:
        list_scenarios(scenarios)
        return

    # Dry run
    if args.dry_run:
        dry_run(scenarios, cli_models, manifest)
        return

    # Validate skills exist
    for s in scenarios:
        try:
            read_skill(manifest, s.target_skill)
        except (ValueError, FileNotFoundError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    # Execute — each scenario runs on its own models
    semaphore = asyncio.Semaphore(args.concurrency)
    tasks = []
    all_models_used = set()

    for scenario in scenarios:
        models = get_scenario_models(scenario, cli_models)
        for model in models:
            if model == "bp-linter":
                continue  # Handled separately below
            all_models_used.add(model)
            tasks.append(run_scenario(scenario, model, manifest, semaphore))

    # Run BP linter per-skill (no API calls)
    skills_in_scenarios = {s.target_skill for s in scenarios}
    bp_results = []
    for skill_name in sorted(skills_in_scenarios):
        skill_content = read_skill(manifest, skill_name)
        checks = run_bp_checks(skill_content, skill_name)
        bp_results.extend(bp_checks_to_run_results(checks, skill_name))

    total_api = len(tasks)
    total = total_api + len(bp_results)
    print(
        f"Running {total} checks ({total_api} API calls + {len(bp_results)} BP linter, concurrency={args.concurrency})"
    )

    # Print BP results immediately (they're instant)
    for r in bp_results:
        print(f"  [BP] {r.scenario_id} × bp-linter: OK (0.0s)")

    # Run API calls
    completed = 0
    results = list(bp_results)  # Start with BP results
    all_models_used.add("bp-linter")
    for coro in asyncio.as_completed(tasks):
        result = await coro
        completed += 1
        status = "OK" if not result.error else "ERR"
        print(
            f"  [{completed + len(bp_results)}/{total}] {result.scenario_id} × {result.model}: {status} ({result.duration_s}s)"
        )
        results.append(result)

    # Generate reports
    output_path = Path(args.output) if args.output else None

    # Create BP pseudo-scenarios for report
    bp_scenarios = [
        Scenario(
            id=f"bp-{skill_name}",
            name=f"BP linter: {skill_name}",
            prompt="(static analysis)",
            target_skill=skill_name,
            source_file="(bp-linter)",
            category="BP",
        )
        for skill_name in sorted(skills_in_scenarios)
    ]
    all_scenarios_for_report = list(scenarios) + bp_scenarios

    md_path, json_path = save_reports(
        all_scenarios_for_report, results, sorted(all_models_used), output_path
    )

    print("\nReports saved:")
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
