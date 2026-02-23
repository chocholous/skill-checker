import { Button, Heading, Text, theme } from "@apify/ui-library";
import { useState } from "react";
import styled from "styled-components";
import type { CellDetail } from "../api/client";
import { MarkdownViewer } from "./MarkdownViewer";

const Overlay = styled.div`
	position: fixed;
	top: 0;
	right: 0;
	bottom: 0;
	left: 0;
	background: rgba(0, 0, 0, 0.3);
	z-index: 100;
`;

const Panel = styled.div`
	position: fixed;
	top: 0;
	right: 0;
	bottom: 0;
	width: 64rem;
	max-width: 90vw;
	background: ${theme.color.neutral.cardBackground};
	box-shadow: ${theme.shadow.shadow5};
	z-index: 101;
	display: flex;
	flex-direction: column;
	overflow: hidden;
`;

const PanelHeader = styled.div`
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: ${theme.space.space16};
	border-bottom: 1px solid ${theme.color.neutral.border};
`;

const PanelBody = styled.div`
	flex: 1;
	overflow-y: auto;
	padding: ${theme.space.space16};
`;

const ComparisonGrid = styled.div`
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: ${theme.space.space16};

	@media (max-width: 768px) {
		grid-template-columns: 1fr;
	}
`;

const SkillColumn = styled.div`
	border: 1px solid ${theme.color.neutral.border};
	border-radius: ${theme.radius.radius8};
	padding: ${theme.space.space12};
`;

const ResultBadge = styled.span<{ $result: string }>`
	display: inline-block;
	padding: 0.2rem ${theme.space.space8};
	border-radius: ${theme.radius.radius4};
	font-size: 1.2rem;
	font-weight: 600;
	text-transform: uppercase;
	background: ${(p) => {
		switch (p.$result) {
			case "pass":
				return theme.color.success.backgroundSubtle;
			case "fail":
				return theme.color.danger.backgroundSubtle;
			case "unclear":
				return theme.color.warning.backgroundSubtle;
			default:
				return theme.color.neutral.backgroundMuted;
		}
	}};
	color: ${(p) => {
		switch (p.$result) {
			case "pass":
				return theme.color.success.text;
			case "fail":
				return theme.color.danger.text;
			case "unclear":
				return theme.color.warning.text;
			default:
				return theme.color.neutral.textMuted;
		}
	}};
`;

const EvidenceBox = styled.div`
	background: ${theme.color.neutral.backgroundMuted};
	border-radius: ${theme.radius.radius6};
	padding: ${theme.space.space8};
	margin-top: ${theme.space.space8};
	font-size: 1.2rem;
	line-height: 1.6;
	white-space: pre-wrap;
	max-height: 20rem;
	overflow-y: auto;
`;

const ExpandSection = styled.div`
	margin-top: ${theme.space.space12};
	padding-top: ${theme.space.space12};
	border-top: 1px solid ${theme.color.neutral.separatorSubtle};
`;

interface SkillResultProps {
	label: string;
	data: CellDetail["specialist"];
}

function SkillResult({ label, data }: SkillResultProps) {
	const [expanded, setExpanded] = useState(false);

	if (!data) {
		return (
			<SkillColumn>
				<Text type="body" size="small" weight="bold" mb="space8">
					{label}
				</Text>
				<Text type="body" size="small" color={theme.color.neutral.textMuted}>
					No data
				</Text>
			</SkillColumn>
		);
	}

	return (
		<SkillColumn>
			<Text type="body" size="small" weight="bold" mb="space4">
				{label}
			</Text>
			<Text
				type="code"
				size="small"
				color={theme.color.neutral.textMuted}
				mb="space8"
			>
				{data.skill} ({data.model})
			</Text>

			<div>
				<ResultBadge $result={data.result}>{data.result}</ResultBadge>
			</div>

			{data.summary && (
				<Text type="body" size="small" mt="space8">
					{data.summary}
				</Text>
			)}

			{data.evidence && <EvidenceBox>{data.evidence}</EvidenceBox>}

			{data.markdown_response && (
				<ExpandSection>
					<Button
						variant="tertiary"
						size="small"
						onClick={() => setExpanded(!expanded)}
					>
						{expanded ? "Hide full analysis" : "View full analysis"}
					</Button>
					{expanded && (
						<div style={{ marginTop: "0.8rem" }}>
							<MarkdownViewer content={data.markdown_response} />
						</div>
					)}
				</ExpandSection>
			)}
		</SkillColumn>
	);
}

interface Props {
	detail: CellDetail;
	onClose: () => void;
}

export function CellDetailPanel({ detail, onClose }: Props) {
	return (
		<>
			<Overlay onClick={onClose} />
			<Panel>
				<PanelHeader>
					<div>
						<Heading type="titleS">
							{detail.scenario_id} / {detail.check_id}
						</Heading>
					</div>
					<Button variant="tertiary" size="small" onClick={onClose}>
						Close
					</Button>
				</PanelHeader>
				<PanelBody>
					<ComparisonGrid>
						<SkillResult label="Specialist" data={detail.specialist} />
						<SkillResult label="MCPC" data={detail.mcpc} />
					</ComparisonGrid>
				</PanelBody>
			</Panel>
		</>
	);
}
