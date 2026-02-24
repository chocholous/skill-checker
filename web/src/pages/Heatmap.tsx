import { Button, Heading, Text, theme } from "@apify/ui-library";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import styled from "styled-components";
import type { CellDetail } from "../api/client";
import { api } from "../api/client";
import { CellDetailPanel } from "../components/CellDetailPanel";
import { HeatmapLegend } from "../components/HeatmapLegend";
import { BPHeatmapTable, DomainHeatmapTable } from "../components/HeatmapTable";
import { SkillFilterPanel } from "../components/SkillFilterPanel";
import { useScoredSSE } from "../hooks/useScoredSSE";

const AVAILABLE_MODELS = ["sonnet", "opus", "haiku"];

// --- Styled components ---

const PageHeader = styled.div`
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: ${theme.space.space16};
`;

const TabBar = styled.div`
	display: flex;
	gap: ${theme.space.space4};
	margin-bottom: ${theme.space.space16};
	border-bottom: 1px solid ${theme.color.neutral.border};
	padding-bottom: ${theme.space.space4};
	overflow-x: auto;
`;

const Tab = styled.button<{ $active: boolean }>`
	padding: ${theme.space.space6} ${theme.space.space12};
	border: none;
	border-radius: ${theme.radius.radius6} ${theme.radius.radius6} 0 0;
	background: ${(p) =>
		p.$active
			? theme.color.primary.backgroundSubtle
			: theme.color.neutral.backgroundMuted};
	color: ${(p) =>
		p.$active ? theme.color.primary.text : theme.color.neutral.textMuted};
	font-size: 1.3rem;
	font-weight: ${(p) => (p.$active ? "600" : "500")};
	cursor: pointer;
	white-space: nowrap;
	transition: background ${theme.transition.fastEaseInOut};

	&:hover {
		background: ${(p) =>
			p.$active
				? theme.color.primary.backgroundSubtle
				: theme.color.neutral.hover};
	}
`;

const EmptyState = styled.div`
	text-align: center;
	padding: ${theme.space.space32};
	background: ${theme.color.neutral.cardBackground};
	border-radius: ${theme.radius.radius8};
	box-shadow: ${theme.shadow.shadow1};
`;

const ProgressSection = styled.div`
	padding: ${theme.space.space16};
	background: ${theme.color.neutral.cardBackground};
	border-radius: ${theme.radius.radius8};
	box-shadow: ${theme.shadow.shadow1};
	margin-bottom: ${theme.space.space16};
`;

const ProgressBar = styled.div`
	width: 100%;
	height: 0.8rem;
	border-radius: ${theme.radius.radius4};
	background: ${theme.color.neutral.backgroundMuted};
	overflow: hidden;
	margin-top: ${theme.space.space8};
`;

const ProgressFill = styled.div<{ $pct: number }>`
	height: 100%;
	width: ${(p) => p.$pct}%;
	background: ${theme.color.primary.background};
	transition: width 0.3s ease;
`;

const DomainSummary = styled.div`
	display: flex;
	gap: ${theme.space.space16};
	margin-top: ${theme.space.space16};
	padding: ${theme.space.space12};
	background: ${theme.color.neutral.backgroundMuted};
	border-radius: ${theme.radius.radius6};
`;

const SummaryItem = styled.div`
	display: flex;
	align-items: center;
	gap: ${theme.space.space4};
`;

const SummaryDot = styled.div<{ $color: string }>`
	width: 1rem;
	height: 1rem;
	border-radius: 50%;
	background: ${(p) => p.$color};
`;

// --- Run controls styled components ---

const ControlsGrid = styled.div`
	display: grid;
	grid-template-columns: 1fr;
	gap: ${theme.space.space16};
	margin-bottom: ${theme.space.space24};

	@media ${theme.device.tablet} {
		grid-template-columns: repeat(3, 1fr);
	}
`;

