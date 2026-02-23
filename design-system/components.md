# Komponenty

Vsechny importy z `@apify/ui-library`.

---

## Button

```tsx
import { Button } from '@apify/ui-library';

<Button
    size="medium"           // 'extraLarge' | 'large' | 'medium' | 'small' | 'extraSmall'
    color="default"         // 'default' | 'success' | 'danger' | 'primaryBlack'
    variant="primary"       // 'primary' | 'secondary' | 'tertiary'
    type="button"           // 'button' | 'submit'
    onClick={(e) => {}}
    disabled={false}
    LeftIcon={SomeIcon}     // React.ElementType (z @apify/ui-icons)
    RightIcon={SomeIcon}
>
    Label
</Button>

// Jako link:
<Button href="/path" target="_blank">Link Button</Button>
<Button to="/internal-path">Router Link</Button>
```

Margin props: `m`, `mt`, `mb`, `ml`, `mr`, `mx`, `my`

---

## Badge

```tsx
import { Badge } from '@apify/ui-library';

<Badge
    size="regular"          // 'large' | 'regular' | 'small' | 'extra_small'
    variant="neutral"       // 'neutral' | 'neutral_muted' | 'neutral_subtle'
                            // 'primary_black' | 'primary_blue'
                            // 'success' | 'warning' | 'danger'
    type="body"             // 'body' | 'code'
    LeadingIcon={Icon}
    TrailingIcon={Icon}
>
    Status
</Badge>
```

---

## Chip

```tsx
import { Chip, PrimaryChip, SuccessChip, DangerChip, WarningChip, NeutralChip } from '@apify/ui-library';

<Chip
    type="DEFAULT"          // 'DEFAULT' | 'PRIMARY' | 'SUCCESS' | 'WARNING' | 'DANGER'
    size="M"                // 'XS' | 'S' | 'M' | 'L'
    icon={<SomeIcon />}
    clickable={false}
>
    Label
</Chip>

// Convenience:
<SuccessChip size="S">Done</SuccessChip>
<DangerChip>Error</DangerChip>
```

---

## Tag

```tsx
import { Tag } from '@apify/ui-library';

<Tag
    as="button"             // 'a' | 'button'
    size="regular"          // 'regular' | 'small' | 'big'
    variant="primary"       // 'primary' | 'secondary' | 'subtle' | 'accent'
                            // 'success' | 'warning' | 'error'
    LeadingIcon={Icon}
    TrailingIcon={Icon}
    onClick={() => {}}      // kdyz as="button"
    disabled={false}
>
    Tag Label
</Tag>

// Jako link:
<Tag as="a" to="/path" variant="primary">Link Tag</Tag>
```

---

## Text

```tsx
import { Text } from '@apify/ui-library';

<Text
    type="body"             // 'body' | 'code'
    size="regular"          // 'regular' | 'small' | 'big'
    weight="normal"         // 'normal' | 'medium' | 'bold'
    italic={false}
    uppercase={false}
    align="left"            // 'left' | 'right' | 'center'
    color={theme.color.neutral.textMuted}  // optional override
    as="span"               // HTML element
>
    Body text
</Text>
```

---

## Heading

```tsx
import { Heading } from '@apify/ui-library';

<Heading
    type="titleL"           // 'titleXs' | 'titleS' | 'titleM' | 'titleL'
                            // 'titleXl' | 'title2xl' | 'title3xl'
    italic={false}
    uppercase={false}
    align="left"            // 'left' | 'right' | 'center'
    as="h2"                 // HTML element
>
    Page Title
</Heading>
```

---

## Box

Zakladni layout kontejner se spacing props.

```tsx
import { Box } from '@apify/ui-library';

<Box
    // Margin: m, mt, mb, ml, mr, mx, my
    // Padding: p, pt, pb, pl, pr, px, py
    // Hodnoty: size tokeny ('space8', 'space16'...) | 'none' | 'auto'
    p="space16"
    mt="space8"
    as="section"
>
    Content
</Box>
```

---

## CardContainer

```tsx
import { CardContainer } from '@apify/ui-library';

<CardContainer header="Card Title">
    Card content
</CardContainer>

// Custom header:
<CardContainer header={<CardContainer.Heading>Custom</CardContainer.Heading>}>
    Content
</CardContainer>

// headerPlacement: 'TOP' | 'BOTTOM'
```

---

## Message

```tsx
import { Message, InfoMessage, WarningMessage, SuccessMessage, DangerMessage } from '@apify/ui-library';

<Message
    type="info"             // 'info' | 'warning' | 'success' | 'danger'
    caption="Optional caption"
    Icon={CustomIcon}
    borderless={false}
    boxless={false}
    onDismissClick={() => {}}
    actions={[{ label: 'Action', onClick: () => {} }]}
>
    Message content
</Message>

// Convenience:
<InfoMessage>Informational text</InfoMessage>
<DangerMessage>Error occurred</DangerMessage>
```

