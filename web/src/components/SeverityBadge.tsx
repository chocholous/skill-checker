import { Badge } from "@apify/ui-library";

type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";

type BadgeVariant = "danger" | "warning" | "neutral" | "success";

const variantMap: Record<Severity, BadgeVariant> = {
	CRITICAL: "danger",
	HIGH: "warning",
	MEDIUM: "neutral",
	LOW: "success",
};

export function SeverityBadge({ severity }: { severity: string | null }) {
	if (!severity) return null;
	const variant = variantMap[severity as Severity] ?? "neutral";
	return (
		<Badge size="small" variant={variant}>
			{severity}
		</Badge>
	);
}
