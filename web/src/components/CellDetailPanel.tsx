import { CopyIcon, CrossIcon, ExpandIcon } from "@apify/ui-icons";
import { Button, IconButton, Text, theme } from "@apify/ui-library";
import { useState } from "react";
import styled from "styled-components";
import type { CellDetail, SkillDetail } from "../api/client";
import { AnalysisModal } from "./AnalysisModal";
import { SeverityBadge } from "./SeverityBadge";

const Overlay = styled.div`
	position: fixed;
	inset: 0;
	background: ${theme.color.neutral.overlay};
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
	padding: ${theme.space.space12} ${theme.space.space16};
	border-bottom: 1px solid ${theme.color.neutral.border};
	background: ${theme.color.neutral.backgroundMuted};
`;

const HeaderLeft = styled.div`
	display: flex;
	align-items: center;
	gap: ${theme.space.space8};
	min-width: 0;
`;

const PanelBody = styled.div`
	flex: 1;
	overflow-y: auto;
	padding: ${theme.space.space16};
`;

const ModelSection = styled.div`
	margin-bottom: ${theme.space.space16};
	border: 1px solid ${theme.color.neutral.border};
	border-radius: ${theme.radius.radius8};
	overflow: hidden;
`;

const ModelHeader = styled.div`
	padding: ${theme.space.space8} ${theme.space.space12};
	background: ${theme.color.neutral.backgroundMuted};
	border-bottom: 1px solid ${theme.color.neutral.border};
`;

const SkillGrid = styled.div`
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: ${theme.space.space12};
	padding: ${theme.space.space12};

	@media (max-width: 768px) {
		grid-template-columns: 1fr;
	}
`;

const SkillColumn = styled.div`
	border: 1px solid ${theme.color.neutral.separatorSubtle};
	border-radius: ${theme.radius.radius6};
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

const EvidenceWrapper = styled.div`
	position: relative;
	margin-top: ${theme.space.space8};
`;

const EvidenceBox = styled.div`
	background: ${theme.color.neutral.backgroundMuted};
	border-radius: ${theme.radius.radius6};
	padding: ${theme.space.space8};
	padding-right: ${theme.space.space32};
	font-size: 1.2rem;
	line-height: 1.6;
	white-space: pre-wrap;
	max-height: 20rem;
	overflow-y: auto;
`;

const CopyButton = styled.div`
	position: absolute;
	top: ${theme.space.space4};
	right: ${theme.space.space4};
`;

const ActionRow = styled.div`
	margin-top: ${theme.space.space12};
	padding-top: ${theme.space.space12};
	border-top: 1px solid ${theme.color.neutral.separatorSubtle};
`;

interface AnalysisModalState {
	model: string;
	skillLabel: string;
	content: string;
}

interface SkillResultProps {
	label: string;
	data: SkillDetail | null;
	onOpenAnalysis: (content: string) => void;
}

function SkillResult({ label, data, onOpenAnalysis }: SkillResultProps) {
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
				{data.skill}
			</Text>

			<div>
				<ResultBadge $result={data.result}>{data.result}</ResultBadge>
			</div>

			{data.summary && (
				<Text type="body" size="small" mt="space8">
					{data.summary}
				</Text>
			)}

			{data.evidence && (
				<EvidenceWrapper>
					<EvidenceBox>{data.evidence}</EvidenceBox>
					<CopyButton>
						<IconButton
							Icon={CopyIcon}
							size="small"
							title="Copy evidence"
							onClick={() => {
								if (data.evidence) {
									navigator.clipboard.writeText(data.evidence);
								}
							}}
						/>
					</CopyButton>
				</EvidenceWrapper>
			)}

			{data.markdown_response && (
				<ActionRow>
					<Button
						variant="tertiary"
						size="small"
						LeftIcon={ExpandIcon}
						onClick={() => onOpenAnalysis(data.markdown_response)}
					>
						View full analysis
					</Button>
				</ActionRow>
			)}
		</SkillColumn>
	);
}

interface Props {
	detail: CellDetail;
	checkName?: string;
	checkSeverity?: string;
	onClose: () => void;
}

export function CellDetailPanel({
	detail,
	checkName,
	checkSeverity,
	onClose,
}: Props) {
	const modelEntries = Object.entries(detail.models ?? {});
	const [analysisModal, setAnalysisModal] = useState<AnalysisModalState | null>(
		null,
	);

	return (
		<>
			<Overlay onClick={onClose} />
			<Panel>
				<PanelHeader>
					<HeaderLeft>
						<Text type="code" size="small" weight="bold">
							{detail.check_id}
						</Text>
						{checkName && (
							<Text type="body" size="small" weight="medium">
								{checkName}
							</Text>
						)}
						{checkSeverity && <SeverityBadge severity={checkSeverity} />}
						<Text
							type="body"
							size="small"
							color={theme.color.neutral.textMuted}
						>
							/ {detail.scenario_id}
						</Text>
					</HeaderLeft>
					<Button
						variant="tertiary"
						size="small"
						LeftIcon={CrossIcon}
						onClick={onClose}
					>
						Close
					</Button>
				</PanelHeader>
				<PanelBody>
					{modelEntries.length === 0 && (
						<Text
							type="body"
							size="small"
							color={theme.color.neutral.textMuted}
						>
							No data available
						</Text>
					)}
					{modelEntries.map(([model, data]) => (
						<ModelSection key={model}>
							<ModelHeader>
								<Text type="body" size="small" weight="bold">
									{model}
								</Text>
							</ModelHeader>
							<SkillGrid>
								<SkillResult
									label="Specialist"
									data={data.specialist}
									onOpenAnalysis={(content) =>
										setAnalysisModal({
											model,
											skillLabel: "Specialist",
											content,
										})
									}
								/>
								<SkillResult
									label="MCPC"
									data={data.mcpc}
									onOpenAnalysis={(content) =>
										setAnalysisModal({
											model,
											skillLabel: "MCPC",
											content,
										})
									}
								/>
							</SkillGrid>
						</ModelSection>
					))}
				</PanelBody>
			</Panel>

			{analysisModal && (
				<AnalysisModal
					checkId={detail.check_id}
					checkName={checkName}
					severity={checkSeverity}
					model={analysisModal.model}
					skillLabel={analysisModal.skillLabel}
					content={analysisModal.content}
					onClose={() => setAnalysisModal(null)}
				/>
			)}
		</>
	);
}
