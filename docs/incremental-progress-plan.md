# Incremental progress + multi-model run

## Context

Scored run systém ukládá report JEN na konci celého runu. Pokud run crashne, data jsou ztracena. UI neaktualizuje heatmapu během runu — uživatel vidí jen progress bar. Pro 3 modely musí spustit 3 runy ručně.

Cíl: inkrementální ukládání po každém tasku, live refresh UI, multi-model podpora v jednom runu.

<!-- PHASE:1 -->
## Phase 1: Incremental save in sim_core

### Branch
`incremental-save-simcore`

### Scope

Přidat `save_scored_report_incremental(run_id, results, metadata)` do `sim_core.py`.

- Ukládá do `reports/scored_run_{run_id}.json`
- Atomický zápis: write do `.json.tmp` → `os.rename()` (prevents partial reads)
- JSON struktura identická s `save_scored_report` + přidané pole `run_id`
- `load_all_scored_reports()` beze změny — glob `scored_*.json` matchuje `scored_run_*.json`
- Existující `save_scored_report()` zůstává beze změny

```python
def save_scored_report_incremental(
    run_id: str,
    results: list[ScoredRun],
    metadata: dict,
) -> Path:
    """Overwrite the run's report file with current results (atomic)."""
    REPORTS_DIR.mkdir(exist_ok=True)
    path = REPORTS_DIR / f"scored_run_{run_id}.json"
    tmp_path = path.with_suffix(".json.tmp")
    data = {
        "type": "scored",
        "generated": datetime.now().isoformat(),
        "run_id": run_id,
        **metadata,
        "result_count": len(results),
        "results": [/* same structure as save_scored_report */],
    }
    tmp_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    tmp_path.rename(path)  # atomic on same filesystem
    return path
```

### Files to Create/Modify
- `sim_core.py` — přidat funkci `save_scored_report_incremental`

### Acceptance Criteria
- [ ] `save_scored_report_incremental` existuje a generuje validní JSON
- [ ] Soubor se jmenuje `scored_run_{run_id}.json`
- [ ] Zápis je atomický (tmp + rename)
- [ ] `load_all_scored_reports()` korektně načte soubory `scored_run_*.json`
- [ ] Existující `save_scored_report()` zůstává beze změny
- [ ] `.venv/bin/python -m pytest tests/ -v` — all pass

### Tests Required
- `.venv/bin/python -m pytest tests/ -v` — stávající testy prochází
- Manuální test: zavolat `save_scored_report_incremental("test123", [...], {...})`, ověřit že soubor existuje a je validní JSON
<!-- /PHASE:1 -->

<!-- PHASE:2 DEPENDS:1 -->
## Phase 2: Runner incremental save + multi-model

### Branch
`runner-incremental-multimodel`

### Scope

Upravit `server/services/runner.py`:

**A. Multi-model podpora:**
- `ScoredRunState.model: str` → `models: list[str]`
- Task list builder přidá model jako vnitřní dimenzi:
  ```python
  for scenario in scenarios:
      for skill in get_target_skills(scenario, manifest):
          for model in state.models:
              tasks_list.append((scenario, skill, model))
  ```
- `run_one_scored()` přijímá parametr `model`
- SSE progress event rozšířen o pole `"model"` v data dict
- Metadata: `"models": state.models` místo `"model": state.model`

**B. Inkrementální save:**
- Přidat `_save_lock: asyncio.Lock` do `ScoredRunState`
- Po každém dokončeném `run_scored_scenario()`:
  1. Append result do `state.results`
  2. `async with state._save_lock:` → `save_scored_report_incremental(state.run_id, state.results, metadata)`
- Odebrat finální `save_scored_report()` volání na konci runu (inkrementální save to pokrývá)
- Try/except kolem `asyncio.gather` — při crashi provede jeden poslední incremental save

**C. SSE progress data rozšíření:**
- Stávající: `{"scenario_id": "...", "skill": "...", "status": "ok", "duration_s": 12.3, "error": null}`
- Nově přidat: `"model": "sonnet"` do každého progress eventu

### Files to Create/Modify
- `server/services/runner.py` — multi-model task list, incremental save, save lock, model v SSE

### Acceptance Criteria
- [ ] `ScoredRunState` má `models: list[str]` místo `model: str`
- [ ] Task list iteruje přes (scenario × skill × model) cross-product
- [ ] Po každém tasku se zavolá `save_scored_report_incremental`
- [ ] Save je chráněn asyncio.Lock
- [ ] SSE progress eventy obsahují pole `model`
- [ ] Při crashi se uloží partial data
- [ ] Finální `save_scored_report` volání je odebráno
- [ ] `.venv/bin/python -m pytest tests/ -v` — all pass

### Tests Required
- `.venv/bin/python -m pytest tests/ -v` — stávající testy prochází
- Manuální test: spustit run přes API s `models: ["haiku"]`, ověřit inkrementální soubor se vytváří
<!-- /PHASE:2 -->

<!-- PHASE:3 DEPENDS:2 -->
## Phase 3: Heatmap router multi-model request

### Branch
`heatmap-router-multimodel`

