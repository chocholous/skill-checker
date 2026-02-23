# Design System Agent Instructions

Zdroj: [apify/apify-mcp-server/DESIGN_SYSTEM_AGENT_INSTRUCTIONS.md](https://github.com/apify/apify-mcp-server/blob/master/DESIGN_SYSTEM_AGENT_INSTRUCTIONS.md)

---

## Pravidla (zero tolerance)

### 1. Design tokeny ONLY

```typescript
// ZAKAZANO
color: '#1976d2'
padding: '8px'
border-radius: '4px'
font-size: '14px'

// POVINNE
color: ${theme.color.primary.action}
padding: ${theme.space.space8}
border-radius: ${theme.radius.radius8}
// Typografie pres <Text> nebo <Heading>
```

### 2. Importy komponent

```typescript
// SPRAVNE
import { Button, Badge, Chip } from '@apify/ui-library';

// ZAKAZANO — nikdy duplikovat komponenty
// ZAKAZANO — nikdy importovat z relativnich cest mimo ui-library
```

### 3. Styled Components pattern

```typescript
import styled, { css } from 'styled-components';
import { theme } from '@apify/ui-library';

// $ prefix pro transient props
const StyledComponent = styled.div<{ $variant?: string }>`
    color: ${theme.color.neutral.text};
    padding: ${theme.space.space16};

    ${({ $variant }) => $variant === 'primary' && css`
        background: ${theme.color.primary.background};
    `}
`;
```

### 4. Poradi v souboru

```typescript
// 1. React importy
// 2. styled-components
// 3. @apify/ui-library importy
// 4. Konstanty & typy
// 5. Styled components
// 6. Komponenta + displayName
```

### 5. Barvy — semanticke

```typescript
// Text:       theme.color.{cat}.text, .textMuted, .textSubtle, .textDisabled
// Background: theme.color.{cat}.background, .backgroundSubtle, .backgroundMuted
// Interactive: theme.color.{cat}.action, .actionHover, .actionActive
// Borders:    theme.color.{cat}.border, .separatorSubtle, .fieldBorder
// Icons:      theme.color.{cat}.icon, .iconSubtle, .iconDisabled
```

### 6. Spacing

| Kontext | Tokeny |
|---------|--------|
| Gaps | `space4`, `space8`, `space12` |
| Padding | `space8`, `space12`, `space16` |
| Sekce | `space16`, `space24`, `space32` |
| Layout | `space40`, `space64`, `space80` |

### 7. Typografie

```typescript
// SPRAVNE
<Text type="body" size="regular" weight="normal">Content</Text>
<Heading type="titleL">Title</Heading>

// ZAKAZANO — nikdy primo font properties
```

---

## Verifikace pred odevzdanim

1. **Token audit**: hledat `#[0-9a-fA-F]{3,8}` a `[0-9]+px` — melo byt 0 vysledku
2. **Import check**: vsechny styled-components importuji `theme` z `@apify/ui-library`
3. **Pattern match**: porovnat s existujicimi komponentami

---

## Casty chyby

```typescript
// SPATNE — mix hardcoded a tokenu
padding: ${theme.space.space16} 10px;
// SPRAVNE
padding: ${theme.space.space16} ${theme.space.space10};

// SPATNE — neexistujici vlastnosti
theme.color.neutral.textLight     // neexistuje
theme.color.primary.main          // neexistuje
// SPRAVNE
theme.color.neutral.textMuted     // existuje
theme.color.primary.action        // existuje
```
