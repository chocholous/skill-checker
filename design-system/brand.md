# Apify Brand

Zdroje: [apify.com/resources/brand](https://apify.com/resources/brand), `assets/Apify Brand Assets/Apify logo manual.pdf` (v0.2, June 2025)

---

## Logo

Tri casti: **Symbol** (barevne trojuhelniky) + **Wordmark** ("apify", font Styrene) + clear space.

### Varianty

| Varianta | Pouziti | Soubory |
|----------|---------|---------|
| Colors (symbol) + dark wordmark | Svetle pozadi | `Logo/Logo colors/apify-logo-wordmark-dark.*` |
| Colors (symbol) + white wordmark | Tmave pozadi | `Logo/Logo colors/apify-logo-wordmark-white.*` |
| Dark (cerne) | Monochromaticke svetle | `Logo/Logo dark/apify-logo-dark.*` |
| White (bile) | Monochromaticke tmave | `Logo/Logo white/apify-logo-white.*` |

### Symbol samostatne

| Varianta | Soubory |
|----------|---------|
| Colors | `Symbol/apify-symbol-colors.*` |
| Dark | `Symbol/apify-symbol-dark.*` |
| White | `Symbol/apify-symbol-white.*` |

Vsechny v PNG + SVG, s i bez marginu.

### Pravidla

- Vzdy poskytnout dostatek prostoru kolem loga (min = vyska pismene "a")
- **ZAKAZANO**: stiny, blury, gradienty, zmena barev, tahy, deformace
- Pouze schvalene varianty z manualu

---

## Primarni barvy (symbol)

| Nazev | Hex | CMYK | Token v ui-library |
|-------|-----|------|--------------------|
| **Chateau Green** | #20A34E | c81 m9 y97 k0 | `theme.colorPalette.light.logoGreen` |
| **Blue Ribbon** | #246DFF | c83 m50 y3 k0 | `theme.colorPalette.light.logoBlue` |
| **Blaze Orange** | #F86606 | c0 m74 y100 k0 | `theme.colorPalette.light.logoOrange` |

Kazda ma 10-shade paletu (50-950).

---

## Doplnkove palety

| Nazev | Base | Accent | Token (deep) | Token (accent) |
|-------|------|--------|--------------|----------------|
| Magenta | #694D6B | #FF64B8 | `magentaDeep` | `magentaAccent` |
| Mondo | #FF4800 | #4E4236 | `mondoDeep` | `mondoAccent` |
| Lime | #756506 | #FFFF5A | `limeDeep` | `limeAccent` |
| Meteorite | #321868 | #38FB9D | `meteoriteDeep` | `meteoriteAccent` |

---

## Typografie

| Rodina | Pouziti | Vahy | Token v ui-library |
|--------|---------|------|--------------------|
| **GT Walsheim** | Nadpisy, marketing | Regular, Bold | `theme.typography.marketing` |
| **Inter** | Body, UI, navigace, buttony | Regular (400), Medium (500), Bold (600-700) | `theme.typography.shared` |
| **IBM Plex Mono** | Code, snippety | Regular, Bold | `theme.typography.shared` (code type) |

### Zasady

- **Clarity**: Inter pro husty obsah, GT Walsheim pro klicove zpravy
- **Consistency**: Pouze tyto tri rodiny, zadne jine
- **Contrast**: Dostatecny kontrast text vs pozadi
- **Accessibility**: Primerene velikosti, line-height, letter-spacing

---

## Assets

```
design-system/assets/Apify Brand Assets/
  Apify logo manual.pdf       — kompletni brand manual (v0.2)
  Logo/
    Logo colors/               — wordmark dark + white (PNG, SVG, margins)
    Logo dark/                 — monochromaticky dark (PNG, SVG, margins)
    Logo white/                — monochromaticky white (PNG, SVG, margins)
  Symbol/
    apify-symbol-{colors,dark,white}.*  — symbol (PNG, SVG, margins)
  Badges/
    apify-{affiliate,certified}-partner-{dark,light}.png
  Banners/
    Affiliate banery v IAB rozmerech (300x50, 300x250, 336x280, 728x90)
  Grid/
    apify-grid-base.svg        — zakladni grid element
    apify-grid-pattern.svg     — opakovatelny pattern
```

---

## Overeni shody: brand vs ui-library

| Vlastnost | Brand manual | ui-library theme | Shoda |
|-----------|-------------|------------------|-------|
| Logo Green | #20A34E | `logoGreen: #20a34e` | OK |
| Logo Blue | #246DFF | `logoBlue: #246dff` | OK |
| Logo Orange | #F86606 | `logoOrange: #f86606` | OK |
| Magenta Deep | #694D6B | `magentaDeep: #694d6b` | OK |
| Magenta Accent | #FF64B8 | `magentaAccent: #ff64b8` | OK |
| Mondo Deep | #FF4800 | `mondoDeep: #ff4800` | OK |
| Mondo Accent | #4E4236 | `mondoAccent: #4e4236` | OK |
| Lime Deep | #756506 | `limeDeep: #756506` | OK |
| Lime Accent | #FFFF5A | `limeAccent: #ffff5a` | OK |
| Meteorite Deep | #321868 | `meteoriteDeep: #321868` | OK |
| Meteorite Accent | #38FB9D | `meteoriteAccent: #38fb9d` | OK |
| Font: GT Walsheim | Display/headlines | `typography.marketing` | OK |
| Font: Inter | Body/UI | `typography.shared` | OK |
| Font: IBM Plex Mono | Code | `typography.shared` (code) | OK |

Vsechny hodnoty jsou 1:1 aligned.

---

## Kontakt

Design dotazy: design@apify.com
