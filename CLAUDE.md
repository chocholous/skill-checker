# Skill Checker

CLI nástroj pro testování kvality SKILL.md souborů — posílá skill + testovací prompt Claude modelům a porovnává jejich reasoning o složitostech, edge cases a přístupu.

## Účel

Ověřit, jak dobře SKILL.md instrukce připraví agenta na reálné uživatelské prompty. Identifikuje mezery, chybějící guidance a potenciální selhání napříč 5 vrstvami: WF (workflow), DK (domain knowledge), BP (best practices — statický linter), APF (Apify platform) a SEC (security).

## Architektura

- **`sim.py`** — hlavní CLI, async. Používá `claude -p` pro volání modelů (ne Agent SDK, ne API přímo).
- **`sim_core.py`** — shared logika: taxonomie, dataclass, loading, execution, reporting.
- **`bp_linter.py`** — statický linter pro BP checky (bez API volání).
- **`skills_manifest.yaml`** — absolutní cesty ke SKILL.md souborům (žádné kopie → žádný drift)
- **`scenarios/*.yaml`** — testovací scénáře po kategoriích s expected_checks
- **`reports/`** — gitignored výstup (Markdown + JSON)

## 13 testovaných skillů

- 9 dispatcher skillů (shared 5-step workflow) z `apify-marketing-intelligence/.agents/skills/`
- 1 dispatcher outlier: apify-ecommerce (inline schema, no mcpc)
- 2 dev skillů: apify-actor-development, apify-actorization
- 1 mcpc skill: mcpc-apify z `apify-mcpc-plugin/`

## Scored mode: domain scénáře × 3 skilly

V scored mode (`--scored`) se každý non-dev domain scénář automaticky spouští proti 3 skillům: specialist + apify-mcpc + apify-ultimate-scraper. Dev domény (actor-development, actorization) běží jen proti specialist skillu.

## 23 category scénářů ve 4 souborech + BP linter per-skill

| Soubor | Cat | Počet | Modely |
|---|---|---|---|
| `wf_scenarios.yaml` | WF | 5 | sonnet |
| `dk_scenarios.yaml` | DK | 6 | sonnet, opus, haiku |
| `apf_scenarios.yaml` | APF | 10 | sonnet, opus |
| `sec_scenarios.yaml` | SEC | 2 | sonnet |
| (bp-linter per-skill) | BP | 7 | bp-linter (static) |

Total: 45 API volání + 7 BP checks = 52 celkem

## Per-category model strategie

- `--model` CLI = full override (přepíše per-category defaults)
- Bez `--model`: každá kategorie používá své default modely
- BP linter běží vždy per-skill bez API volání

## Použití

```bash
# Spouštěj z terminálu, NE z Claude Code session (claude -p nesting nefunguje)

python3 sim.py --list              # Přehled scénářů
python3 sim.py --dry-run           # Co se spustí + odhad ceny
python3 sim.py -s wf-scraper-basic -m haiku   # Jeden scénář, jeden model
python3 sim.py -m sonnet -m opus   # Dva modely (override), všechny scénáře
python3 sim.py                     # Plný běh (~52 checks, ~$2-7)
python3 sim.py -c 5                # Zvýšit concurrency (default 3)
```

## 5-Category Taxonomy (37 checků)

### WF — Workflow Quality (6)
| ID | Severity | Název |
|---|---|---|
| WF-1 | HIGH | Missing workflow |
| WF-2 | MED | No feedback loop |
| WF-3 | HIGH | Wrong degrees of freedom |
| WF-4 | MED | Missing examples |
| WF-5 | MED | No scope detection |
| WF-6 | MED | Linear-only workflow |

### DK — Domain Knowledge (8)
| ID | Severity | Název |
|---|---|---|
| DK-1 | HIGH | Actor selection ambiguity |
| DK-2 | MED | Output variability |
| DK-3 | MED | Unrealistic expectations |
| DK-4 | MED | Time-sensitive content |
| DK-5 | MED | No scheduling pattern |
| DK-6 | HIGH | Missing domain caveats |
| DK-7 | HIGH | Input correctness validation |
| DK-8 | MED | Data completeness awareness |

### BP — Best Practices (8) — static linter, no API
| ID | Severity | Název |
|---|---|---|
| BP-1 | HIGH | Token budget exceeded (>500 lines) |
| BP-2 | MED | Poor description |
| BP-3 | LOW | Deep reference nesting |
| BP-4 | LOW | Inconsistent terminology |
| BP-5 | MED | No progressive disclosure |
| BP-6 | LOW | Magic constants |
| BP-7 | MED | Duplication between SKILL.md and references |
| BP-8 | MED | Missing "when to read" guidance |

### APF — Apify Platform Awareness (13)
| ID | Severity | Název |
|---|---|---|
| APF-1 | CRIT | Path resolution |
| APF-2 | HIGH | Schema drift |
| APF-3 | HIGH | Expected tool not available |
| APF-4 | HIGH | Input schema gotchas |
| APF-5 | MED | No resource budgeting |
| APF-6 | MED | Run observability |
| APF-7 | MED | Output storage confusion |
| APF-8 | MED | Store search mismatch |
| APF-9 | LOW | Actor metadata ignorance |
| APF-10 | MED | Proxy unawareness |
| APF-11 | MED | Multi-actor orchestration gap |
| APF-12 | MED | Memory and scaling limits |
| APF-13 | LOW | Parallelization patterns |

### SEC — Security (2)
| ID | Severity | Název |
|---|---|---|
| SEC-1 | HIGH | Auth anti-patterns |
| SEC-4 | MED | Credential exposure |

## Stack

- Language: Python 3.13, TypeScript 5.9
- Frontend: React 19, Vite 7, styled-components 6, @apify/ui-library 1.124
- Backend: FastAPI (uvicorn), Python
- Package managers: pip (Python), npm (Node.js)
- Testing: pytest (Python), ESLint (TypeScript)

## Testing Conventions

- Python tests: `pytest tests/ -v`
- Frontend lint: `cd web && npm run lint`
- Frontend build check: `cd web && npm run build`
- Full test: `make test` (pytest + dry-run + lint)

## Code Quality Standards

- No hardcoded hex colors — use theme.color.* tokens
- No hardcoded px/rem — use theme.space.* or theme.radius.*
- Typography only via <Text> and <Heading> components
- $ prefix for transient styled-components props
- ESLint for TypeScript, ruff for Python

## Project Structure

- `sim.py`, `sim_core.py`, `bp_linter.py` — CLI tool (Python)
- `server/` — FastAPI backend
- `web/` — React frontend (Vite)
  - `web/src/components/` — shared components
  - `web/src/pages/` — route pages
  - `web/src/api/` — API client
  - `web/src/hooks/` — React hooks
- `scenarios/` — YAML test scenarios (4 files by category: wf, dk, apf, sec)
- `design-system/` — @apify/ui-library reference docs
- `skills/` — cloned agent-skills repo (gitignored subdir)
- `reports/` — generated reports (gitignored)

## Config Management

- Ports configured via `.env` (gitignored), template in `.env.example`
- `BACKEND_PORT` — FastAPI/uvicorn port (default: 8420)
- `FRONTEND_PORT` — Vite dev server port (default: 5173)
- Vite proxy: /api → http://127.0.0.1:$BACKEND_PORT
- CORS: automatically allows http://localhost:$FRONTEND_PORT + http://127.0.0.1:$FRONTEND_PORT
- Makefile, vite.config.ts, server/main.py all read from `.env`

## Dependencies

- Python 3.13 (system)
- PyYAML (system-level, no venv needed)
- `claude` CLI v Claude Code
