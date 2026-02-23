import { Text, theme } from "@apify/ui-library";
import styled from "styled-components";

const LegendWrapper = styled.div`
	display: flex;
	align-items: center;
	gap: ${theme.space.space16};
	padding: ${theme.space.space8} 0;
`;

const LegendItem = styled.div`
	display: flex;
	align-items: center;
	gap: ${theme.space.space4};
`;

const ColorDot = styled.div<{ $color: string }>`
	width: 1.2rem;
	height: 1.2rem;
	border-radius: ${theme.radius.radius4};
	background: ${(p) => p.$color};
`;

const items = [
	{ label: "Pass", color: theme.color.success.backgroundSubtle },
	{ label: "Fail", color: theme.color.danger.backgroundSubtle },
	{ label: "Unclear", color: theme.color.warning.backgroundSubtle },
	{ label: "N/A", color: theme.color.neutral.backgroundMuted },
];

export function HeatmapLegend() {
	return (
		<LegendWrapper>
			{items.map((item) => (
				<LegendItem key={item.label}>
					<ColorDot $color={item.color} />
					<Text type="body" size="small" color={theme.color.neutral.textMuted}>
						{item.label}
					</Text>
				</LegendItem>
			))}
		</LegendWrapper>
	);
}