const Card = styled.div`
	background: ${theme.color.neutral.cardBackground};
	border: 1px solid ${theme.color.neutral.border};
	border-radius: ${theme.radius.radius8};
	box-shadow: ${theme.shadow.shadow1};
	padding: ${theme.space.space16};
`;

const CardTitle = styled(Heading)`
	margin-bottom: ${theme.space.space12};
`;

const CheckboxLabel = styled.label<{ $disabled?: boolean }>`
	display: flex;
	align-items: center;
	gap: ${theme.space.space8};
	font-size: 1.4rem;
	color: ${({ $disabled }) =>
		$disabled ? theme.color.neutral.textDisabled : theme.color.neutral.text};
	cursor: ${({ $disabled }) => ($disabled ? "not-allowed" : "pointer")};
	margin-bottom: ${theme.space.space4};

	&:last-child {
		margin-bottom: 0;
	}
`;

const NativeCheckbox = styled.input`
	width: 1.6rem;
	height: 1.6rem;
	cursor: inherit;
	accent-color: ${theme.color.primary.action};
	flex-shrink: 0;
`;

const DomainList = styled.div`
	max-height: 24rem;
	overflow-y: auto;
`;

const SelectAllRow = styled.div`
	display: flex;
	gap: ${theme.space.space8};
	margin-bottom: ${theme.space.space8};
	padding-bottom: ${theme.space.space8};
	border-bottom: 1px solid ${theme.color.neutral.border};
`;

const ToggleButton = styled.button<{ $disabled?: boolean }>`
	background: none;
	border: 1px solid ${theme.color.neutral.border};
	border-radius: ${theme.radius.radius4};
	padding: ${theme.space.space2} ${theme.space.space8};
	font-size: 1.2rem;
	color: ${theme.color.neutral.text};
	cursor: ${({ $disabled }) => ($disabled ? "not-allowed" : "pointer")};
	opacity: ${({ $disabled }) => ($disabled ? "0.5" : "1")};
	transition: background ${theme.transition.fastEaseInOut};

	&:hover:not(:disabled) {
		background: ${theme.color.neutral.hover};
	}
`;

const NativeSelect = styled.select<{ $disabled?: boolean }>`
	font-size: 1.4rem;
	padding: ${theme.space.space6} ${theme.space.space8};
	border-radius: ${theme.radius.radius4};
	border: 1px solid ${theme.color.neutral.fieldBorder};
	background: ${theme.color.neutral.fieldBackground};
	color: ${theme.color.neutral.text};
	cursor: ${({ $disabled }) => ($disabled ? "not-allowed" : "pointer")};
	opacity: ${({ $disabled }) => ($disabled ? "0.5" : "1")};
	width: 100%;

	&:focus {
		outline: none;
		border-color: ${theme.color.primary.fieldBorderActive};
		box-shadow: ${theme.shadow.shadowActive};
	}
`;

const RangeWrapper = styled.div`
	display: flex;
	flex-direction: column;
	gap: ${theme.space.space8};
	margin-top: ${theme.space.space16};
`;

const NativeRange = styled.input`
	width: 100%;
	accent-color: ${theme.color.primary.action};
	cursor: pointer;

	&:disabled {
		cursor: not-allowed;
		opacity: 0.5;
	}
`;

const RangeValue = styled(Text)`
	text-align: center;
	color: ${theme.color.neutral.textMuted};
`;

const RunCardInner = styled.div`
	display: flex;
	flex-direction: column;
	justify-content: space-between;
	height: 100%;
`;

const RunSummary = styled(Text)`
	color: ${theme.color.neutral.textMuted};
	margin-bottom: ${theme.space.space12};
`;

// --- Page component ---

