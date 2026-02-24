import { Text, Tooltip, theme } from "@apify/ui-library";
import { Fragment } from "react";
import styled from "styled-components";
import type {
	BPHeatmapData,
	DomainHeatmapData,
	HeatmapCheck,
} from "../api/client";
import { SingleHeatmapCell, SplitHeatmapCell } from "./HeatmapCell";
import { SeverityBadge } from "./SeverityBadge";

// --- Shared widths for sticky columns ---
const CHECK_COL_WIDTH = "7rem";
const NAME_COL_WIDTH = "16rem";

// --- Styled components ---

const TableWrapper = styled.div`
	overflow-x: auto;
	border: 1px solid ${theme.color.neutral.border};
	border-radius: ${theme.radius.radius8};
	background: ${theme.color.neutral.cardBackground};
	max-height: 80vh;
	overflow-y: auto;
`;

const Table = styled.table`
	width: 100%;
	border-collapse: separate;
	border-spacing: 0;
	min-width: 40rem;
`;

// --- Header cells ---

const Th = styled.th<{ $rotated?: boolean; $sticky?: boolean }>`
	padding: ${theme.space.space8};
	text-align: left;
	border-bottom: 1px solid ${theme.color.neutral.border};
	background: ${theme.color.neutral.backgroundMuted};
	white-space: nowrap;
	font-size: 1.2rem;
	font-weight: 600;
	color: ${theme.color.neutral.textMuted};
	position: sticky;
	top: 0;
	z-index: 3;

	${(p) =>
		p.$rotated &&
		`
		writing-mode: vertical-rl;
		text-orientation: mixed;
		transform: rotate(180deg);
		height: 10rem;
		padding: ${theme.space.space4};
		text-align: center;
		max-width: 3.2rem;
	`}
`;

/** First column header: sticky top + left */
const CheckTh = styled(Th)`
	position: sticky;
	left: 0;
	z-index: 4;
	width: ${CHECK_COL_WIDTH};
	min-width: ${CHECK_COL_WIDTH};
`;

/** Second column header: sticky top + left (offset) */
const NameTh = styled(Th)`
	position: sticky;
	left: ${CHECK_COL_WIDTH};
	z-index: 4;
	width: ${NAME_COL_WIDTH};
	min-width: ${NAME_COL_WIDTH};
	border-right: 2px solid ${theme.color.neutral.border};
`;

const ScenarioTh = styled.th`
	padding: ${theme.space.space6} ${theme.space.space4};
	text-align: center;
	border-bottom: 1px solid ${theme.color.neutral.border};
	border-left: 2px solid ${theme.color.neutral.border};
	background: ${theme.color.neutral.backgroundMuted};
	font-size: 1.2rem;
	font-weight: 600;
	color: ${theme.color.neutral.text};
	position: sticky;
	top: 0;
	z-index: 3;
`;

const ModelTh = styled.th`
	padding: ${theme.space.space4};
	text-align: center;
	border-bottom: 2px solid ${theme.color.neutral.border};
	background: ${theme.color.neutral.backgroundMuted};
	font-size: 1.1rem;
	font-weight: 600;
	color: ${theme.color.neutral.textMuted};
	text-transform: lowercase;
	min-width: 6.4rem;
	position: sticky;
	z-index: 3;

	&:first-of-type {
		border-left: 2px solid ${theme.color.neutral.border};
	}
`;

// --- Body cells ---

const Td = styled.td`
	padding: ${theme.space.space4} ${theme.space.space8};
	border-bottom: 1px solid ${theme.color.neutral.separatorSubtle};
	vertical-align: middle;
	background: ${theme.color.neutral.cardBackground};
`;

const ModelTd = styled(Td)`
	border-left: none;
	padding: ${theme.space.space4};

	&:nth-child(3) {
		border-left: 2px solid ${theme.color.neutral.border};
	}
`;

/** Sticky first column (check ID) with severity left border */
const CheckIdCell = styled(Td)<{ $severityColor?: string }>`
	white-space: nowrap;
	font-family: "IBM Plex Mono", monospace;
	font-size: 1.2rem;
	font-weight: 600;
	position: sticky;
	left: 0;
	z-index: 2;
	width: ${CHECK_COL_WIDTH};
	min-width: ${CHECK_COL_WIDTH};
	border-left: 3px solid ${(p) => p.$severityColor ?? "transparent"};
`;

/** Sticky second column (name) */
const NameCell = styled(Td)`
	position: sticky;
	left: ${CHECK_COL_WIDTH};
	z-index: 2;
	width: ${NAME_COL_WIDTH};
	min-width: ${NAME_COL_WIDTH};
	border-right: 2px solid ${theme.color.neutral.border};
`;

const NameContent = styled.div`
	display: flex;
	align-items: center;
	gap: ${theme.space.space4};
`;

const GroupHeaderRow = styled.tr`
	background: ${theme.color.neutral.hover};
`;

const GroupHeaderCell = styled.td`
	padding: ${theme.space.space6} ${theme.space.space8};
	font-size: 1.2rem;
	font-weight: 700;
	color: ${theme.color.neutral.textMuted};
	text-transform: uppercase;
	letter-spacing: 0.05em;
	border-bottom: 2px solid ${theme.color.neutral.border};
	background: ${theme.color.neutral.hover};
	position: sticky;
	left: 0;
`;

// --- Severity color mapping ---

const severityBorderColors: Record<string, string> = {
	CRITICAL: theme.color.danger.border,
	HIGH: theme.color.warning.border,
	MEDIUM: theme.color.neutral.border,
	LOW: theme.color.success.borderSubtle,
};