### Scope

Upravit `server/routers/heatmap.py`:

- `ScoredRunRequest`: `model: str = "sonnet"` → `models: list[str] = ["sonnet"]`
- Validace: každý model musí být z `["sonnet", "opus", "haiku"]`, neprázdný list
- Total tasks kalkulace: `total *= len(body.models)` (zahrnuje model dimenzi)
- Předat `models=body.models` do `run_manager.start_scored_run()`
- Update `start_scored_run()` volání dle nového podpisu z Phase 2

### Files to Create/Modify
- `server/routers/heatmap.py` — ScoredRunRequest model, validace, total tasks

### Acceptance Criteria
- [ ] `POST /api/heatmap/run` přijímá `{"models": ["sonnet", "opus"]}`
- [ ] Neplatné modely vrací 400 error
- [ ] Prázdný models list vrací 400 error
- [ ] Response `total` správně počítá scenario × skill × model
- [ ] Backward kompatibilita: `{"model": "sonnet"}` stále funguje (nebo je nahrazeno `models`)
- [ ] `.venv/bin/python -m pytest tests/ -v` — all pass

### Tests Required
- `.venv/bin/python -m pytest tests/ -v` — stávající testy prochází
- `curl -X POST http://127.0.0.1:20001/api/heatmap/run -H 'Content-Type: application/json' -d '{"domains": ["market-research"], "models": ["haiku"]}'` — vrací run_id a total
<!-- /PHASE:3 -->

<!-- PHASE:4 DEPENDS:3 -->
## Phase 4: Frontend — live refresh + multi-model UI

### Branch
`frontend-live-multimodel`

### Scope

**A. `web/src/api/client.ts`:**
- `startScoredRun` options: `model?: string` → `models?: string[]`

**B. `web/src/pages/Heatmap.tsx` — throttled cache invalidation:**
- Přidat `useRef` pro throttle:
  ```typescript
  const INVALIDATION_THROTTLE_MS = 5000;
  const lastInvalidationRef = useRef<number>(0);
  ```
- V useEffect sledující `events`: po každém completion eventu (status !== "running"), pokud uplynulo >= 5s od posledního refreshe, invalidovat `["heatmap-skills"]` a `["heatmap-domain"]` queries
- Stávající isDone invalidace zůstává jako fallback

**C. `web/src/pages/Heatmap.tsx` — multi-model UI:**
- State: `selectedModel: string` → `selectedModels: string[]` (default: `["sonnet"]`)
- Model selection: checkboxy pro sonnet/opus/haiku místo dropdown
- "Run All Models" tlačítko: předvyplní všechny 3 modely
- `handleRunScored`: předat `models: selectedModels` do API
- Progress text: `"15 / 201 completed (sonnet, opus, haiku)"`
- Run summary: `"13 domains × ~67 scenarios × 3 models"`

### Files to Create/Modify
- `web/src/api/client.ts` — `models?: string[]` v startScoredRun
- `web/src/pages/Heatmap.tsx` — throttled refresh, multi-model checkboxy, Run All

### Acceptance Criteria
- [ ] Během runu se heatmap buňky plní průběžně (~každých 5s refresh)
- [ ] Model selection: checkboxy pro 3 modely
- [ ] "Run All" funkčnost (all domains + all models)
- [ ] Progress zobrazuje celkový počet včetně model dimenze
- [ ] API volání posílá `models` array
- [ ] `cd web && npm run build && npm run lint` — 0 errors

### Tests Required
- `cd web && npm run build` — 0 errors
- `cd web && npm run lint` — 0 errors
- Playwright vizuální test: spustit run, ověřit že buňky se plní průběžně
<!-- /PHASE:4 -->

<!-- PHASE:5 DEPENDS:4 -->
## Phase 5: Full re-run + verifikace

### Branch
`full-rerun-verification`

### Scope

End-to-end verifikace celého systému:

1. Spustit full scored run: 13 domén × 3 modely přes API
2. Ověřit inkrementální ukládání: soubor `scored_run_*.json` roste s každým taskem
3. Ověřit live UI refresh: buňky v heatmapě se plní průběžně
4. Ověřit multi-model sloupce: každý domain tab ukazuje haiku/opus/sonnet sloupce
5. Kill test: ukončit run uprostřed → partial report existuje a správně se načte
6. Ověřit backward kompatibilitu: staré `scored_{timestamp}.json` reporty se stále načítají

### Files to Create/Modify
- Žádné nové soubory — pouze verifikace

### Acceptance Criteria
- [ ] `cd web && npm run build && npm run lint` — 0 errors
- [ ] `.venv/bin/python -m pytest tests/ -v` — all pass
- [ ] Full run s 3 modely startuje a produkuje výsledky
- [ ] Buňky v heatmapě se plní průběžně
- [ ] Partial report je validní po kill
- [ ] Staré reporty se stále načítají

### Tests Required
- `cd web && npm run build && npm run lint` — 0 errors
- `.venv/bin/python -m pytest tests/ -v` — all pass
- Manuální end-to-end test s Playwright
<!-- /PHASE:5 -->
