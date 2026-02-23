# Migrace Skill Checker UI: Tailwind → @apify/ui-library

## Context

Web UI skill-checkeru pouziva Tailwind CSS pro styling. Nahradit za `@apify/ui-library` + `styled-components`, aby appka vypadala konzistentne s Apify platformou. Design system reference je v `design-system/`. Balicky uz nainstalovane: `@apify/ui-library@1.124.1`, `styled-components@^6.3.11`, `@apify/ui-icons@1.27.2`.

## Overene predpoklady

- `html { font-size: 62.5% }` (1rem = 10px) — NUTNE, knihovna predpoklada 10px base (bodyM=1.4rem=14px, space8=0.8rem=8px)
- `UiDependencyProvider` — prijima `dependencies` objekt (NE individualni props)
- `InternalLink` — prijima `href` (NE `to`), adapter mapuje `href` → React Router `to`
- `styled(NavLink)` — BEZPECNE, pouzit `&.active` pro active state
- `SimpleMarkdown` — exportovana, vyzaduje UiDependencyProvider, nahradi react-markdown
- Shadow CSS vars (`--shadow-1` az `--shadow-5`) — MANUALNI definice nutna
- Barvy vyhradne pres `theme.color.*`, spacing pres `theme.space.*`, typografie pres `<Text>`/`<Heading>`

## Kriticke design-system reference (precist pred implementaci)

- `design-system/setup.md` — bootstrap vzor (GlobalStyle, UiDependencyProvider, fonty)
- `design-system/components.md` — kompletni katalog komponent s props
- `design-system/colors.md` — semanticke barvy a palety
- `design-system/tokens.md` — spacing, radius, shadows, transitions
- `design-system/typography.md` — Text/Heading komponenty
- `design-system/icons.md` — 168 ikon z @apify/ui-icons
- `design-system/agent-instructions.md` — zero-tolerance pravidla

## Kriticka omezeni (vsechny faze)

1. NIKDY hardcoded hex barvy — vzdy `theme.color.*`
2. NIKDY hardcoded px/rem — vzdy `theme.space.*` nebo `theme.radius.*`
3. NIKDY font properties primo — vzdy `<Text>` nebo `<Heading>`
4. VZDY `$` prefix pro transient styled-components props
5. VZDY importy v poradi: react → styled-components → @apify/ui-library + @apify/ui-icons → lokalni

## Execution Groups

- Group A: [Phase 1] — solo (infrastructure)
- Group B: [Phase 2] — solo (components, depends on 1)
- Group C: [Phase 3, Phase 4] — parallel (pages, both depend on 2)
- Group D: [Phase 5] — solo (cleanup, depends on 3+4)

---

<!-- PHASE:1 -->
## Phase 1: Infrastructure

### Branch
`phase-1-infrastructure`

### Scope
Setup @apify/ui-library infrastructure: GlobalStyle with CSS variables, UiDependencyProvider, font loading, remove Tailwind. This phase creates the foundation all other phases depend on.

**DULEZITE:** Precist `design-system/setup.md` pred zacatkem — obsahuje kompletni bootstrap vzor.

App.tsx vzor:
```tsx
import { forwardRef } from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { createGlobalStyle } from 'styled-components';
import {
    UiDependencyProvider,
    cssColorsVariablesLight,
    cssColorsVariablesPaletteLight,
} from '@apify/ui-library';

const GlobalStyle = createGlobalStyle`
    :root {
        ${cssColorsVariablesLight}
        ${cssColorsVariablesPaletteLight}
        --shadow-active: 0 0 0 3px var(--color-primary-shadow-active);
        --shadow-1: 0 1px 2px rgba(0, 0, 0, 0.06);
        --shadow-2: 0 2px 4px rgba(0, 0, 0, 0.08);
        --shadow-3: 0 4px 8px rgba(0, 0, 0, 0.1);
        --shadow-4: 0 8px 16px rgba(0, 0, 0, 0.12);
        --shadow-5: 0 16px 32px rgba(0, 0, 0, 0.16);
    }
    html { font-size: 62.5%; }
    body {
        font-family: 'Inter', sans-serif;
        font-size: 1.4rem;
        line-height: 1.5;
        color: var(--color-neutral-text);
        background: var(--color-neutral-background);
        margin: 0;
    }
    *, *::before, *::after { box-sizing: border-box; }
    code, pre { font-family: 'IBM Plex Mono', Consolas, 'Liberation Mono', Menlo, monospace; }
