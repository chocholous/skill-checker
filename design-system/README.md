# Apify Design System Reference

Reference pro `@apify/ui-library@1.124.1` + Apify brand guidelines.
Extrahovanou z TypeScript deklaraci, runtime hodnot balicku, brand manualu a [apify.com/resources/brand](https://apify.com/resources/brand).

## Soubory

| Soubor | Obsah |
|--------|-------|
| [brand.md](brand.md) | Brand guidelines, logo pravidla, overeni shody s ui-library |
| [setup.md](setup.md) | ThemeProvider, imports, styled-components pattern |
| [components.md](components.md) | Kompletni katalog komponent s props |
| [colors.md](colors.md) | Semanticke barvy, palety (light/dark), brand barvy |
| [tokens.md](tokens.md) | Spacing, radius, shadows, transitions, breakpoints |
| [typography.md](typography.md) | Text/Heading komponenty, font system |
| [icons.md](icons.md) | 168 ikon z @apify/ui-icons, velikosti, pouziti |
| [agent-instructions.md](agent-instructions.md) | Oficialni Apify design system pravidla pro agenty |

## Assets

```
assets/Apify Brand Assets/
  Apify logo manual.pdf       — brand manual v0.2
  Logo/                        — wordmark varianty (SVG, PNG)
  Symbol/                      — symbol varianty (SVG, PNG)
  Badges/                      — partner badges
  Banners/                     — affiliate banery (IAB rozmery)
  Grid/                        — grid base + pattern (SVG)
```

## Brand barvy (primarni)

| Nazev | Hex | ui-library token |
|-------|-----|------------------|
| Chateau Green | #20A34E | `theme.colorPalette.light.logoGreen` |
| Blue Ribbon | #246DFF | `theme.colorPalette.light.logoBlue` |
| Blaze Orange | #F86606 | `theme.colorPalette.light.logoOrange` |

## Quick Reference

```typescript
import { Button, Badge, Text, Heading, theme } from '@apify/ui-library';
import styled from 'styled-components';

// Barvy — vzdy pres theme.color
theme.color.neutral.text
theme.color.primary.action
theme.color.success.background

// Spacing
theme.space.space8   // 0.8rem
theme.space.space16  // 1.6rem

// Radius
theme.radius.radius8 // 8px

// Typografie — vzdy pres komponenty
<Text type="body" size="regular">...</Text>
<Heading type="titleL">...</Heading>
```

## Zdroje

- Brand: [apify.com/resources/brand](https://apify.com/resources/brand) + `assets/Apify Brand Assets/Apify logo manual.pdf`
- Balicek: `@apify/ui-library` na npm (Apache-2.0)
- Peer deps: `react@19.x`, `react-dom@19.x`, `styled-components@^6.1.19`
- Ikony: `@apify/ui-icons`
- Design system instrukce: [apify/apify-mcp-server](https://github.com/apify/apify-mcp-server/blob/master/DESIGN_SYSTEM_AGENT_INSTRUCTIONS.md)
- Storybook: privatni (v internim balicku `components-storybook`)
- Kontakt: design@apify.com
