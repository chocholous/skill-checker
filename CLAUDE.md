# Skill Checker

CLI nástroj pro testování kvality SKILL.md souborů — posílá skill + testovací prompt Claude modelům a porovnává jejich reasoning o složitostech, edge cases a přístupu.

## Účel

Ověřit, jak dobře SKILL.md instrukce připraví agenta na reálné uživatelské prompty. Identifikuje mezery, chybějící guidance a potenciální selhání napříč 10 kategoriemi složitosti (CAT-1 až CAT-10).

## Architektura

- **`sim.py`** — hlavní CLI, async, ~270 řádků. Používá `claude -p` pro volání modelů (ne Agent SDK, ne API přímo).
- **`skills_manifest.yaml`** — absolutní cesty ke SKILL.md souborům (žádné kopie → žádný drift)
- **`scenarios/*.yaml`** — testovací scénáře s expected_complexities
- **`reports/`** — gitignored výstup (Markdown + JSON)

## 13 testovaných skillů

- 9 dispatcher skillů (shared 5-step workflow) z `apify-marketing-intelligence/.agents/skills/`
- 1 dispatcher outlier: apify-ecommerce (inline schema, no mcpc)
- 2 dev skillů: apify-actor-development, apify-actorization
- 1 mcpc skill: mcpc-apify z `apify-skills-audit/`

## 18 scénářů ve 4 kategoriích

| Soubor | Počet | Co testuje |
|---|---|---|
| `dispatcher_common.yaml` | 5 | ultimate-scraper — basic, chain, limits, prereqs, ambiguity |
| `dispatcher_specific.yaml` | 5 | per-skill edge cases — filtering, aggregation, GDPR, outlier |
| `dev_skills.yaml` | 3 | actor dev + actorization — new, convert, debug |
| `mcpc_skills.yaml` | 5 | discovery, schema, run+debug, clarification, constraints |

## Použití

```bash
# Spouštěj z terminálu, NE z Claude Code session (claude -p nesting nefunguje)

python3 sim.py --list              # Přehled scénářů
python3 sim.py --dry-run           # Co se spustí + odhad ceny
python3 sim.py -s dc-1 -m haiku   # Jeden scénář, jeden model
python3 sim.py -m sonnet -m opus   # Dva modely, všechny scénáře
python3 sim.py                     # Plný běh (54 calls, ~$3-8)
python3 sim.py -c 5                # Zvýšit concurrency (default 3)
```

## 10 kategorií složitosti (CAT-1 → CAT-10)

1. `${CLAUDE_PLUGIN_ROOT}` undefined — zlomí run_actor.js cestu
2. Dynamic schema via mcpc — latence + hard dependency
3. Žádný resource management (--memory, concurrency)
4. Žádný parallel actor guidance
5. Actor duplicity — stejný actor v 6-8 skillech s různým popisem
6. Žádná input validation (min values, destructive defaults)
7. mcpc not installed by default vs. "no need to check upfront"
8. Token extraction anti-pattern
9. Ecommerce outlier — inline schema může zastarat
10. Dev skills mají references/, dispatcher skills nemají

## Dependencies

- Python 3.13 (system)
- PyYAML (system-level, no venv needed)
- `claude` CLI v Claude Code
