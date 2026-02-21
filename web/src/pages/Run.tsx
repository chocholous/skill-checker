import { useQuery } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { RunProgress } from "../components/RunProgress";
import { useSSE } from "../hooks/useSSE";

const AVAILABLE_MODELS = ["sonnet", "opus", "haiku"];

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

	return (
		<div>
			<h1 className="text-2xl font-bold mb-6">Run Scenarios</h1>

			<div className="grid md:grid-cols-3 gap-6 mb-6">
				{/* Models */}
				<div className="bg-white rounded-lg border shadow-sm p-4">
					<h3 className="font-semibold mb-3">Models</h3>
					<div className="flex flex-col gap-2">
						{AVAILABLE_MODELS.map((m) => (
							<label key={m} className="flex items-center gap-2 text-sm">
								<input
									type="checkbox"
									checked={selectedModels.includes(m)}
									onChange={() => toggleModel(m)}
									disabled={isRunning}
									className="rounded"
								/>
								{m}
							</label>
						))}
					</div>
				</div>

				{/* Concurrency */}
				<div className="bg-white rounded-lg border shadow-sm p-4">
					<h3 className="font-semibold mb-3">Concurrency</h3>
					<input
						type="range"
						min={1}
						max={10}
						value={concurrency}
						onChange={(e) => setConcurrency(Number(e.target.value))}
						disabled={isRunning}
						className="w-full"
					/>
					<div className="text-center text-sm text-gray-600 mt-1">
						{concurrency}
					</div>
				</div>

				{/* Actions */}
				<div className="bg-white rounded-lg border shadow-sm p-4 flex flex-col justify-between">
					<div>
						<h3 className="font-semibold mb-1">Run</h3>
						<p className="text-xs text-gray-500 mb-3">
							{selectedScenarios.length || scenarios?.length || 0} scenarios x{" "}
							{selectedModels.length} models ={" "}
							{(selectedScenarios.length || scenarios?.length || 0) *
								selectedModels.length}{" "}
							calls
						</p>
					</div>
					<button
						onClick={handleStart}
						disabled={isRunning || selectedModels.length === 0}
						className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-40 font-medium"
					>
						{isRunning ? "Running..." : "Start Run"}
					</button>
				</div>
			</div>

			{/* Scenario selection */}
			{scenarios && (
				<div className="bg-white rounded-lg border shadow-sm p-4 mb-6">
					<div className="flex items-center justify-between mb-3">
						<div className="flex items-center gap-3">
							<h3 className="font-semibold">Scenarios</h3>
							<select
								value={skillFilter}
								onChange={(e) => handleSkillFilter(e.target.value)}
								disabled={isRunning}
								className="text-xs px-2 py-1 rounded border bg-white"
							>
								<option value="">All skills</option>
								{uniqueSkills.map((skill) => (
									<option key={skill} value={skill}>
										{skill} (
										{scenarios.filter((s) => s.target_skill === skill).length})
									</option>
								))}
							</select>
						</div>
						<div className="flex gap-2">
							<button
								onClick={() => {
									setSkillFilter("");
									setSelectedScenarios([]);
								}}
								className="text-xs px-2 py-1 rounded border hover:bg-gray-50"
								disabled={isRunning}
							>
								All
							</button>
							<button
								onClick={() =>
									setSelectedScenarios(filteredScenarios.map((s) => s.id))
								}
								className="text-xs px-2 py-1 rounded border hover:bg-gray-50"
								disabled={isRunning}
							>
								Select All
							</button>
						</div>
					</div>
					<div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-1">
						{filteredScenarios.map((s) => (
							<label
								key={s.id}
								className="flex items-center gap-2 text-xs p-1 rounded hover:bg-gray-50"
							>
								<input
									type="checkbox"
									checked={
										selectedScenarios.length === 0 ||
										selectedScenarios.includes(s.id)
									}
									onChange={() => toggleScenario(s.id)}
									disabled={isRunning}
									className="rounded"
								/>
								<span className="font-mono">{s.id}</span>
								<span className="text-gray-500 truncate">{s.name}</span>
							</label>
						))}
					</div>
				</div>
			)}

			{/* Progress */}
			{runId && (
				<div className="bg-white rounded-lg border shadow-sm p-4">
					<h3 className="font-semibold mb-3">
						Progress
						<span className="text-xs font-normal text-gray-400 ml-2">
							Run: {runId}
						</span>
					</h3>
					<RunProgress
						scenarioIds={scenarioIds}
						models={selectedModels}
						progress={progress}
						isRunning={isRunning}
					/>
					{completedReport && (
						<div className="mt-4 p-3 bg-green-50 rounded border border-green-200">
							<span className="text-green-700 text-sm font-medium">
								Run completed!
							</span>
							<a
								href={`/reports/${completedReport}`}
								className="ml-3 text-sm text-blue-600 hover:underline"
							>
								View Report
							</a>
						</div>
					)}
				</div>
			)}
		</div>
	);
}
