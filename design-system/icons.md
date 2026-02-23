# Ikony (@apify/ui-icons)

```bash
npm install @apify/ui-icons
```

## Pouziti

```tsx
import { PlayIcon, SearchIcon, SettingsIcon } from '@apify/ui-icons';

// Jako samostatna ikona
<PlayIcon size="20" />

// V Button
import { Button } from '@apify/ui-library';
<Button LeftIcon={PlayIcon} size="medium">Run</Button>

// V IconButton
import { IconButton } from '@apify/ui-library';
<IconButton Icon={DeleteIcon} variant="DANGER" title="Smazat" onClick={...} />

// V Badge/Tag
<Badge LeadingIcon={CheckIcon} variant="success">Done</Badge>
<Tag LeadingIcon={WarningTriangleIcon} variant="warning">Caution</Tag>
```

## Velikosti

| Size | px | Pouziti |
|------|----|---------|
| `"12"` | 12px | Extra male, inline s textem |
| `"16"` | 16px | Male, labely, badges |
| `"20"` | 20px | Default, buttony, navigace |
| `"24"` | 24px | Vetsi, nadpisy |
| `"40"` | 40px | Hero, prazdne stavy |

## Props

```typescript
type IconProps = React.SVGProps<SVGSVGElement> & {
    size?: '12' | '16' | '20' | '24' | '40';
    role?: React.AriaRole;
    className?: string;
    style?: React.CSSProperties;
    title?: string;      // accessible name
    titleId?: string;
};
```

## Dostupne ikony (168)

### Navigace & akce
`ArrowLeftIcon`, `ArrowRightIcon`, `ArrowDownCircleIcon`, `ArrowSortIcon`, `ArrowSortDownIcon`, `ArrowSortUpIcon`, `CaretDownIcon`, `CaretUpIcon`, `CaretUpDownIcon`, `ChevronDownIcon`, `ChevronLeftIcon`, `ChevronRightIcon`, `ChevronSelectIcon`, `ChevronUpIcon`, `BackLink` (via ui-library)

### Stav & feedback
`CheckIcon`, `CheckCircleIcon`, `CrossIcon`, `XCircleIcon`, `CircleDashXIcon`, `InfoIcon`, `WarningTriangleIcon`, `QuestionMarkIcon`, `SkullIcon`

### Akce
`PlayIcon`, `PlayCircleIcon`, `StopCircleIcon`, `RefreshIcon`, `RefreshAutoIcon`, `RotateIcon`, `SearchIcon`, `FilterIcon`, `SortAscendingIcon`, `SortDescendingIcon`, `ExpandIcon`, `CollapseIcon`, `FullscreenIcon`, `MinimizeIcon`, `PlusIcon`, `MinusIcon`, `MoreIcon`, `MenuIcon`, `DragIndicatorIcon`

### CRUD & soubory
`EditIcon`, `DeleteIcon`, `CopyIcon`, `DownloadIcon`, `UploadIcon`, `FileUploadIcon`, `ImportFileIcon`, `CreateFileIcon`, `CreateFolderIcon`, `FileIcon`, `FolderIcon`, `FolderOpenIcon`, `DocumentIcon`, `ImageIcon`

### Komunikace
`EmailIcon`, `EmailOpenedIcon`, `CommentIcon`, `ShareIcon`, `PhoneIcon`, `BellIcon`, `MegaphoneIcon`

### Dev & tech
`CodeIcon`, `CodeAiIcon`, `TerminalIcon`, `ApiIcon`, `GitIcon`, `GitBranchIcon`, `DockerIcon`, `NpmIcon`, `FormatCodeIcon`, `WebhookIcon`, `ServerIcon`, `McpIcon`

### Jazyky & formaty
`JavascriptIcon`, `TypescriptIcon`, `PythonIcon`, `CssIcon`, `HtmlIcon`, `JsonIcon`, `MarkdownIcon`, `PdfIcon`

### UI & layout
`LayoutIcon`, `LayoutSidebarIcon`, `SidebarCollapseIcon`, `SidebarExpandIcon`, `ColumnsIcon`, `HomeIcon`, `GlobeIcon`, `SettingsIcon`, `AdjustmentIcon`, `InputIcon`, `OutputIcon`

### AI & platformy
`AnthropicIcon`, `ClaudeIcon`, `ChatGptIcon`, `PerplexityIcon`, `SparkleIcon`, `BoxAiIcon`

### Social
`DiscordIcon`, `FacebookIcon`, `LinkedinIcon`, `TwitterIcon`

### Business
`AnalyticsIcon`, `BuildingIcon`, `BuildingBankIcon`, `CreditCardIcon`, `CoinIcon`, `ShoppingCartIcon`, `PeopleIcon`, `PersonIcon`, `IdBadgeIcon`

### Misc
`BookOpenIcon`, `BookmarkIcon`, `BookmarkSolidIcon`, `BuildIcon`, `CalendarIcon`, `ClockIcon`, `ClockStopIcon`, `CloudIcon`, `CursorIcon`, `DevelopmentIcon`, `DeviceDesktopIcon`, `DeviceMobileIcon`, `DeviceTabletIcon`, `ExamplesIcon`, `ExternalLinkIcon`, `EyeIcon`, `EyeDynamicIcon`, `EyeOffIcon`, `FlagIcon`, `HeartbeatIcon`, `HourglassIcon`, `InfinityIcon`, `KeyValueStoreIcon`, `KeyboardIcon`, `CommandIcon`, `LightbulbIcon`, `LinkIcon`, `LoaderIcon`, `LockIcon`, `UnlockIcon`, `LogIcon`, `LogOutIcon`, `PasswordIcon`, `PlaceholderIcon`, `PuzzleIcon`, `RocketIcon`, `ShieldIcon`, `StandbyIcon`, `StarEmptyIcon`, `StarFullIcon`, `StarHalfIcon`, `StorageIcon`, `SunIcon`, `SwitchIcon`, `TagIcon`, `ThumbsUpIcon`, `TimeDuration0Icon`, `TimeDuration30Icon`, `VectorTriangleIcon`, `VscodeIcon`, `WifiIcon`, `BoxIcon`

## Utility

```typescript
import { withSize } from '@apify/ui-icons';

// Preset velikosti — vytvori wrapper ktery automaticky nastavi size
const SmallIcon = withSize('16')(PlayIcon);
<SmallIcon />  // vzdy 16px
```
