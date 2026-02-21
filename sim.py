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
import sys
from pathlib import Path

from sim_core import (
    DEFAULT_CONCURRENCY,
    DEFAULT_MODELS,
    load_manifest,
    load_scenarios,
    read_skill,
    run_scenario,
    save_reports,
    Scenario,
)


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
    print(
        f"Dry run: {len(scenarios)} scenarios × {len(models)} models = {total} calls\n"
    )
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
        "--model",
        "-m",
        action="append",
        help=f"Model to use (repeat for multiple). Default: {', '.join(DEFAULT_MODELS)}",
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
    args = parser.parse_args()

    # Load data
    all_scenarios = load_scenarios()
    manifest = load_manifest()
    models = args.model or DEFAULT_MODELS

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
    if args.scenario:
        scenarios = [s for s in scenarios if s.id == args.scenario]
        if not scenarios:
            print(f"Error: scenario '{args.scenario}' not found", file=sys.stderr)
            list_scenarios(all_scenarios)
            sys.exit(1)

    # List mode
    if args.list:
        list_scenarios(scenarios)
        return

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
    print(
        f"Running {total} calls ({len(scenarios)} scenarios × {len(models)} models, concurrency={args.concurrency})"
    )
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
        print(
            f"  [{completed}/{total}] {result.scenario_id} × {result.model}: {status} ({result.duration_s}s)"
        )
        results.append(result)

    # Generate reports
    output_path = Path(args.output) if args.output else None
    md_path, json_path = save_reports(scenarios, results, models, output_path)

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
