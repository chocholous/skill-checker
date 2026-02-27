#!/usr/bin/env bash
# PostToolUse hook: log Apify Actor run costs from call-actor --json responses.
#
# Fires on every Bash tool use; exits 0 immediately for non-call-actor commands.
# Reads stdin JSON: {tool_input: {command}, tool_response: {stdout, stderr, exitCode}}
#
# Log format (tab-separated):  2024-01-15T10:30:00Z  actor=apify/google-search-scraper  usd=0.0042
# Override log path with APIFY_COST_LOG env var.

set -uo pipefail

LOG_FILE="${APIFY_COST_LOG:-$HOME/.apify-costs.log}"

# Read hook payload from stdin
INPUT=$(cat)

# Fast exit: only interested in call-actor + --json (cost data only present in --json mode)
COMMAND=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null || true)
[[ "$COMMAND" != *"call-actor"* ]] && exit 0
[[ "$COMMAND" != *"--json"* ]] && exit 0

# Try to extract _meta.usageTotalUsd from tool_response.stdout
# Note: only available when mcpc is called without output pipes that strip _meta
STDOUT=$(printf '%s' "$INPUT" | jq -r '.tool_response.stdout // ""' 2>/dev/null || true)
COST=$(printf '%s' "$STDOUT" | jq -r '._meta.usageTotalUsd // empty' 2>/dev/null || true)
[[ -z "$COST" ]] && exit 0

# Extract actor name from the command string
ACTOR=$(printf '%s' "$COMMAND" | sed -n 's/.*actor:="\([^"]*\)".*/\1/p' || true)
[[ -z "$ACTOR" ]] && ACTOR="unknown"

# Append log entry
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
printf '%s\tactor=%s\tusd=%s\n' "$TIMESTAMP" "$ACTOR" "$COST" >> "$LOG_FILE"