`;

const InternalLink = forwardRef<HTMLAnchorElement, any>(({ href, ...props }, ref) => (
    <Link ref={ref} to={href} {...props} />
));
InternalLink.displayName = 'InternalLink';

const InternalImage = forwardRef<HTMLImageElement, any>((props, ref) => (
    <img ref={ref} {...props} />
));
InternalImage.displayName = 'InternalImage';

// Wrap the whole app:
<QueryClientProvider client={queryClient}>
    <BrowserRouter>
        <GlobalStyle />
        <UiDependencyProvider dependencies={{
            InternalLink,
            InternalImage,
            windowLocationHost: window.location.host,
            isHrefTrusted: () => true,
            tooltipSafeHtml: (content) => content,
            uiTheme: 'LIGHT',
        }}>
            <Routes>...</Routes>
        </UiDependencyProvider>
    </BrowserRouter>
</QueryClientProvider>
```

vite.config.ts — remove `tailwindcss` import and plugin, keep only `react()` and `server.proxy`.

index.html — add Google Fonts (Inter 400-700, IBM Plex Mono 400-600), change favicon to `apify-symbol.svg`, change title to "Skill Checker".

index.css — remove `@import "tailwindcss"` and Tailwind directives, keep just a comment `/* Styles handled by GlobalStyle in App.tsx */`.

apify-symbol.svg — copy from `design-system/assets/Apify Brand Assets/Symbol/apify-symbol-colors.svg`.

### Files to Create/Modify
- `web/src/App.tsx` — add GlobalStyle, UiDependencyProvider with dependencies object, InternalLink/InternalImage adapters
- `web/index.html` — font links (Inter, IBM Plex Mono), favicon → apify-symbol.svg, title → "Skill Checker"
- `web/src/index.css` — remove Tailwind import, minimal placeholder
- `web/vite.config.ts` — remove tailwindcss plugin import and usage
- `web/public/apify-symbol.svg` — copy Apify symbol SVG for favicon

### Acceptance Criteria
- [ ] App.tsx has GlobalStyle with cssColorsVariablesLight, cssColorsVariablesPaletteLight, and shadow vars --shadow-1 through --shadow-5
- [ ] App.tsx has `html { font-size: 62.5% }` in GlobalStyle
- [ ] App.tsx wraps routes in UiDependencyProvider with `dependencies` object prop (NOT individual props)
- [ ] InternalLink adapter accepts `href` prop and maps to React Router `to`
- [ ] InternalLink and InternalImage have displayName set
- [ ] vite.config.ts has no tailwindcss import or plugin
- [ ] index.html loads Inter (400,500,600,700) and IBM Plex Mono (400,500,600) from Google Fonts
- [ ] index.html favicon points to /apify-symbol.svg
- [ ] index.css contains no Tailwind imports or directives
- [ ] web/public/apify-symbol.svg exists and is a valid SVG
- [ ] `npm run build` passes in web/ directory
- [ ] `npm run lint` passes in web/ directory

### Tests Required
- `cd web && npm run build` — TypeScript compiles and Vite builds without errors
- `cd web && npm run lint` — ESLint passes
- Verify `grep -r "tailwindcss" web/src/ web/vite.config.ts` returns no matches
<!-- /PHASE:1 -->

<!-- PHASE:2 DEPENDS:1 -->
## Phase 2: Components

### Branch
`phase-2-components`

### Scope
Migrate all 6 shared components from Tailwind classes to @apify/ui-library components + styled-components. Each component file is self-contained.

**DULEZITE:** Precist `design-system/components.md`, `design-system/colors.md`, `design-system/icons.md` a `design-system/typography.md` pred zacatkem.

**Pravidla:**
- Zadne `className=` s Tailwind tridami
- Vsechny barvy pres `theme.color.*`, spacing pres `theme.space.*`
- Typografie pres `<Text>` a `<Heading>`
- `$` prefix pro transient styled-components props

**SeverityBadge.tsx** — nahradit span+Tailwind za `<Badge>` z ui-library:
```tsx
import { Badge } from '@apify/ui-library';
// CRITICAL → variant="danger", HIGH → variant="warning", MEDIUM → variant="neutral", LOW → variant="success"
```

