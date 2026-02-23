import { PlayIcon } from "@apify/ui-icons";
import { Button, Heading, Text, theme } from "@apify/ui-library";
import { useQuery } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import styled from "styled-components";
import { api } from "../api/client";
import { RunProgress } from "../components/RunProgress";
import { useSSE } from "../hooks/useSSE";

const AVAILABLE_MODELS = ["sonnet", "opus", "haiku"];

const PageTitle = styled(Heading)`
	margin-bottom: ${theme.space.space24};
`;

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
	margin-bottom: ${theme.space.space8};

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

const RangeWrapper = styled.div`
	display: flex;
	flex-direction: column;
	gap: ${theme.space.space8};
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

const ScenarioSection = styled(Card)`
	margin-bottom: ${theme.space.space24};
`;

const ScenarioHeader = styled.div`
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: ${theme.space.space12};
`;

const ScenarioHeaderLeft = styled.div`
	display: flex;
	align-items: center;
	gap: ${theme.space.space12};
`;

const ScenarioHeaderRight = styled.div`
	display: flex;
	gap: ${theme.space.space8};
`;

const SelectWrapper = styled.div`
	display: inline-flex;
`;

const NativeSelect = styled.select<{ $disabled?: boolean }>`
	font-size: 1.2rem;
	padding: ${theme.space.space4} ${theme.space.space8};
	border-radius: ${theme.radius.radius4};
	border: 1px solid ${theme.color.neutral.fieldBorder};
	background: ${theme.color.neutral.fieldBackground};
	color: ${theme.color.neutral.text};
	cursor: ${({ $disabled }) => ($disabled ? "not-allowed" : "pointer")};
	opacity: ${({ $disabled }) => ($disabled ? "0.5" : "1")};

	&:focus {
		outline: none;
		border-color: ${theme.color.primary.fieldBorderActive};
		box-shadow: ${theme.shadow.shadowActive};
	}
`;

const FilterButton = styled.button<{ $disabled?: boolean }>`
	background: none;
	border: 1px solid ${theme.color.neutral.border};
	border-radius: ${theme.radius.radius4};
	padding: ${theme.space.space4} ${theme.space.space8};
	font-size: 1.2rem;
	color: ${theme.color.neutral.text};
	cursor: ${({ $disabled }) => ($disabled ? "not-allowed" : "pointer")};
	opacity: ${({ $disabled }) => ($disabled ? "0.5" : "1")};
	transition: background ${theme.transition.fastEaseInOut};

	&:hover:not(:disabled) {
		background: ${theme.color.neutral.hover};
	}
`;

const ScenarioGrid = styled.div`
	display: grid;
	grid-template-columns: repeat(2, 1fr);
	gap: ${theme.space.space4};

	@media ${theme.device.tablet} {
		grid-template-columns: repeat(3, 1fr);
	}

	@media ${theme.device.desktop} {
		grid-template-columns: repeat(4, 1fr);
	}
`;

const ScenarioCheckLabel = styled.label<{ $disabled?: boolean }>`
	display: flex;
	align-items: center;
	gap: ${theme.space.space8};
	padding: ${theme.space.space4};
	border-radius: ${theme.radius.radius4};
	font-size: 1.2rem;
	cursor: ${({ $disabled }) => ($disabled ? "not-allowed" : "pointer")};
	transition: background ${theme.transition.fastEaseInOut};
	color: ${({ $disabled }) =>
		$disabled ? theme.color.neutral.textDisabled : theme.color.neutral.text};

	&:hover {
		background: ${({ $disabled }) =>
			$disabled ? "transparent" : theme.color.neutral.hover};
	}
`;

const ScenarioId = styled.span`
	font-family: "IBM Plex Mono", monospace;
	font-size: 1.1rem;
	color: ${theme.color.neutral.text};
	white-space: nowrap;
`;

const ScenarioName = styled.span`
	color: ${theme.color.neutral.textMuted};
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
`;

const ProgressSection = styled(Card)`
	margin-bottom: ${theme.space.space24};
`;

const ProgressHeader = styled.div`
	display: flex;
	align-items: baseline;
	gap: ${theme.space.space8};
	margin-bottom: ${theme.space.space12};
`;

const RunIdText = styled(Text)`
	color: ${theme.color.neutral.textMuted};
	font-family: "IBM Plex Mono", monospace;
