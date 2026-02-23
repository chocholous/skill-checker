# Tokeny

## Spacing

Pristup: `theme.space.{token}`

| Token | Hodnota | ~px |
|-------|---------|-----|
| `space2` | 0.2rem | 3.2px |
| `space4` | 0.4rem | 6.4px |
| `space6` | 0.6rem | 9.6px |
| `space8` | 0.8rem | 12.8px |
| `space10` | 1rem | 16px |
| `space12` | 1.2rem | 19.2px |
| `space16` | 1.6rem | 25.6px |
| `space24` | 2.4rem | 38.4px |
| `space32` | 3.2rem | 51.2px |
| `space40` | 4rem | 64px |
| `space64` | 6.4rem | 102.4px |
| `space80` | 8rem | 128px |

### Doporuceni

| Kontext | Tokeny |
|---------|--------|
| Gaps mezi elementy | `space4`, `space8`, `space12` |
| Padding komponent | `space8`, `space12`, `space16` |
| Marginy sekci | `space16`, `space24`, `space32` |
| Velke layouty | `space40`, `space64`, `space80` |

---

## Border Radius

Pristup: `theme.radius.{token}`

| Token | Hodnota |
|-------|---------|
| `radius4` | 4px |
| `radius6` | 6px |
| `radius8` | 8px |
| `radius12` | 12px |
| `radius16` | 16px |
| `radius20` | 20px |
| `radiusFull` | 100px |

---

## Shadows

Pristup: `theme.shadow.{token}`

| Token | Pouziti |
|-------|---------|
| `shadowActive` | Active/focused stavy |
| `shadow1` | Jemny elevation |
| `shadow2` | Karty |
| `shadow3` | Dropdown/popover |
| `shadow4` | Modal |
| `shadow5` | Nejvetsi elevation |

Hodnoty jsou CSS promenne (`var(--shadow-N)`), resolvuji se podle light/dark theme.

---

## Transitions

Pristup: `theme.transition.{token}`

| Token | Hodnota | Pouziti |
|-------|---------|---------|
| `smoothEaseIn` | 0.3s ease-in | Pozvolne animace |
| `smoothEaseOut` | 0.3s ease-out | Pozvolne animace |
| `fastEaseIn` | 0.12s ease-in | Hover, focus |
| `fastEaseOut` | 0.12s ease-out | Hover, focus |
| `fastEaseInOut` | 0.12s ease-in-out | Hover, focus |

---

## Breakpoints

### Device (preferovane — s media query syntaxi)

Pristup: `theme.device.{token}`

| Token | Hodnota |
|-------|---------|
| `tablet` | `(min-width: 768px)` |
| `desktop` | `(min-width: 1024px)` |
| `mediumDesktop` | `(min-width: 1200px)` |
| `largeDesktop` | `(min-width: 1440px)` |

```tsx
const Responsive = styled.div`
    padding: ${theme.space.space8};

    @media ${theme.device.tablet} {
        padding: ${theme.space.space16};
    }

    @media ${theme.device.desktop} {
        padding: ${theme.space.space24};
    }
`;
```

### Layout (deprecated — jen px hodnoty)

Pristup: `theme.layout.{token}`

| Token | Hodnota |
|-------|---------|
| `tablet` | 768px |
| `desktop` | 1024px |
| `mediumDesktop` | 1200px |
| `largeDesktop` | 1440px |
