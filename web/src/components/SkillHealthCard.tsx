import { Text, theme } from "@apify/ui-library";
import styled from "styled-components";
import type { SkillHealth } from "../api/client";

const Card = styled.div`
	background: ${theme.color.neutral.cardBackground};
	border-radius: ${theme.radius.radius8};
	box-shadow: ${theme.shadow.shadow1};
	padding: ${theme.space.space16};
	cursor: pointer;
	transition: box-shadow ${theme.transition.fastEaseInOut},
		transform ${theme.transition.fastEaseInOut};

	&:hover {
		box-shadow: ${theme.shadow.shadow3};
		transform: translateY(-1px);
	}
`;

const CardHeader = styled.div`
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: ${theme.space.space8};
`;

const SkillName = styled(Text)`
	font-family: "IBM Plex Mono", monospace;
`;

const DevBadge = styled.span`
	font-size: 1rem;
	padding: 0.2rem ${theme.space.space6};
	border-radius: ${theme.radius.radius4};
	background: ${theme.color.primary.backgroundSubtle};
	color: ${theme.color.primary.text};
	font-weight: 600;
`;

const ProgressBarOuter = styled.div`
	width: 100%;
	height: 0.8rem;
	border-radius: ${theme.radius.radius4};
	background: ${theme.color.neutral.backgroundMuted};
	overflow: hidden;
	margin-bottom: ${theme.space.space8};
`;

const ProgressBarInner = styled.div<{ $pct: number; $color: string }>`
	height: 100%;
	width: ${(p) => p.$pct}%;
	background: ${(p) => p.$color};
	border-radius: ${theme.radius.radius4};
	transition: width 0.3s ease;
`;

const StatsRow = styled.div`
	display: flex;
	gap: ${theme.space.space12};
	margin-bottom: ${theme.space.space8};
`;

const StatItem = styled.div`
	display: flex;
	align-items: center;
	gap: ${theme.space.space4};
`;

const StatDot = styled.div<{ $color: string }>`
	width: 0.8rem;
	height: 0.8rem;
	border-radius: 50%;
	background: ${(p) => p.$color};
`;

const GapsSection = styled.div`
	margin-top: ${theme.space.space8};
	padding-top: ${theme.space.space8};
	border-top: 1px solid ${theme.color.neutral.separatorSubtle};
`;

const GapItem = styled.div`
	display: flex;
	align-items: center;
	gap: ${theme.space.space4};
	margin-bottom: ${theme.space.space2};
`;

function pctColor(pct: number): string {
	if (pct >= 70) return theme.color.success.background;
	if (pct >= 40) return theme.color.warning.background;
	return theme.color.danger.background;
}

interface Props {
	health: SkillHealth;
	onClick: () => void;
}

export function SkillHealthCard({ health, onClick }: Props) {
	return (
		<Card onClick={onClick}>
			<CardHeader>
				<SkillName type="body" size="small" weight="bold">
					{health.skill.replace("apify-", "")}
				</SkillName>
				{health.is_dev && <DevBadge>DEV</DevBadge>}
			</CardHeader>

			<Text
				type="body"
				size="small"
				color={theme.color.neutral.textMuted}
				mb="space4"
			>
				{health.domain}
			</Text>

			<ProgressBarOuter>
				<ProgressBarInner
					$pct={health.pass_pct}
					$color={pctColor(health.pass_pct)}
				/>
			</ProgressBarOuter>

			<Text type="body" size="small" weight="bold" mb="space4">
				{health.pass_pct}% pass
			</Text>

			<StatsRow>
				<StatItem>
					<StatDot $color={theme.color.success.backgroundSubtle} />
					<Text type="body" size="small">
						{health.pass_count}
					</Text>
				</StatItem>
				<StatItem>
					<StatDot $color={theme.color.danger.backgroundSubtle} />
					<Text type="body" size="small">
						{health.fail_count}
					</Text>
				</StatItem>
				<StatItem>
					<StatDot $color={theme.color.warning.backgroundSubtle} />
					<Text type="body" size="small">
						{health.unclear_count}
					</Text>
				</StatItem>
			</StatsRow>

			{health.top_gaps.length > 0 && (
				<GapsSection>
					<Text
						type="body"
						size="small"
						color={theme.color.neutral.textMuted}
						mb="space4"
					>
						Top gaps:
					</Text>
					{health.top_gaps.slice(0, 3).map((g) => (
						<GapItem key={g.check_id}>
							<Text type="code" size="small" color={theme.color.danger.text}>
								{g.check_id}
							</Text>
							<Text type="body" size="small">
								{g.name}
							</Text>
						</GapItem>
					))}
				</GapsSection>
			)}
		</Card>
	);
}