**CategoryTag.tsx** — nahradit hand-made tooltip za `<Tag>` + `<Tooltip>` z ui-library:
```tsx
import { Tag, Tooltip } from '@apify/ui-library';
```

**RunProgress.tsx** — progress bar jako styled div s `theme.color.primary.action`, status chips jako `<Badge>` s variantou dle stavu. Elapsed timer zustat. Tabulka: styled `<table>` s `theme.color.*` a `theme.space.*`.

**YamlEditor.tsx** — wrapper card jako styled div s `theme.color.*`, Save button jako `<Button>` z ui-library, error message jako styled div s `theme.color.danger.*`. CodeMirror beze zmeny.

**MarkdownViewer.tsx** — nahradit ReactMarkdown za `<SimpleMarkdown>` z ui-library (vyzaduje UiDependencyProvider — uz je v App.tsx). Odebrat primo import `react-markdown`.

**Layout.tsx** — styled nav s `theme.color.*`, Apify symbol logo (import SVG z `../../public/apify-symbol.svg` nebo inline), `styled(NavLink)` s `&.active` pro aktivni stav. Main content wrapper s max-width `128rem` (= 1280px pri 10px base).

### Files to Create/Modify
- `web/src/components/SeverityBadge.tsx` — Badge from ui-library, severity→variant mapping
- `web/src/components/CategoryTag.tsx` — Tag + Tooltip from ui-library
- `web/src/components/RunProgress.tsx` — styled progress bar, Badge for status cells, styled table
- `web/src/components/YamlEditor.tsx` — styled card wrapper, Button for save, styled error message
- `web/src/components/MarkdownViewer.tsx` — SimpleMarkdown from ui-library replaces ReactMarkdown
- `web/src/components/Layout.tsx` — styled nav with Apify symbol, styled(NavLink), styled main container

### Acceptance Criteria
- [ ] SeverityBadge uses `<Badge>` from @apify/ui-library with correct variant mapping (CRITICAL→danger, HIGH→warning, MEDIUM→neutral, LOW→success)
- [ ] CategoryTag uses `<Tag>` and `<Tooltip>` from @apify/ui-library instead of hand-made hover tooltip
- [ ] RunProgress progress bar uses `theme.color.primary.action` for fill, `theme.color.neutral.backgroundMuted` for track
- [ ] RunProgress status cells use `<Badge>` with appropriate variants
- [ ] YamlEditor Save button is `<Button>` from @apify/ui-library
- [ ] YamlEditor error display uses `theme.color.danger.*` tokens
- [ ] MarkdownViewer uses `<SimpleMarkdown>` from @apify/ui-library (no direct react-markdown import)
- [ ] Layout nav uses styled-components with theme tokens (no Tailwind classes)
- [ ] Layout NavLink uses `styled(NavLink)` with `&.active` selector using `theme.color.primary.*`
- [ ] Layout main container has `max-width: 128rem` (1280px at 10px base)
- [ ] Zero `className=` attributes with Tailwind classes across all 6 files
- [ ] All colors from `theme.color.*`, all spacing from `theme.space.*`
- [ ] `npm run build` passes
- [ ] `npm run lint` passes

### Tests Required
- `cd web && npm run build` — TypeScript compiles and Vite builds without errors
- `cd web && npm run lint` — ESLint passes
- Verify `grep -rn 'className=' web/src/components/` returns no Tailwind utility classes
- Verify `grep -rn "from 'react-markdown'" web/src/components/` returns no matches
<!-- /PHASE:2 -->

<!-- PHASE:3 DEPENDS:2 -->
## Phase 3: Pages — Dashboard, Scenarios, ScenarioDetail

### Branch
`phase-3-pages-dashboard-scenarios`

### Scope
Migrate 3 pages from Tailwind to styled-components + @apify/ui-library. These pages use components from Phase 2 (SeverityBadge, CategoryTag, YamlEditor, MarkdownViewer).

**DULEZITE:** Precist `design-system/components.md` a `design-system/typography.md` pred zacatkem.

