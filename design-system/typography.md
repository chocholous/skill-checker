# Typografie

Typografie se pouziva **vyhradne pres komponenty** `<Text>` a `<Heading>`, nikdy ne primo pres CSS font properties.

## Font families

| Pouziti | Font |
|---------|------|
| UI / aplikace | Inter, sans-serif |
| Code | IBM Plex Mono, monospace |
| Marketing | GT-Walsheim-Regular (nebudeme pouzivat) |

---

## Heading

```tsx
import { Heading } from '@apify/ui-library';

<Heading type="titleL" as="h2">Title</Heading>
```

| Type | Mobile | Desktop | Weight |
|------|--------|---------|--------|
| `title3xl` | 2.8rem | 3.6rem | 700 |
| `title2xl` | 2.4rem | 2.8rem | 700 |
| `titleXl` | 2rem | 2.4rem | 650-700 |
| `titleL` | 1.8rem | 2rem | 650 |
| `titleM` | 1.6rem | 1.6rem | 650 |
| `titleS` | 1.4rem | 1.4rem | 650 |
| `titleXs` | 1.2rem | 1.2rem | 650 |

Props: `type`, `italic`, `uppercase`, `align` ('left'|'right'|'center'), `color`, `as`

---

## Text

```tsx
import { Text } from '@apify/ui-library';

<Text type="body" size="regular" weight="normal">Content</Text>
<Text type="code" size="small">monospace</Text>
```

### Body type

| Size | Font size | Pouziti |
|------|-----------|---------|
| `big` | 1.6rem | Vetsi odstavce |
| `regular` | 1.4rem | Bezny text |
| `small` | 1.2rem | Drobny text, labely |

### Code type

| Size | Font size | Font |
|------|-----------|------|
| `big` | 1.6rem | IBM Plex Mono |
| `regular` | 1.4rem | IBM Plex Mono |
| `small` | 1.2rem | IBM Plex Mono |

### Weight varianty

| Weight | CSS value | Pouziti |
|--------|-----------|---------|
| `normal` | 400 | Bezny text |
| `medium` | 500 | Zvyrazneny text |
| `bold` | 600 | Tucny text |

Props: `type`, `size`, `weight`, `italic`, `uppercase`, `align`, `color`, `as`

---

## Content typografie (TextContent)

Pro delsi clanky / dokumentaci:

```tsx
import { TextContent } from '@apify/ui-library';

<TextContent type="paragraph">Long form content...</TextContent>
<TextContent type="snippet" weight="bold">Code snippet</TextContent>
```

| Type | Font size | Font |
|------|-----------|------|
| `paragraph` | 1.6rem | Inter |
| `snippet` | 1.4rem | IBM Plex Mono |

---

## Line height vzory

| Velikost textu | Line height ratio |
|---------------|-------------------|
| 2.8rem+ | 1.15-1.2x |
| 1.6-2rem | 1.2-1.4x |
| 1.2-1.4rem | 1.3x |

---

## Priklady pouziti

```tsx
// Nadpis stranky
<Heading type="titleL" as="h1">Dashboard</Heading>

// Sekce
<Heading type="titleM" as="h2">Scenarios</Heading>

// Podsekce
<Heading type="titleS" as="h3">Results</Heading>

// Bezny text
<Text type="body" size="regular">Description here</Text>

// Muted text
<Text type="body" size="small" color={theme.color.neutral.textMuted}>
    Secondary info
</Text>

// Code
<Text type="code" size="regular">function_name()</Text>

// Bold
<Text type="body" size="regular" weight="bold">Important</Text>
```
