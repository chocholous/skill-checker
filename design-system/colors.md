# Barvy

Vsechny barvy pres `theme.color.{kategorie}.{vlastnost}`. Hodnoty jsou CSS promenne (`var(--...)`).

## Brand barvy (primarni — logo)

| Nazev | Hex | CMYK | Token |
|-------|-----|------|-------|
| **Chateau Green** | #20A34E | c81 m9 y97 k0 | `colorPalette.light.logoGreen` |
| **Blue Ribbon** | #246DFF | c83 m50 y3 k0 | `colorPalette.light.logoBlue` |
| **Blaze Orange** | #F86606 | c0 m74 y100 k0 | `colorPalette.light.logoOrange` |

## Brand barvy (doplnkove palety)

| Nazev | Deep | Accent | Tokeny |
|-------|------|--------|--------|
| Magenta | #694D6B | #FF64B8 | `magentaDeep`, `magentaAccent` |
| Mondo | #FF4800 | #4E4236 | `mondoDeep`, `mondoAccent` |
| Lime | #756506 | #FFFF5A | `limeDeep`, `limeAccent` |
| Meteorite | #321868 | #38FB9D | `meteoriteDeep`, `meteoriteAccent` |

Kazda ma dalsi odstiny: `Main`, `Medium`, `Muted`, `Subtle`, `Tint`.

---

## Semanticke barvy

### Neutral

| Vlastnost | Pouziti |
|-----------|---------|
| `text` | Primarni text |
| `textMuted` | Sekundarni text |
| `textSubtle` | Tercialni text |
| `textDisabled` | Disabled text |
| `textOnPrimary` | Text na primary pozadi |
| `textPlaceholder` | Input placeholder |
| `icon` | Primarni ikony |
| `iconSubtle` | Sekundarni ikony |
| `iconDisabled` | Disabled ikony |
| `iconOnPrimary` | Ikony na primary pozadi |
| `background` | Hlavni pozadi |
| `backgroundMuted` | Tlumene pozadi |
| `backgroundSubtle` | Jemne pozadi |
| `backgroundWhite` | Bile pozadi |
| `cardBackground` | Pozadi karet |
| `cardBackgroundHover` | Hover karet |
| `border` | Hlavni bordery |
| `separatorSubtle` | Jemne oddelovace |
| `fieldBorder` | Input bordery |
| `fieldBackground` | Input pozadi |
| `hover` | Hover stav |
| `disabled` | Disabled stav |
| `overlay` | Overlay pozadi |
| `actionSecondary` | Sekundarni akce |
| `actionSecondaryHover` | Sekundarni akce hover |
| `actionSecondaryActive` | Sekundarni akce active |
| `chipBackground` | Chip pozadi |
| `chipBackgroundHover` | Chip hover |
| `chipBackgroundActive` | Chip active |
| `chipBackgroundDisabled` | Chip disabled |
| `smallTooltipText` | Maly tooltip text |
| `smallTooltipBackground` | Maly tooltip pozadi |
| `smallTooltipBorder` | Maly tooltip border |
| `largeTooltipBackground` | Velky tooltip pozadi |
| `largeTooltipBorder` | Velky tooltip border |

### Primary

| Vlastnost | Pouziti |
|-----------|---------|
| `text` | Primary text |
| `textInteractive` | Interaktivni primary text |
| `icon` | Primary ikony |
| `action` | Primary tlacitka |
| `actionHover` | Primary hover |
| `actionActive` | Primary active |
| `fieldBorderActive` | Aktivni input border |
| `borderSubtle` | Jemny primary border |
| `background` | Primary pozadi |
| `backgroundSubtle` | Jemne primary pozadi |
| `backgroundHover` | Primary pozadi hover |
| `chipBackground` | Primary chip |
| `chipBackgroundSubtle` | Jemny primary chip |
| `chipBackgroundHover` | Primary chip hover |
| `chipText` | Primary chip text |
| `shadowActive` | Active shadow |

### Primary Black

| Vlastnost | Pouziti |
|-----------|---------|
| `action` | Cerne tlacitko |
| `actionHover` | Hover |
| `actionActive` | Active |
| `background` | Pozadi |
| `backgroundHover` | Pozadi hover |
| `chipText` | Chip text |