export function Heatmap() {
	const { domain: urlDomain } = useParams<{ domain?: string }>();
	const navigate = useNavigate();
	const queryClient = useQueryClient();

	// BP toggle
	const [bpForDomain, setBpForDomain] = useState<string | null>(null);
	const showBP = bpForDomain !== null && bpForDomain === (urlDomain ?? null);
	const [cellDetail, setCellDetail] = useState<CellDetail | null>(null);
	const [cellCheckMeta, setCellCheckMeta] = useState<{
		name?: string;
		severity?: string;
	}>({});

	// Skill filter: which domain IDs to show in tabs
	const [selectedSkills, setSelectedSkills] = useState<string[] | null>(null);

	// Run controls state
	const [selectedDomains, setSelectedDomains] = useState<string[] | null>(null);
	const [selectedModel, setSelectedModel] = useState("sonnet");
	const [concurrency, setConcurrency] = useState(3);

	const { events, isConnected, connect } = useScoredSSE();

	// Queries
	const domains = useQuery({
		queryKey: ["heatmap-domains"],
		queryFn: api.getHeatmapDomains,
	});

	const skills = useQuery({
		queryKey: ["heatmap-skills"],
		queryFn: api.getHeatmapSkills,
	});

	const domainData = useQuery({
		queryKey: ["heatmap-domain", urlDomain],
		queryFn: () => api.getHeatmapDomain(urlDomain!),
		enabled: !!urlDomain,
	});

	const bpData = useQuery({
		queryKey: ["heatmap-bp"],
		queryFn: api.getHeatmapBP,
		enabled: showBP,
	});

	// Resolved lists
	const allDomainIds = useMemo(
		() => domains.data?.map((d) => d.id) ?? [],
		[domains.data],
	);
	const effectiveDomains = selectedDomains ?? allDomainIds;

	const allSkillDomains = useMemo(
		() => skills.data?.map((h) => h.domain).filter(Boolean) ?? [],
		[skills.data],
	);
	const effectiveSkills = selectedSkills ?? allSkillDomains;

	// Auto-navigate to first selected skill if no domain in URL
	useEffect(() => {
		if (skills.data && skills.data.length > 0 && !urlDomain) {
			const first = effectiveSkills[0];
			if (first) {
				navigate(`/heatmap/${first}`, { replace: true });
			}
		}
	}, [skills.data, urlDomain, effectiveSkills, navigate]);

	// SSE progress tracking
	const progressInfo = useMemo(() => {
		const started = events.find((e) => e.event === "started");
		const total = (started?.data?.total as number) ?? 0;
		const completed = events.filter(
			(e) => e.event === "progress" && e.data?.status !== "running",
		).length;
		const isDone = events.some(
			(e) => e.event === "completed" || e.event === "error",
		);
		return { total, completed, isDone };
	}, [events]);

	// When SSE completes, invalidate cached queries
	useEffect(() => {
		if (progressInfo.isDone) {
			queryClient.invalidateQueries({ queryKey: ["heatmap-skills"] });
			queryClient.invalidateQueries({ queryKey: ["heatmap-domain"] });
		}
	}, [progressInfo.isDone, queryClient]);

	// Handlers
	const handleRunScored = useCallback(async () => {
		const result = await api.startScoredRun({
			domains: selectedDomains !== null ? selectedDomains : undefined,
			model: selectedModel,
			concurrency,
		});
		connect(result.run_id);
	}, [connect, selectedDomains, selectedModel, concurrency]);

	const handleCellClick = useCallback(
		async (scenarioId: string, checkId: string) => {
			// Find check metadata from current domain data
			const check = domainData.data?.checks.find((c) => c.id === checkId);
			setCellCheckMeta({
				name: check?.name,
				severity: check?.severity,
			});
			const detail = await api.getHeatmapDetail(scenarioId, checkId);
			setCellDetail(detail);
		},
		[domainData.data?.checks],
	);

	const toggleDomain = (id: string) => {
		const current = effectiveDomains;
		setSelectedDomains(
			current.includes(id) ? current.filter((x) => x !== id) : [...current, id],
		);
	};

	const toggleSkillFilter = (domainId: string) => {
		const current = effectiveSkills;
		setSelectedSkills(
			current.includes(domainId)
				? current.filter((x) => x !== domainId)
				: [...current, domainId],
		);
	};

	const hasData = skills.data && skills.data.length > 0;

	// Tabs: only show filtered skills
	const domainTabs = useMemo(() => {
		if (!domains.data) return [];
		return domains.data
			.filter((d) => effectiveSkills.includes(d.id))
			.map((d) => ({
				id: d.id,
				label: d.id.replace(/-/g, " "),
			}));
	}, [domains.data, effectiveSkills]);

	const estimatedTasks = useMemo(() => {
		if (!domains.data) return 0;
		return domains.data
			.filter((d) => effectiveDomains.includes(d.id))
			.reduce((sum, d) => sum + d.scenario_count, 0);
	}, [domains.data, effectiveDomains]);

	// Compute domain summary stats (with model dimension)
	const domainSummary = useMemo(() => {
		if (!domainData.data) return null;
		const data = domainData.data;
		let pass = 0;
		let fail = 0;
		let unclear = 0;
		let na = 0;
		for (const scenarioChecks of Object.values(data.matrix)) {
			for (const modelCells of Object.values(scenarioChecks)) {
				for (const cell of Object.values(modelCells)) {
					for (const side of [cell.specialist, cell.mcpc]) {
						if (!side) continue;
						switch (side.result) {
							case "pass":
								pass++;
								break;
							case "fail":
								fail++;
								break;
							case "unclear":
								unclear++;
								break;
							default:
								na++;
						}
					}
				}
			}
		}
		return { pass, fail, unclear, na };
	}, [domainData.data]);

	return (
		<div>
			{/* Header */}
			<PageHeader>
				<Heading type="titleL" as="h1">
					Skill Heatmap
				</Heading>
			</PageHeader>

			{/* Run controls panel */}
			<ControlsGrid>
				{/* Card 1: Domain checkboxes */}
				<Card>
					<CardTitle type="titleS" as="h3">
						Domains
					</CardTitle>
					<SelectAllRow>
						<ToggleButton
							$disabled={isConnected}
							disabled={isConnected}
							onClick={() => setSelectedDomains(null)}
						>
							All
						</ToggleButton>
						<ToggleButton
							$disabled={isConnected}
							disabled={isConnected}
							onClick={() => setSelectedDomains([])}
						>
							None
						</ToggleButton>
					</SelectAllRow>
					<DomainList>
						{domains.data?.map((d) => (
							<CheckboxLabel key={d.id} $disabled={isConnected}>
								<NativeCheckbox
									type="checkbox"
									checked={effectiveDomains.includes(d.id)}
									onChange={() => toggleDomain(d.id)}
									disabled={isConnected}
								/>
								{d.id.replace(/-/g, " ")} ({d.scenario_count})
							</CheckboxLabel>
						))}
					</DomainList>
				</Card>

				{/* Card 2: Model + Concurrency */}
				<Card>
					<CardTitle type="titleS" as="h3">
						Model
					</CardTitle>
					<NativeSelect
						value={selectedModel}
						onChange={(e) => setSelectedModel(e.target.value)}
						disabled={isConnected}
						$disabled={isConnected}
					>
						{AVAILABLE_MODELS.map((m) => (
							<option key={m} value={m}>
								{m}
							</option>
						))}
					</NativeSelect>
					<RangeWrapper>
						<CardTitle type="titleS" as="h3">
							Concurrency
						</CardTitle>
						<NativeRange
							type="range"
							min={1}
							max={10}
							value={concurrency}
							onChange={(e) => setConcurrency(Number(e.target.value))}
							disabled={isConnected}
						/>
						<RangeValue type="body" size="small">
							{concurrency}
						</RangeValue>
					</RangeWrapper>
				</Card>

				{/* Card 3: Summary + Run button */}
				<Card>
					<RunCardInner>
						<div>
							<CardTitle type="titleS" as="h3">
								Run
							</CardTitle>
							<RunSummary type="body" size="small">
								{effectiveDomains.length} domains &times; ~{estimatedTasks}{" "}
								scenarios (model: {selectedModel})
							</RunSummary>
						</div>
						<Button
							size="large"
							variant="primary"
							onClick={handleRunScored}
							disabled={isConnected || effectiveDomains.length === 0}
						>
							{isConnected ? "Running..." : "Run Scored Analysis"}
						</Button>
					</RunCardInner>
				</Card>
			</ControlsGrid>

			{/* Run progress */}
			{isConnected && (
				<ProgressSection>
					<Text type="body" size="small" weight="bold">
						Scored run in progress...
					</Text>
					<Text type="body" size="small" color={theme.color.neutral.textMuted}>
						{progressInfo.completed} / {progressInfo.total || "?"} completed
					</Text>
					<ProgressBar>
						<ProgressFill
							$pct={
								progressInfo.total
									? (progressInfo.completed / progressInfo.total) * 100
									: 0
							}
						/>
					</ProgressBar>
				</ProgressSection>
			)}

			{/* Empty state */}
			{!hasData && !isConnected && (
				<EmptyState>
					<Heading type="titleS" mb="space8">
						No scored data yet
					</Heading>
					<Text
						type="body"
						size="regular"
						color={theme.color.neutral.textMuted}
						mb="space16"
					>
						Run a scored analysis to populate the heatmap with pass/fail results
						per check.
					</Text>
				</EmptyState>
			)}

			{/* Skill filter + domain tabs + table */}
			{hasData && (
				<>
					<SkillFilterPanel
						skills={skills.data!}
						selectedDomains={effectiveSkills}
						onToggle={toggleSkillFilter}
						onSelectAll={() => setSelectedSkills(null)}
						onSelectNone={() => setSelectedSkills([])}
					/>

					<HeatmapLegend />

					<TabBar>
						{domainTabs.map((tab) => (
							<Tab
								key={tab.id}
								$active={!showBP && urlDomain === tab.id}
								onClick={() => {
									setBpForDomain(null);
									navigate(`/heatmap/${tab.id}`);
								}}
							>
								{tab.label}
							</Tab>
						))}
						<Tab
							$active={showBP}
							onClick={() => setBpForDomain(urlDomain ?? null)}
						>
							BP (Static)
						</Tab>
					</TabBar>

					{showBP ? (
						bpData.data ? (
							<BPHeatmapTable data={bpData.data} />
						) : (
							<Text
								type="body"
								size="small"
								color={theme.color.neutral.textMuted}
							>
								Loading BP data...
							</Text>
						)
					) : urlDomain && domainData.data ? (
						<>
							<DomainHeatmapTable
								data={domainData.data}
								onCellClick={handleCellClick}
							/>
							{domainSummary && (
								<DomainSummary>
									<SummaryItem>
										<SummaryDot $color={theme.color.success.backgroundSubtle} />
										<Text type="body" size="small">
											Pass: {domainSummary.pass}
										</Text>
									</SummaryItem>
									<SummaryItem>
										<SummaryDot $color={theme.color.danger.backgroundSubtle} />
										<Text type="body" size="small">
											Fail: {domainSummary.fail}
										</Text>
									</SummaryItem>
									<SummaryItem>
										<SummaryDot $color={theme.color.warning.backgroundSubtle} />
										<Text type="body" size="small">
											Unclear: {domainSummary.unclear}
										</Text>
									</SummaryItem>
									<SummaryItem>
										<SummaryDot $color={theme.color.neutral.backgroundMuted} />
										<Text type="body" size="small">
											N/A: {domainSummary.na}
										</Text>
									</SummaryItem>
								</DomainSummary>
							)}
						</>
					) : urlDomain ? (
						<Text
							type="body"
							size="small"
							color={theme.color.neutral.textMuted}
						>
							Loading domain data...
						</Text>
					) : null}
				</>
			)}

			{/* Detail panel */}
			{cellDetail && (
				<CellDetailPanel
					detail={cellDetail}
					checkName={cellCheckMeta.name}
					checkSeverity={cellCheckMeta.severity}
					onClose={() => setCellDetail(null)}
				/>
			)}
		</div>
	);
}
