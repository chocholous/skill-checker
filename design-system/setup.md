# Setup

Kompletni navod od nuly k funkcni appce s `@apify/ui-library`.

## 1. Instalace

```bash
npm install @apify/ui-library styled-components @apify/ui-icons
```

Peer deps: `react@17-19`, `react-dom@17-19`, `styled-components@^6.1.19`

---

## 2. CSS promenne (KRITICKE)

Barvy v `theme.color.*` jsou CSS variable reference (`var(--color-neutral-text)` atd.).
Knihovna je **neinjektuje automaticky** — musis je aplikovat sam.

### Dostupne exporty

```typescript
import {
    cssColorsVariablesLight,         // 142 semantic CSS vars (light theme)
    cssColorsVariablesDark,          // 142 semantic CSS vars (dark theme)
    cssColorsVariablesPaletteLight,  // paleta (neutral, yellow, red, green, blue skaly)
    cssColorsVariablesPaletteDark,   // paleta (dark varianty)
} from '@apify/ui-library';
```

### Injekce pres createGlobalStyle (doporuceno)

```typescript
import { createGlobalStyle } from 'styled-components';
import {
    cssColorsVariablesLight,
    cssColorsVariablesDark,
    cssColorsVariablesPaletteLight,
    cssColorsVariablesPaletteDark,
} from '@apify/ui-library';

// Light theme
const GlobalStyle = createGlobalStyle`
    :root {
        ${cssColorsVariablesLight}
        ${cssColorsVariablesPaletteLight}
    }
`;

// Nebo s dark mode podporou:
const GlobalStyleWithDarkMode = createGlobalStyle<{ $isDark?: boolean }>`
    :root {
        ${({ $isDark }) => $isDark
            ? `${cssColorsVariablesDark} ${cssColorsVariablesPaletteDark}`
            : `${cssColorsVariablesLight} ${cssColorsVariablesPaletteLight}`
        }
    }
`;
```

### Shadow promenne

Shadows (`theme.shadow.*`) pouzivaji `var(--shadow-N)`. Tyto nejsou v exportech — definuj je rucne:

```css
:root {
    --shadow-active: 0 0 0 3px var(--color-primary-shadow-active);
    --shadow-1: 0 1px 2px rgba(0, 0, 0, 0.06);
    --shadow-2: 0 2px 4px rgba(0, 0, 0, 0.08);
    --shadow-3: 0 4px 8px rgba(0, 0, 0, 0.1);
    --shadow-4: 0 8px 16px rgba(0, 0, 0, 0.12);
    --shadow-5: 0 16px 32px rgba(0, 0, 0, 0.16);
}
```

---

## 3. Fonty

Knihovna predpoklada ze fonty jsou dostupne. Nacti je v HTML nebo pres CSS.

### Inter (UI text) — Google Fonts

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;650;700&display=swap" rel="stylesheet">
```

### IBM Plex Mono (code) — Google Fonts

```html
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
```

### GT Walsheim (marketing) — neni na Google Fonts

Komercni font, pouzivany v marketing typografii. Pro nas projekt **nepotrebujeme** — pouzivame `shared` typografii (Inter).

---

## 4. UiDependencyProvider

Obaluje app a poskytuje sdilene zavislosti vsem komponentam.

```tsx
import { forwardRef } from 'react';
import { Link } from 'react-router-dom';
import { UiDependencyProvider } from '@apify/ui-library';

// Adapter pro React Router Link → ui-library InternalLink
const InternalLink = forwardRef<HTMLAnchorElement, any>(({ to, ...props }, ref) => (
    <Link ref={ref} to={to} {...props} />
));
InternalLink.displayName = 'InternalLink';

const InternalImage = forwardRef<HTMLImageElement, any>((props, ref) => (
    <img ref={ref} {...props} />
));
InternalImage.displayName = 'InternalImage';

const uiDependencies = {
    InternalLink,
    InternalImage,
    windowLocationHost: window.location.host,
    isHrefTrusted: () => true,
    tooltipSafeHtml: (content) => content,
    uiTheme: 'LIGHT' as const,        // 'LIGHT' | 'DARK'
    // trackClick: (id, data) => {},   // optional analytics
};
```

### UiDependencies interface

| Vlastnost | Typ | Povinne | Popis |
|-----------|-----|---------|-------|
| `InternalLink` | `ForwardRefComponent` | ano | Router link adapter |
| `InternalImage` | `ForwardRefComponent` | ano | Image adapter |
| `windowLocationHost` | `string` | ano | Pro detekci externich linku |
| `isHrefTrusted` | `(href) => boolean` | ano | Validace URL bezpecnosti |
| `tooltipSafeHtml` | `(content) => ReactNode` | ano | Sanitizace HTML v tooltipech |
| `uiTheme` | `'LIGHT' \| 'DARK'` | ne | Prepinani theme |
| `trackClick` | `(id, data?) => void` | ne | Analytics tracking |
| `generateProxyImageUrl` | `(url, opts) => string` | ne | Image proxy/resize |

---

## 5. Kompletni app bootstrap

```tsx
// main.tsx
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './App';

