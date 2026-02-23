import { Text, theme } from "@apify/ui-library";
import styled from "styled-components";
import type {
	BPHeatmapData,
	DomainHeatmapData,
	HeatmapCheck,
} from "../api/client";
import { SingleHeatmapCell, SplitHeatmapCell } from "./HeatmapCell";

const TableWrapper = styled.div`
	overflow-x: auto;
	border: 1px solid ${theme.color.neutral.border};
	border-radius: ${theme.radius.radius8};
	background: ${theme.color.neutral.cardBackground};
`;

const Table = styled.table`
	width: 100%;
	border-collapse: collapse;
	min-width: 40rem;
`;

const Th = styled.th<{ $rotated?: boolean }>`
	padding: ${theme.space.space8};
	text-align: left;
	border-bottom: 1px solid ${theme.color.neutral.border};
	background: ${theme.color.neutral.backgroundMuted};
	white-space: nowrap;
	font-size: 1.2rem;
	font-weight: 600;
	color: ${theme.color.neutral.textMuted};

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

const Td = styled.td`
	padding: ${theme.space.space4} ${theme.space.space8};
	border-bottom: 1px solid ${theme.color.neutral.separatorSubtle};
	vertical-align: middle;
`;

const CheckIdCell = styled(Td)`
	white-space: nowrap;
	font-family: "IBM Plex Mono", monospace;
	font-size: 1.2rem;
	font-weight: 600;
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
`;

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

// --- Domain Heatmap Table ---

interface DomainTableProps {
	data: DomainHeatmapData;
	onCellClick?: (scenarioId: string, checkId: string) => void;
}

export function DomainHeatmapTable({ data, onCellClick }: DomainTableProps) {
	const groups = groupChecks(data.checks);

	return (
		<TableWrapper>
			<Table>
				<thead>
					<tr>
						<Th>Check</Th>
						<Th>Name</Th>
						{data.scenarios.map((s) => (
							<Th key={s.id} $rotated>
								{s.name}
							</Th>
						))}
					</tr>
				</thead>
				<tbody>
					{groups.map((g) => (
						<>
							<GroupHeaderRow key={`group-${g.group}`}>
								<GroupHeaderCell colSpan={2 + data.scenarios.length}>
									{g.group}
								</GroupHeaderCell>
							</GroupHeaderRow>
							{g.checks.map((check) => (
								<tr key={check.id}>
									<CheckIdCell>{check.id}</CheckIdCell>
									<Td>
										<Text type="body" size="small">
											{check.name}
										</Text>
									</Td>
									{data.scenarios.map((s) => {
										const cell = data.matrix[s.id]?.[check.id];
										if (data.is_dev) {
											return (
												<Td key={s.id}>
													<SingleHeatmapCell
														result={cell?.specialist?.result ?? "na"}
														detail={cell?.specialist?.summary}
														onClick={
															onCellClick
																? () => onCellClick(s.id, check.id)
																: undefined
														}
													/>
												</Td>
											);
										}
										return (
											<Td key={s.id}>
												<SplitHeatmapCell
													specialist={cell?.specialist ?? null}
													mcpc={cell?.mcpc ?? null}
													onClick={
														onCellClick
															? () => onCellClick(s.id, check.id)
															: undefined
													}
												/>
											</Td>
										);
									})}
								</tr>
							))}
						</>
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
						<Th>Check</Th>
						<Th>Name</Th>
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
							<CheckIdCell>{check.id}</CheckIdCell>
							<Td>
								<Text type="body" size="small">
									{check.name}
								</Text>
							</Td>
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
