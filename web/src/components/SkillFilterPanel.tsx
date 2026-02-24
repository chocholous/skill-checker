import { Text, theme } from "@apify/ui-library";
import styled from "styled-components";
import type { SkillHealth } from "../api/client";

const PanelCard = styled.div`
	background: ${theme.color.neutral.cardBackground};
	border: 1px solid ${theme.color.neutral.border};
	border-radius: ${theme.radius.radius8};
	box-shadow: ${theme.shadow.shadow1};
	padding: ${theme.space.space16};
	margin-bottom: ${theme.space.space16};
`;

const Header = styled.div`
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: ${theme.space.space12};
`;

const ToggleRow = styled.div`
	display: flex;
	gap: ${theme.space.space8};
`;

const ToggleButton = styled.button`
	background: none;
	border: 1px solid ${theme.color.neutral.border};
	border-radius: ${theme.radius.radius4};
	padding: ${theme.space.space2} ${theme.space.space8};
	font-size: 1.2rem;
	color: ${theme.color.neutral.text};
	cursor: pointer;
	transition: background ${theme.transition.fastEaseInOut};

	&:hover {
		background: ${theme.color.neutral.hover};
	}
`;

const SkillList = styled.div`
	display: flex;
	flex-direction: column;
	gap: ${theme.space.space4};
	max-height: 32rem;
	overflow-y: auto;
`;

const SkillRow = styled.label`
	display: flex;
	align-items: center;
	gap: ${theme.space.space8};
	padding: ${theme.space.space4} ${theme.space.space8};
	border-radius: ${theme.radius.radius4};
	cursor: pointer;
	transition: background ${theme.transition.fastEaseInOut};

	&:hover {
		background: ${theme.color.neutral.hover};
	}
`;

const NativeCheckbox = styled.input`
	width: 1.6rem;
	height: 1.6rem;
	cursor: pointer;
	accent-color: ${theme.color.primary.action};
	flex-shrink: 0;
`;

const SkillName = styled.span`
	font-family: "IBM Plex Mono", monospace;
	font-size: 1.3rem;
	font-weight: 600;
	color: ${theme.color.neutral.text};
	flex-shrink: 0;
`;

const PassPct = styled.span<{ $pct: number }>`
	font-size: 1.2rem;
	font-weight: 600;
	margin-left: auto;
	color: ${(p) => {
		if (p.$pct >= 70) return theme.color.success.text;
		if (p.$pct >= 40) return theme.color.warning.text;
		return theme.color.danger.text;
	}};
`;

const ModelBadge = styled.span<{ $color: string }>`
	display: inline-block;
	padding: 0.1rem ${theme.space.space4};
	border-radius: ${theme.radius.radius4};
	font-size: 1rem;
	font-weight: 600;
	background: ${(p) => p.$color};
	color: ${theme.color.neutral.cardBackground};
	text-transform: uppercase;
	letter-spacing: 0.03em;
`;

const MODEL_COLORS: Record<string, string> = {
	sonnet: theme.color.primary.background,
	opus: theme.color.danger.background,
	haiku: theme.color.success.background,
};

interface Props {
	skills: SkillHealth[];
	selectedDomains: string[];
	onToggle: (domainId: string) => void;
	onSelectAll: () => void;
	onSelectNone: () => void;
}

export function SkillFilterPanel({
	skills,
	selectedDomains,
	onToggle,
	onSelectAll,
	onSelectNone,
}: Props) {
	return (
		<PanelCard>
			<Header>
				<Text type="body" size="small" weight="bold">
					Skills
				</Text>
				<ToggleRow>
					<ToggleButton onClick={onSelectAll}>All</ToggleButton>
					<ToggleButton onClick={onSelectNone}>None</ToggleButton>
				</ToggleRow>
			</Header>
			<SkillList>
				{skills.map((h) => (
					<SkillRow key={h.skill}>
						<NativeCheckbox
							type="checkbox"
							checked={selectedDomains.includes(h.domain)}
							onChange={() => onToggle(h.domain)}
						/>
						<SkillName>{h.skill.replace("apify-", "")}</SkillName>
						{h.models?.map((m) => (
							<ModelBadge
								key={m}
								$color={MODEL_COLORS[m] ?? theme.color.neutral.textMuted}
							>
								{m.slice(0, 3)}
							</ModelBadge>
						))}
						<PassPct $pct={h.pass_pct}>{h.pass_pct}%</PassPct>
					</SkillRow>
				))}
			</SkillList>
		</PanelCard>
	);
}
