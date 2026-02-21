# Skill Checker

CLI nástroj pro testování kvality SKILL.md souborů — posílá skill + testovací prompt Claude modelům a porovnává jejich reasoning o složitostech, edge cases a přístupu.

## Účel

Ověřit, jak dobře SKILL.md instrukce připraví agenta na reálné uživatelské prompty. Identifikuje mezery, chybějící guidance a potenciální selhání napříč dvěma vrstvami: GEN (obecná kvalita skillů) a APF (Apify platform pasti).

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

## Taxonomie kategorií (GEN + APF se severity)

### GEN — Obecné skill quality problémy (13 kategorií)

| ID | Severity | Název | Co testuje |
|---|---|---|---|
| GEN-1 | HIGH | Token budget exceeded | SKILL.md nad 500 řádků; zbytečný kontext |
| GEN-2 | MEDIUM | Poor description | Chybí trigger conditions, není 3rd person, vágní |
| GEN-3 | HIGH | Missing workflow | Komplexní task bez kroků, checklistu |
| GEN-4 | MEDIUM | No feedback loop | Chybí validate→fix→retry cyklus |
| GEN-5 | HIGH | Wrong degrees of freedom | Příliš rigidní nebo příliš volné |
| GEN-6 | LOW | Deep reference nesting | Reference 2+ úrovně hluboko |
| GEN-7 | MEDIUM | Time-sensitive content | Hardcoded verze, schémata bez údržby |
| GEN-8 | LOW | Inconsistent terminology | Míchání termínů pro stejný koncept |
| GEN-9 | HIGH | Unverified dependencies | Předpokládá instalované tools bez checku |
| GEN-10 | MEDIUM | No progressive disclosure | Vše v jednom souboru |
| GEN-11 | MEDIUM | Missing examples | Chybí input/output příklady |
| GEN-12 | HIGH | Scripts punt errors | Skripty selhávají bez vysvětlení |
| GEN-13 | LOW | Magic constants | Hardcoded hodnoty bez vysvětlení |

### APF — Apify platform pasti (11 kategorií)

| ID | Severity | Název | Co testuje |
|---|---|---|---|
| APF-1 | CRITICAL | Path resolution | Skill path nefunguje across setups |
| APF-2 | HIGH | Schema drift | Actor schéma se změní, skill má zastaralé příklady |
| APF-3 | HIGH | Expected tool not available | Skill předpokládá tool (mcpc, CLI, MCP server) který není dostupný |
| APF-4 | HIGH | Input validation gaps | Destructive defaults, chybí min/max limity |
| APF-5 | HIGH | Actor selection ambiguity | Víc actorů pro stejný úkol, žádná guidance |
| APF-6 | MEDIUM | No resource budgeting | Chybí memory, timeout, concurrency, cost guidance |
| APF-7 | MEDIUM | Run observability | Chybí debugging guidance — logy, konzole |
| APF-8 | MEDIUM | Auth management | Token/OAuth anti-patterns |
| APF-9 | LOW | Output variability | Různé actory vrací různé tvary dat |
| APF-10 | MEDIUM | No scheduling pattern | Jen one-shot, ne recurring use cases |
| APF-11 | MEDIUM | Multi-actor orchestration | Chybí řetězení actorů guidance |

## Dependencies

- Python 3.13 (system)
- PyYAML (system-level, no venv needed)
- `claude` CLI v Claude Code
