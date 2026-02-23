import { Badge } from "@apify/ui-library";
import { CATEGORY_LABELS } from "./categoryConstants";

type CategoryKey = "WF" | "DK" | "BP" | "APF" | "SEC";

type BadgeVariant =
	| "primary_blue"
	| "success"
	| "neutral_muted"
	| "warning"
	| "danger";

const VARIANT_MAP: Record<CategoryKey, BadgeVariant> = {
	WF: "primary_blue",
	DK: "success",
	BP: "neutral_muted",
	APF: "warning",
	SEC: "danger",
};

interface Props {
	category: string;
	showLabel?: boolean;
}

export function CategoryBadge({ category, showLabel = false }: Props) {
	const key = category.toUpperCase() as CategoryKey;
	const variant = VARIANT_MAP[key] ?? "neutral_muted";
	const label = CATEGORY_LABELS[key];
	return (
		<Badge size="small" variant={variant}>
			{showLabel && label ? `${key} — ${label}` : key}
		</Badge>
	);
}