// --- Helper ---

function groupChecks(
	checks: HeatmapCheck[],
): Array<{ group: string; checks: HeatmapCheck[] }> {
	const grouped: Record<string, HeatmapCheck[]> = {};
	const order: string[] = [];
	for (const c of checks) {
		if (!grouped[c.group]) {
			grouped[c.group] = [];
			order.push(c.group);
		}
		grouped[c.group].push(c);
	}
	return order.map((g) => ({ group: g, checks: grouped[g] }));
}

// --- Domain Heatmap Table (multi-model) ---

interface DomainTableProps {
	data: DomainHeatmapData;
	onCellClick?: (scenarioId: string, checkId: string) => void;
}

export function DomainHeatmapTable({ data, onCellClick }: DomainTableProps) {
	const groups = groupChecks(data.checks);
	const models = data.models ?? [];
	const totalModelCols = data.scenarios.length * Math.max(models.length, 1);

	const scenarioStartCols: Set<number> = new Set();
	const modelsPerScenario = Math.max(models.length, 1);
	for (let i = 0; i < data.scenarios.length; i++) {
		scenarioStartCols.add(i * modelsPerScenario);
	}

	return (
		<TableWrapper>
			<Table>
				<thead>
					<tr>
						<CheckTh rowSpan={models.length > 1 ? 2 : 1}>Check</CheckTh>
						<NameTh rowSpan={models.length > 1 ? 2 : 1}>Name</NameTh>
						{data.scenarios.map((s) => (
							<ScenarioTh key={s.id} colSpan={Math.max(models.length, 1)}>
								{s.name}
							</ScenarioTh>
						))}
					</tr>
					{models.length > 1 && (
						<tr>
							{data.scenarios.map((s) =>
								models.map((m) => <ModelTh key={`${s.id}-${m}`}>{m}</ModelTh>),
							)}
						</tr>
					)}
				</thead>
				<tbody>
					{groups.map((g) => (
						<Fragment key={`group-${g.group}`}>
							<GroupHeaderRow>
								<GroupHeaderCell colSpan={2 + totalModelCols}>
									{g.group}
								</GroupHeaderCell>
							</GroupHeaderRow>
							{g.checks.map((check) => (
								<tr key={check.id}>
									<CheckIdCell
										$severityColor={
											severityBorderColors[check.severity?.toUpperCase()] ??
											"transparent"
										}
									>
										{check.id}
									</CheckIdCell>
									<NameCell>
										<NameContent>
											<Tooltip
												content={`${check.id}: ${check.name} (${check.severity})`}
												delayShow={400}
												size="medium"
											>
												<Text type="body" size="small">
													{check.name}
												</Text>
											</Tooltip>
											<SeverityBadge severity={check.severity} />
										</NameContent>
									</NameCell>
									{data.scenarios.map((s, sIdx) =>
										(models.length > 0 ? models : ["_default"]).map(
											(m, mIdx) => {
												const cell =
													models.length > 0
														? data.matrix[s.id]?.[check.id]?.[m]
														: undefined;
												const isScenarioStart = scenarioStartCols.has(
													sIdx * Math.max(models.length, 1) + mIdx,
												);
												const tdStyle = isScenarioStart
													? {
															borderLeft: `2px solid ${theme.color.neutral.border}`,
														}
													: undefined;

												if (data.is_dev) {
													return (
														<ModelTd key={`${s.id}-${m}`} style={tdStyle}>
															<SingleHeatmapCell
																result={cell?.specialist?.result ?? "na"}
																detail={cell?.specialist?.summary}
																onClick={
																	onCellClick
																		? () => onCellClick(s.id, check.id)
																		: undefined
																}
															/>
														</ModelTd>
													);
												}
												return (
													<ModelTd key={`${s.id}-${m}`} style={tdStyle}>
														<SplitHeatmapCell
															specialist={cell?.specialist ?? null}
															mcpc={cell?.mcpc ?? null}
															onClick={
																onCellClick
																	? () => onCellClick(s.id, check.id)
																	: undefined
															}
														/>
													</ModelTd>
												);
											},
										),
									)}
								</tr>
							))}
						</Fragment>
					))}
				</tbody>
			</Table>
		</TableWrapper>
	);
}

// --- BP Heatmap Table ---

interface BPTableProps {
	data: BPHeatmapData;
}

export function BPHeatmapTable({ data }: BPTableProps) {
	return (
		<TableWrapper>
			<Table>
				<thead>
					<tr>
						<CheckTh>Check</CheckTh>
						<NameTh>Name</NameTh>
						{data.skills.map((skill) => (
							<Th key={skill} $rotated>
								{skill.replace("apify-", "")}
							</Th>
						))}
					</tr>
				</thead>
				<tbody>
					{data.checks.map((check) => (
						<tr key={check.id}>
							<CheckIdCell
								$severityColor={
									severityBorderColors[check.severity?.toUpperCase()] ??
									"transparent"
								}
							>
								{check.id}
							</CheckIdCell>
							<NameCell>
								<NameContent>
									<Text type="body" size="small">
										{check.name}
									</Text>
									<SeverityBadge severity={check.severity} />
								</NameContent>
							</NameCell>
							{data.skills.map((skill) => {
								const cell = data.matrix[check.id]?.[skill];
								return (
									<Td key={skill}>
										<SingleHeatmapCell
											result={cell?.result ?? "na"}
											detail={cell?.detail}
										/>
									</Td>
								);
							})}
						</tr>
					))}
				</tbody>
			</Table>
		</TableWrapper>
	);
}