---

## Banner

```tsx
import { Banner } from '@apify/ui-library';

<Banner
    background={theme.color.primary.background}
    useGradientBackground={false}
    width="100%"
>
    Banner content
</Banner>
```

---

## Tabs

```tsx
import { Tabs } from '@apify/ui-library';

const tabs = [
    { id: 'tab1', title: 'First', to: '/tab1' },
    { id: 'tab2', title: 'Second', to: '/tab2', chip: 5 },
    { id: 'tab3', title: 'Beta', to: '/tab3', rollout: 'beta' },
    { id: 'tab4', title: 'Disabled', to: '/tab4', disabled: true },
];

<Tabs
    tabs={tabs}
    variant="default"       // 'default' | 'boxed' | 'buttoned'
    activeTab="tab1"
    onSelect={({ id, href, event }) => {}}
/>
```

TabData: `{ id, title, to, Icon?, chip?, rollout?, disabled? }`

---

## Menu

```tsx
import { Menu } from '@apify/ui-library';

const options = [
    { value: 'opt1', label: 'Option 1' },
    { value: 'opt2', label: 'Option 2' },
];

<Menu
    options={options}
    value="opt1"
    onSelect={(newValue, selectedBy) => {}}
    defaultLabel="Select..."
    closeOnSelect={true}
    placement="bottom-start"
    renderOption={(option) => <span>{option.label}</span>}
/>
```

selectedBy: `'click' | 'enter' | 'space' | 'type'`

---

## Tooltip

```tsx
import { Tooltip } from '@apify/ui-library';

<Tooltip
    content="Tooltip text"
    placement="top"         // 'top' | 'top-start' | 'top-end' | 'right' | 'bottom' | 'left' (+ start/end)
    size="medium"           // 'xsmall' | 'small' | 'medium' | 'large' | 'xlarge'
    textAlign="left"        // 'left' | 'center'
    delayShow={200}
    delayHide={0}
    shortcuts={['Ctrl', 'S']}
    offsetPx={8}
>
    <span>Hover me</span>
</Tooltip>
```

---

## Spinner

```tsx
import { Spinner, BlockSpinner, InlineSpinner } from '@apify/ui-library';

<Spinner small={false} loadingReason="Loading data..." />
<BlockSpinner />           // Block-level centered
<InlineSpinner />          // Inline, inherits text color
```

---

## IconButton

```tsx
import { IconButton } from '@apify/ui-library';
import { SomeIcon } from '@apify/ui-icons';

<IconButton
    as="button"             // 'a' | 'button'
    Icon={SomeIcon}         // required
    variant="DEFAULT"       // 'DEFAULT' | 'BORDERED' | 'DANGER' | 'DANGER_BORDERED' | 'PRIMARY_BLACK'
    size="medium"
    disabled={false}
    isLoading={false}
    title="Delete"          // tooltip text
    onClick={() => {}}
/>
```

---

## Link

```tsx
import { Link } from '@apify/ui-library';

<Link
    to="/path"              // string | Partial<Path> (required)
    hideExternalIcon={false}
    showExternalIcon={false}
    rel="noopener"
    target="_blank"
>
    Click here
</Link>
```

Utility funkce: `isUrlExternal()`, `isUrlEmail()`, `omitDomainAndProtocol()`, `hasUrlHttpProtocol()`

---

## Image

```tsx
import { Image } from '@apify/ui-library';

<Image
    src="/path/to/image.png"  // required
    alt="Description"
    width={200}
    height={150}
    loading="lazy"            // 'eager' | 'lazy'
/>
```

---

## Tile

```tsx
import { Tile } from '@apify/ui-library';

<Tile
    content={<div>Tile content</div>}  // required
    size="LARGE"            // 'SMALL' | 'LARGE'
    isClickable={true}
    onClick={() => {}}
/>
```

---

## Rating

```tsx
import { Rating, SingleStarRating } from '@apify/ui-library';

<Rating rating={4.5} color={theme.color.warning.text} />
<SingleStarRating color={theme.color.warning.text} />
```

---

## Spolecne props (vetsina komponent)

- **Box props**: `children`, `className`, `style`, `onClick`, `id`, `as`
- **Margin**: `m`, `mt`, `mb`, `ml`, `mr`, `mx`, `my`
- **Padding** (Box): `p`, `pt`, `pb`, `pl`, `pr`, `px`, `py`
