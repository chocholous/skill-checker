import { Text, Tooltip, theme } from "@apify/ui-library";
import styled from "styled-components";
import type { CellResult } from "../api/client";

const resultColors: Record<string, string> = {
	pass: theme.color.success.backgroundSubtle,
	fail: theme.color.danger.backgroundSubtle,
	unclear: theme.color.warning.backgroundSubtle,
	na: theme.color.neutral.backgroundMuted,
};

const resultTextColors: Record<string, string> = {
	pass: theme.color.success.text,
	fail: theme.color.danger.text,
	unclear: theme.color.warning.text,
	na: theme.color.neutral.textMuted,
};

const SplitCellWrapper = styled.div<{ $clickable?: boolean }>`
	display: flex;
	min-width: 6rem;
	height: 3.2rem;
	border-radius: ${theme.radius.radius4};
	overflow: hidden;
	cursor: ${(p) => (p.$clickable ? "pointer" : "default")};
	border: 1px solid ${theme.color.neutral.border};

	&:hover {
		box-shadow: ${theme.shadow.shadow2};
	}
`;

const HalfCell = styled.div<{ $color: string }>`
	flex: 1;
	display: flex;
	align-items: center;
	justify-content: center;
	background: ${(p) => p.$color};
	min-width: 3rem;
`;

const SingleCellWrapper = styled.div<{ $color: string; $clickable?: boolean }>`
	display: flex;
	align-items: center;
	justify-content: center;
	min-width: 6rem;
	height: 3.2rem;
	border-radius: ${theme.radius.radius4};
	background: ${(p) => p.$color};
	cursor: ${(p) => (p.$clickable ? "pointer" : "default")};
	border: 1px solid ${theme.color.neutral.border};

	&:hover {
		box-shadow: ${theme.shadow.shadow2};
	}
`;

const ResultLabel = styled(Text)<{ $textColor: string }>`
	color: ${(p) => p.$textColor};
	font-size: 1rem;
	text-transform: uppercase;
	font-weight: 600;
	letter-spacing: 0.05em;
`;

function resultChar(result: string): string {
	switch (result) {
		case "pass":
			return "P";
		case "fail":
			return "F";
		case "unclear":
			return "?";
		case "na":
			return "-";
		default:
			return "?";
	}
}

interface SplitCellProps {
	specialist: CellResult | null;
	mcpc: CellResult | null;
	onClick?: () => void;
}

export function SplitHeatmapCell({
	specialist,
	mcpc,
	onClick,
}: SplitCellProps) {
	const specResult = specialist?.result ?? "na";
	const mcpcResult = mcpc?.result ?? "na";

	return (
		<Tooltip
			content={`Specialist: ${specResult} | MCPC: ${mcpcResult}`}
			delayShow={300}
		>
			<SplitCellWrapper onClick={onClick} $clickable={!!onClick}>
				<HalfCell $color={resultColors[specResult] ?? resultColors.na}>
					<ResultLabel
						type="body"
						size="small"
						$textColor={resultTextColors[specResult] ?? resultTextColors.na}
					>
						{resultChar(specResult)}
					</ResultLabel>
				</HalfCell>
				<HalfCell $color={resultColors[mcpcResult] ?? resultColors.na}>
					<ResultLabel
						type="body"
						size="small"
						$textColor={resultTextColors[mcpcResult] ?? resultTextColors.na}
					>
						{resultChar(mcpcResult)}
					</ResultLabel>
				</HalfCell>
			</SplitCellWrapper>
		</Tooltip>
	);
}

interface SingleCellProps {
	result: string;
	detail?: string;
	onClick?: () => void;
}

export function SingleHeatmapCell({
	result,
	detail,
	onClick,
}: SingleCellProps) {
	const color = resultColors[result] ?? resultColors.na;
	const textColor = resultTextColors[result] ?? resultTextColors.na;

	return (
		<Tooltip
			content={`${result.toUpperCase()}${detail ? `: ${detail}` : ""}`}
			delayShow={300}
		>
			<SingleCellWrapper
				$color={color}
				onClick={onClick}
				$clickable={!!onClick}
			>
				<ResultLabel type="body" size="small" $textColor={textColor}>
					{resultChar(result)}
				</ResultLabel>
			</SingleCellWrapper>
		</Tooltip>
	);
}