createRoot(document.getElementById('root')!).render(
    <StrictMode>
        <App />
    </StrictMode>
);
```

```tsx
// App.tsx
import { forwardRef } from 'react';
import { BrowserRouter, Link } from 'react-router-dom';
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

    html {
        font-size: 62.5%;  /* 1rem = 10px (ui-library pouziva rem s base 10px) */
    }

    body {
        font-family: 'Inter', sans-serif;
        font-size: 1.4rem;
        line-height: 1.5;
        color: var(--color-neutral-text);
        background: var(--color-neutral-background);
        margin: 0;
    }

    *, *::before, *::after {
        box-sizing: border-box;
    }

    code, pre {
        font-family: 'IBM Plex Mono', Consolas, 'Liberation Mono', Menlo, monospace;
    }
`;

const InternalLink = forwardRef<HTMLAnchorElement, any>(({ to, ...props }, ref) => (
    <Link ref={ref} to={to} {...props} />
));
InternalLink.displayName = 'InternalLink';

const InternalImage = forwardRef<HTMLImageElement, any>((props, ref) => (
    <img ref={ref} {...props} />
));
InternalImage.displayName = 'InternalImage';

export function App() {
    return (
        <BrowserRouter>
            <GlobalStyle />
            <UiDependencyProvider
                InternalLink={InternalLink}
                InternalImage={InternalImage}
                windowLocationHost={window.location.host}
                isHrefTrusted={() => true}
                tooltipSafeHtml={(content) => content}
                uiTheme="LIGHT"
            >
                {/* <Routes>...</Routes> */}
            </UiDependencyProvider>
        </BrowserRouter>
    );
}
```

### DULEZITE: font-size 62.5%

Ui-library pouziva rem s predpokladem **1rem = 10px** (napr. `space8 = 0.8rem = 8px`).
Proto `html { font-size: 62.5%; }` (62.5% z 16px = 10px).

---

## 6. Styled Components Pattern

```typescript
import styled, { css } from 'styled-components';
import { theme } from '@apify/ui-library';

// Transient props s $ prefixem (neprojdou do DOM)
const StyledCard = styled.div<{ $isActive?: boolean }>`
    color: ${theme.color.neutral.text};
    padding: ${theme.space.space16};
    border-radius: ${theme.radius.radius8};
    border: 1px solid ${theme.color.neutral.border};
    transition: box-shadow ${theme.transition.fastEaseInOut};

    &:hover {
        box-shadow: ${theme.shadow.shadow2};
    }

    ${({ $isActive }) => $isActive && css`
        border-color: ${theme.color.primary.action};
        background: ${theme.color.primary.backgroundSubtle};
    `}
`;
```

---

## 7. Poradi v souboru (konvence)

```typescript
// 1. React imports
import { forwardRef, useState } from 'react';

// 2. styled-components
import styled from 'styled-components';

// 3. @apify/ui-library + @apify/ui-icons
import { Button, Text, theme } from '@apify/ui-library';
import { PlayIcon } from '@apify/ui-icons';

// 4. Konstanty & typy
export const VARIANTS = { ... } as const;
type Props = { ... };

// 5. Styled components
const StyledWrapper = styled.div`...`;

// 6. Komponenta + displayName
export const MyComponent = forwardRef<HTMLElement, Props>((props, ref) => {
    // implementace
});
MyComponent.displayName = 'MyComponent';
```

---

## 8. Pravidla (zero tolerance)

- **NIKDY** hardcoded hex barvy — vzdy `theme.color.*`
- **NIKDY** hardcoded px/rem hodnoty — vzdy `theme.space.*` nebo `theme.radius.*`
- **NIKDY** font properties primo — vzdy `<Text>` nebo `<Heading>` komponenty
- **NIKDY** duplikovat UI library komponenty
- **VZDY** `$` prefix pro transient styled-components props

---

## Checklist pred spustenim

- [ ] `styled-components` nainstalovane
- [ ] CSS promenne injektovane (`createGlobalStyle` s `cssColorsVariablesLight` + palette)
- [ ] Shadow promenne definovane (--shadow-1 az --shadow-5)
- [ ] `html { font-size: 62.5% }` nastaveno
- [ ] Inter + IBM Plex Mono fonty nactene
- [ ] `UiDependencyProvider` obali celou app
- [ ] `InternalLink` adapter napojeny na React Router
- [ ] `InternalImage` adapter definovany
