#!/usr/bin/env bash
# Verify prerequisites for mcpc-apify skill
set -euo pipefail

errors=0

# 1. Check mcpc is installed
if command -v mcpc &>/dev/null; then
  echo "✓ mcpc $(mcpc --version 2>/dev/null || echo '?')"
else
  echo "✗ mcpc not found. Install: npm install -g @apify/mcpc"
  errors=$((errors + 1))
fi

# 2. Check OAuth profile for mcp.apify.com
if command -v mcpc &>/dev/null; then
  profiles=$(mcpc 2>&1 || true)
  if echo "$profiles" | grep -q 'mcp.apify.com'; then
    echo "✓ OAuth profile for mcp.apify.com exists"
  else
    echo "⚠ No OAuth profile for mcp.apify.com — run: mcpc mcp.apify.com login"
  fi
fi

# 3. Check existing sessions (match exact session names)
if command -v mcpc &>/dev/null; then
  sessions=$(mcpc 2>&1 || true)
  if echo "$sessions" | grep -q '@apify →'; then
    echo "✓ Session @apify exists"
  else
    echo "— No @apify session (create with: mcpc mcp.apify.com connect @apify)"
  fi
  if echo "$sessions" | grep -q '@apify-docs →'; then
    echo "✓ Session @apify-docs exists"
  else
    echo "— No @apify-docs session (create with: mcpc 'mcp.apify.com?tools=docs' connect @apify-docs)"
  fi
fi

if [ "$errors" -gt 0 ]; then
  echo ""
  echo "Found $errors issue(s). Fix them before proceeding."
  exit 1
fi

echo ""
echo "Ready to use mcpc-apify skill."
