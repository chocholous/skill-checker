import { Tag, Tooltip } from "@apify/ui-library";

import { SeverityBadge } from "./SeverityBadge";

interface Props {
	id: string;
	name: string | null;
	severity: string | null;
	description: string | null;
}

export function CategoryTag({ id, name, severity, description }: Props) {
	const hasTooltip = Boolean(name || description);

	const tooltipLines: string[] = [];
	if (name) tooltipLines.push(`${id}: ${name}`);
	if (description) tooltipLines.push(description);
	const tooltipContent = tooltipLines.join("\n");

	const tag = (
		<Tag as="button" size="small" variant="secondary">
			<SeverityBadge severity={severity} />
			{id}
		</Tag>
	);

	if (!hasTooltip) {
		return tag;
	}

	return (
		<Tooltip content={tooltipContent} placement="top" size="medium">
			{tag}
		</Tooltip>
	);
}