**Dashboard.tsx:**
- `<Heading type="titleL">Dashboard</Heading>` misto `<h1 className="text-2xl...">`
- StatCard: styled div s `theme.color.neutral.cardBackground`, `theme.shadow.shadow1`, `theme.radius.radius8`
- Stat value: `<Heading type="titleL">` s `color: ${theme.color.primary.text}`
- Stat label: `<Text type="body" size="small">` s `color: ${theme.color.neutral.textMuted}`
- Quick Run buttons: `<Button>` z ui-library (primary + secondary variant)
- Recent reports list: styled div s `theme.color.*`
- Category taxonomy: styled cards

**Scenarios.tsx:**
- `<Heading type="titleL">` pro title
- `<Text>` pro subtitle/count
- Edit YAML button: `<Button size="small" variant="secondary">`
- Scenario list: styled cards s `theme.color.*`

**ScenarioDetail.tsx:**
- Back link: `<ArrowLeftIcon>` + styled Link
- `<Heading type="titleM">` pro title
- Detail card: styled div s theme tokens
- Run button: `<Button LeftIcon={PlayIcon}>`

### Files to Create/Modify
- `web/src/pages/Dashboard.tsx` — Heading, styled stat cards, Button, styled lists
- `web/src/pages/Scenarios.tsx` — Heading, Text, Button, styled scenario list
- `web/src/pages/ScenarioDetail.tsx` — ArrowLeftIcon back link, Heading, styled card, Button with PlayIcon

### Acceptance Criteria
- [ ] Dashboard uses `<Heading type="titleL">` for page title
- [ ] Dashboard stat cards use `theme.color.neutral.cardBackground`, `theme.shadow.shadow1`, `theme.radius.radius8`
- [ ] Dashboard Quick Run uses `<Button>` from ui-library (not `<a>` or `<Link>` with Tailwind)
- [ ] Scenarios uses `<Heading type="titleL">` and `<Text>` for subtitle
- [ ] Scenarios Edit YAML button is `<Button size="small" variant="secondary">`
- [ ] ScenarioDetail back navigation uses ArrowLeftIcon from @apify/ui-icons
- [ ] ScenarioDetail Run button uses `<Button LeftIcon={PlayIcon}>` from ui-library
- [ ] Zero `className=` attributes with Tailwind classes across all 3 files
- [ ] All colors from `theme.color.*`, spacing from `theme.space.*`
- [ ] `npm run build` passes
- [ ] `npm run lint` passes

### Tests Required
- `cd web && npm run build` — TypeScript compiles and Vite builds without errors
- `cd web && npm run lint` — ESLint passes
- Verify `grep -rn 'className=' web/src/pages/Dashboard.tsx web/src/pages/Scenarios.tsx web/src/pages/ScenarioDetail.tsx` returns no Tailwind classes
<!-- /PHASE:3 -->

<!-- PHASE:4 DEPENDS:2 -->
## Phase 4: Pages — Reports, ReportDetail, Run

### Branch
`phase-4-pages-reports-run`

### Scope
Migrate 3 pages from Tailwind to styled-components + @apify/ui-library. Run.tsx is the most complex page (~283 lines).

**DULEZITE:** Precist `design-system/components.md` a `design-system/typography.md` pred zacatkem.

**Reports.tsx:**
- `<Heading type="titleL">` pro title
- Empty state: styled div s `theme.color.neutral.textMuted` a info text
- Report list: styled div s `theme.color.*`
- Delete button: styled `<button>` s `theme.color.danger.text` (ui-library nema inline delete s potvrzenim)

**ReportDetail.tsx:**
- Back link: `<ArrowLeftIcon>` + styled Link
- `<Heading type="titleM">` pro title
- Loading: `<Text>` s `theme.color.neutral.textMuted`
- Error: styled div s `theme.color.danger.text`
- Content card: styled div s theme tokens

**Run.tsx (nejslozitejsi):**
- `<Heading type="titleL">` pro title
- 3-column grid: styled divs
- Checkboxy: native `<input type="checkbox">` se styled wrapperem (ui-library nema checkbox)
- Range slider: native `<input type="range">` se styled wrapperem
- Skill filter: native `<select>` se styled wrapperem (ui-library Select je prilis tezkopadny)
- Start button: `<Button size="large" LeftIcon={PlayIcon}>` z ui-library
- Completed banner: styled div s `theme.color.success.*`
- Cards: styled divs s `theme.color.neutral.cardBackground`, `theme.shadow.shadow1`

