---
name: apify-status
description: "Shows current Apify/mcpc session state and run cost history. Use when the user asks about their Apify usage, mcpc session status, costs, or wants to see what actors were run recently."
allowed-tools: Bash(mcpc *), Bash(tail *), Bash(awk *)
argument-hint: "[sessions | costs | all]"
---

# apify-status

Run the following commands and present the results to the user.

## Sessions

Current mcpc sessions (shows which MCP servers are connected):

```bash
mcpc
```

## Cost history

Recent actor runs (last 20 entries from cost log):

```bash
tail -n 20 ~/.apify-costs.log
```

Total spend across all logged runs:

```bash
awk -F'\t' '{match($0,/usd=([0-9.]+)/,a); sum+=a[1]} END{printf "Total: $%.4f USD\n", sum}' ~/.apify-costs.log
```

If either cost command fails (file not found), inform the user that cost tracking starts automatically once they run an actor with `call-actor ... --json`. No manual setup needed.

## Notes

- **Cost log**: `~/.apify-costs.log` — auto-populated by a PostToolUse hook on every `call-actor --json` call. Override path with `$APIFY_COST_LOG`.
- **Sessions**: managed via `mcpc mcp.apify.com connect @apify`. If sessions are missing, run the setup commands from the `/apify-mcpc` skill README.