### Success / Warning / Danger

Vsechny tri maji stejnou strukturu:

| Vlastnost | Pouziti |
|-----------|---------|
| `text` | Status text |
| `icon` | Status ikona |
| `action` | Status tlacitko |
| `actionHover` | Hover |
| `actionActive` | Active |
| `background` | Plne pozadi |
| `backgroundHover` | Pozadi hover |
| `backgroundSubtle` | Jemne pozadi |
| `backgroundSubtleHover` | Jemne pozadi hover |
| `backgroundSubtleActive` | Jemne pozadi active |
| `chipBackground` | Chip pozadi |
| `chipBackgroundHover` | Chip hover |
| `chipText` | Chip text |
| `border` | Border |
| `borderSubtle` | Jemny border |
| `fieldBorder` | Input border |

### Special

| Vlastnost | Pouziti |
|-----------|---------|
| `freePlanBackground` | Free plan |
| `starterPlanBackground` | Starter plan |
| `scalePlanBackground` | Scale plan |
| `businessPlanBackground` | Business plan |
| `enterprisePlanBackground` | Enterprise plan |

### Accent barvy

9 akcentnich rodin: `rose`, `buttercup`, `paprika`, `teal`, `indigo`, `slate`, `coral`, `lavender`, `bamboo`

Kazda ma: `light`, `base`, `dark`, `text`

```tsx
theme.color.rose.base
theme.color.teal.light
theme.color.coral.text
```

---

## Paleta (hex hodnoty)

Pristup pres `theme.colorPalette.light.*` / `theme.colorPalette.dark.*`

### Neutral skala

| Token | Hex |
|-------|-----|
| `neutral0` | #ffffff |
| `neutral25` - `neutral950` | 23 odstinu sedi |

### Semantic skaly (light theme)

**Yellow**: `yellow25` (#f9f6ea) - `yellow700` (#864906)
**Red**: `red25` (#fcf2ef) - `red700` (#af0600)
**Green**: `green25` (#e8f9ef) - `green700` (#176b08)
**Blue**: `blue25` (#f0f8ff) - `blue700` (#224ed5)

### Brand barvy

| Token | Hex | Pouziti |
|-------|-----|---------|
| `logoOrange` | #f86606 | Apify logo |
| `logoGreen` | #20a34e | Apify logo |
| `logoBlue` | #246dff | Apify logo |
| `mondoDeep` | #ff4800 | Mondo primary |
| `mondoMain` | #b94013 | Mondo secondary |
| `magentaDeep` | #694d6b | Magenta primary |
| `magentaAccent` | #ff64b8 | Magenta accent |
| `meteoriteMain` | #6759e6 | Meteorite |

### Accent barvy (light theme)

| Rodina | Light | Base | Dark | Text |
|--------|-------|------|------|------|
| Rose | #f483b5 | #c6387d | #781552 | #b6006b |
| Buttercup | #ffdd96 | #f0b21b | #c37319 | #a65d00 |
| Paprika | #e44467 | #9b0238 | #4a0018 | #ba0044 |
| Teal | #a7f2ed | #30c0bb | #297774 | #018181 |
| Indigo | #a1b7ff | #5d85e1 | #365494 | #2563c1 |
| Slate | #c1c5e1 | #8490c4 | #525c85 | #566087 |
| Coral | #ffc89f | #fa8136 | #bb4511 | #c74000 |
| Lavender | #bf97ed | #6a14de | #330276 | #6e00f4 |
| Bamboo | #64cda5 | #12966f | #195d46 | #007455 |

### Pouziti palety vs semantickych barev

```tsx
// PREFEROVANE — semanticke barvy (reaguje na theme)
color: ${theme.color.neutral.text};
background: ${theme.color.success.backgroundSubtle};

// PALETA — jen kdyz semanticka barva neexistuje
color: ${theme.colorPalette.light.blue500};
```

## Stavove barvy — vzor

```tsx
// Default → Hover → Active
background: ${theme.color.primary.action};
&:hover { background: ${theme.color.primary.actionHover}; }
&:active { background: ${theme.color.primary.actionActive}; }
```