### Files to Create/Modify
- `web/src/pages/Reports.tsx` — Heading, styled list, styled delete button, styled empty state
- `web/src/pages/ReportDetail.tsx` — ArrowLeftIcon back link, Heading, styled card
- `web/src/pages/Run.tsx` — Heading, Button, styled form controls, styled cards, styled success banner

### Acceptance Criteria
- [ ] Reports uses `<Heading type="titleL">` for page title
- [ ] Reports empty state uses theme color tokens for muted text
- [ ] Reports delete button uses `theme.color.danger.text` for color
- [ ] ReportDetail back navigation uses ArrowLeftIcon from @apify/ui-icons
- [ ] ReportDetail uses `<Heading type="titleM">` for filename
- [ ] Run uses `<Heading type="titleL">` for page title
- [ ] Run Start button is `<Button>` from ui-library with PlayIcon
- [ ] Run cards use `theme.color.neutral.cardBackground` and `theme.shadow.shadow1`
- [ ] Run completed banner uses `theme.color.success.*` tokens
- [ ] Native form controls (checkbox, range, select) have styled wrappers with theme tokens
- [ ] Zero `className=` attributes with Tailwind classes across all 3 files
- [ ] All colors from `theme.color.*`, spacing from `theme.space.*`
- [ ] `npm run build` passes
- [ ] `npm run lint` passes

### Tests Required
- `cd web && npm run build` — TypeScript compiles and Vite builds without errors
- `cd web && npm run lint` — ESLint passes
- Verify `grep -rn 'className=' web/src/pages/Reports.tsx web/src/pages/ReportDetail.tsx web/src/pages/Run.tsx` returns no Tailwind classes
<!-- /PHASE:4 -->

<!-- PHASE:5 DEPENDS:3,4 -->
## Phase 5: Cleanup

### Branch
`phase-5-cleanup`

### Scope
Remove unused Tailwind dependencies from package.json, delete vite.svg, and verify zero Tailwind remnants across the entire web/ directory.

**Zmeny v package.json:**
- Odebrat z dependencies: `tailwindcss`, `@tailwindcss/vite`, `react-markdown`
- Ponechat: `@apify/ui-library`, `@apify/ui-icons`, `styled-components` (pouzivane)
- Ponechat: `react-markdown` je dependency ui-library — nepotrebujeme primo, ale nerozbije to build kdyz ho odebereme

**Smazat:**
- `web/public/vite.svg` (stary favicon)

**Verifikace:**
- Zero `className=` s Tailwind utility tridami v celom `web/src/`
- Zero hardcoded hex barev (pattern `#[0-9a-fA-F]{3,8}`) v `.tsx` souborech
- `npm install` + `npm run build` + `npm run lint` projde

### Files to Create/Modify
- `web/package.json` — remove tailwindcss, @tailwindcss/vite, react-markdown from dependencies

### Acceptance Criteria
- [ ] package.json does not contain tailwindcss, @tailwindcss/vite, or react-markdown in dependencies
- [ ] package.json still contains @apify/ui-library, @apify/ui-icons, styled-components
- [ ] web/public/vite.svg is deleted
- [ ] Zero matches for Tailwind utility classes in `grep -rn 'className=' web/src/` (no bg-*, text-*, px-*, etc.)
- [ ] Zero hardcoded hex colors in .tsx files: `grep -rn '#[0-9a-fA-F]\{3,8\}' web/src/**/*.tsx` returns 0
- [ ] `npm install` succeeds in web/ directory
- [ ] `npm run build` passes
- [ ] `npm run lint` passes

### Tests Required
- `cd web && npm install && npm run build` — clean install and build passes
- `cd web && npm run lint` — ESLint passes
- `grep -rn 'className=' web/src/ | grep -E '(bg-|text-|px-|py-|mx-|my-|flex|grid|rounded|shadow|border|gap-|space-|font-|leading-|tracking-|w-|h-|min-|max-|overflow|truncate|line-clamp|animate|transition|hover:|focus:)'` — returns 0 matches
- `grep -rn '#[0-9a-fA-F]\{3,8\}' web/src/ --include='*.tsx'` — returns 0 matches
<!-- /PHASE:5 -->