`;

const CompletedBanner = styled.div`
	margin-top: ${theme.space.space16};
	padding: ${theme.space.space12} ${theme.space.space16};
	background: ${theme.color.success.backgroundSubtle};
	border: 1px solid ${theme.color.success.borderSubtle};
	border-radius: ${theme.radius.radius8};
	display: flex;
	align-items: center;
	gap: ${theme.space.space12};
`;

const CompletedText = styled(Text)`
	color: ${theme.color.success.text};
	font-weight: 500;
`;

const ViewReportLink = styled(Link)`
	font-size: 1.3rem;
	color: ${theme.color.primary.text};
	text-decoration: none;

	&:hover {
		text-decoration: underline;
	}
`;

export function Run() {
	const [searchParams] = useSearchParams();
	const preSelectedScenario = searchParams.get("scenario");
	const preSelectedModel = searchParams.get("model");

	const { data: scenarios } = useQuery({
		queryKey: ["scenarios"],
		queryFn: api.getScenarios,
	});

	const [selectedScenarios, setSelectedScenarios] = useState<string[]>([]);
	const [selectedModels, setSelectedModels] = useState<string[]>(
		preSelectedModel ? [preSelectedModel] : [...AVAILABLE_MODELS],
	);
	const [skillFilter, setSkillFilter] = useState<string>("");
	const [concurrency, setConcurrency] = useState(3);
	const [runId, setRunId] = useState<string | null>(null);
	const [starting, setStarting] = useState(false);
	const [completedReport, setCompletedReport] = useState<string | null>(null);

	const { events, isConnected, connect } = useSSE();

	// Unique skills for filter dropdown
	const uniqueSkills = useMemo(() => {
		if (!scenarios) return [];
		return [...new Set(scenarios.map((s) => s.target_skill))].sort();
	}, [scenarios]);

	// Scenarios filtered by skill
	const filteredScenarios = useMemo(() => {
		if (!scenarios) return [];
		if (!skillFilter) return scenarios;
		return scenarios.filter((s) => s.target_skill === skillFilter);
	}, [scenarios, skillFilter]);

	// Pre-select scenario from URL
	useEffect(() => {
		if (preSelectedScenario && scenarios) {
			setSelectedScenarios([preSelectedScenario]);
		}
	}, [preSelectedScenario, scenarios]);

	// Build progress grid from SSE events
	const progress = useMemo(() => {
		const grid: Record<string, Record<string, string>> = {};
		for (const ev of events) {
			if (ev.event === "progress") {
				const sid = ev.data.scenario_id as string;
				const model = ev.data.model as string;
				const status = ev.data.status as string;
				if (!grid[sid]) grid[sid] = {};
				grid[sid][model] = status;
			}
			if (ev.event === "completed") {
				setCompletedReport(ev.data.report_md as string);
			}
		}
		return grid;
	}, [events]);

	const handleStart = useCallback(async () => {
		setStarting(true);
		setCompletedReport(null);
		try {
			const res = await api.startRun({
				scenario_ids:
					selectedScenarios.length > 0 ? selectedScenarios : undefined,
				models: selectedModels,
				concurrency,
			});
			setRunId(res.run_id);
			connect(res.run_id);
		} catch (e) {
			alert(String(e));
		} finally {
			setStarting(false);
		}
	}, [selectedScenarios, selectedModels, concurrency, connect]);

	const toggleModel = (m: string) => {
		setSelectedModels((prev) =>
			prev.includes(m) ? prev.filter((x) => x !== m) : [...prev, m],
		);
	};

	const toggleScenario = (id: string) => {
		setSelectedScenarios((prev) =>
			prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
		);
	};

	const handleSkillFilter = (skill: string) => {
		setSkillFilter(skill);
		// When changing filter, select all visible scenarios from that skill
		if (skill && scenarios) {
			const ids = scenarios
				.filter((s) => s.target_skill === skill)
				.map((s) => s.id);
			setSelectedScenarios(ids);
		} else {
			setSelectedScenarios([]);
		}
	};

	const scenarioIds =
		selectedScenarios.length > 0
			? selectedScenarios
			: scenarios?.map((s) => s.id) || [];

	const isRunning = isConnected || starting;
	const callCount =
		(selectedScenarios.length || scenarios?.length || 0) *
		selectedModels.length;

	return (
		<div>
			<PageTitle type="titleL" as="h1">
				Run Scenarios
			</PageTitle>

			<ControlsGrid>
				{/* Models card */}
				<Card>
					<CardTitle type="titleS" as="h3">
						Models
					</CardTitle>
					{AVAILABLE_MODELS.map((m) => (
						<CheckboxLabel key={m} $disabled={isRunning}>
							<NativeCheckbox
								type="checkbox"
								checked={selectedModels.includes(m)}
								onChange={() => toggleModel(m)}
								disabled={isRunning}
							/>
							{m}
						</CheckboxLabel>
					))}
				</Card>

				{/* Concurrency card */}
				<Card>
					<CardTitle type="titleS" as="h3">
						Concurrency
					</CardTitle>
					<RangeWrapper>
						<NativeRange
							type="range"
							min={1}
							max={10}
							value={concurrency}
							onChange={(e) => setConcurrency(Number(e.target.value))}
							disabled={isRunning}
						/>
						<RangeValue type="body" size="small">
							{concurrency}
						</RangeValue>
					</RangeWrapper>
				</Card>

				{/* Run card */}
				<Card>
					<RunCardInner>
						<div>
							<CardTitle type="titleS" as="h3">
								Run
							</CardTitle>
							<RunSummary type="body" size="small">
								{selectedScenarios.length || scenarios?.length || 0} scenarios
								&times; {selectedModels.length} models = {callCount} calls
							</RunSummary>
						</div>
						<Button
							size="large"
							LeftIcon={PlayIcon}
							onClick={handleStart}
							disabled={isRunning || selectedModels.length === 0}
						>
							{isRunning ? "Running..." : "Start Run"}
						</Button>
					</RunCardInner>
				</Card>
			</ControlsGrid>

			{/* Scenario selection */}
			{scenarios && (
				<ScenarioSection>
					<ScenarioHeader>
						<ScenarioHeaderLeft>
							<CardTitle type="titleS" as="h3">
								Scenarios
							</CardTitle>
							<SelectWrapper>
								<NativeSelect
									value={skillFilter}
									onChange={(e) => handleSkillFilter(e.target.value)}
									disabled={isRunning}
									$disabled={isRunning}
								>
									<option value="">All skills</option>
									{uniqueSkills.map((skill) => (
										<option key={skill} value={skill}>
											{skill} (
											{scenarios.filter((s) => s.target_skill === skill).length}
											)
										</option>
									))}
								</NativeSelect>
							</SelectWrapper>
						</ScenarioHeaderLeft>
						<ScenarioHeaderRight>
							<FilterButton
								onClick={() => {
									setSkillFilter("");
									setSelectedScenarios([]);
								}}
								disabled={isRunning}
								$disabled={isRunning}
							>
								All
							</FilterButton>
							<FilterButton
								onClick={() =>
									setSelectedScenarios(filteredScenarios.map((s) => s.id))
								}
								disabled={isRunning}
								$disabled={isRunning}
							>
								Select All
							</FilterButton>
						</ScenarioHeaderRight>
					</ScenarioHeader>
					<ScenarioGrid>
						{filteredScenarios.map((s) => (
							<ScenarioCheckLabel key={s.id} $disabled={isRunning}>
								<NativeCheckbox
									type="checkbox"
									checked={
										selectedScenarios.length === 0 ||
										selectedScenarios.includes(s.id)
									}
									onChange={() => toggleScenario(s.id)}
									disabled={isRunning}
								/>
								<ScenarioId>{s.id}</ScenarioId>
								<ScenarioName>{s.name}</ScenarioName>
							</ScenarioCheckLabel>
						))}
					</ScenarioGrid>
				</ScenarioSection>
			)}

			{/* Progress */}
			{runId && (
				<ProgressSection>
					<ProgressHeader>
						<Heading type="titleS" as="h3">
							Progress
						</Heading>
						<RunIdText type="body" size="small">
							Run: {runId}
						</RunIdText>
					</ProgressHeader>
					<RunProgress
						scenarioIds={scenarioIds}
						models={selectedModels}
						progress={progress}
						isRunning={isRunning}
					/>
					{completedReport && (
						<CompletedBanner>
							<CompletedText type="body">Run completed!</CompletedText>
							<ViewReportLink to={`/reports/${completedReport}`}>
								View Report
							</ViewReportLink>
						</CompletedBanner>
					)}
				</ProgressSection>
			)}
		</div>
	);
}
