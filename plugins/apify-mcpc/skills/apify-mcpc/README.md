# apify-mcpc skill

Invoke: `/apify-mcpc [use-case or search query]`

## Setup (one-time)

```bash
npm install -g @apify/mcpc
mcpc mcp.apify.com login                              # opens browser OAuth
mcpc mcp.apify.com connect @apify                     # full mode (Actor runs)
mcpc 'mcp.apify.com?tools=docs' connect @apify-docs  # docs-only mode
```

Verify setup:

```bash
bash ~/.claude/skills/apify-mcpc/scripts/check_apify.sh
```

## Use cases

8 marketing intelligence use cases + multi-actor workflow patterns:
audience analysis, brand monitoring, competitor intelligence, content analytics,
influencer discovery, lead generation, market research, trend analysis.

## Connection modes

- **Full mode** (`@apify`) — requires OAuth, runs Actors, costs Apify credits
- **Docs-only** (`@apify-docs`) — no auth needed, searches Apify/Crawlee docs only
