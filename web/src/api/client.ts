const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
	const res = await fetch(`${BASE}${path}`, {
		headers: { "Content-Type": "application/json" },
		...init,
	});
	if (!res.ok) {
		const body = await res.text();
		throw new Error(`${res.status}: ${body}`);
	}
	return res.json();
}

// --- Types ---

export interface CategoryInfo {
	id: string;
	name: string;
	severity: string;
	description: string;
	type: "WF" | "DK" | "BP" | "APF" | "SEC";
}

export interface CategoryGroup {
	name: string;
	default_models: string[];
	categories: Record<string, CategoryInfo>;
}

export interface ScenarioSummary {
	id: string;
	name: string;
	prompt: string;
	target_skill: string;
	source_file: string;
	category: string;
}

export interface SkillInfo {
	name: string;
	path: string;
	category: string;
	exists: boolean;
}

export interface ReportSummary {
	filename: string;
	json_filename: string | null;
	generated?: string;
	models?: string[];
	scenario_count?: number;
}

export interface CategoriesResponse {
	groups: Record<string, CategoryGroup>;
	total: number;
}

// --- Heatmap types ---

export interface DomainInfo {
	id: string;
	specialist: string;
	scenario_count: number;
	is_dev: boolean;
}

export interface SkillHealth {
	skill: string;
	domain: string;
	is_dev: boolean;
	pass_pct: number;
	pass_count: number;
	fail_count: number;
	unclear_count: number;
	na_count: number;
	top_gaps: Array<{ check_id: string; name: string; severity: string }>;
	models: string[];
}

export interface HeatmapCheck {
	id: string;
	name: string;
	severity: string;
	group: string;
}

export interface CellResult {
	result: string;
	evidence: string;
	summary: string;
}

export interface DomainHeatmapData {
	domain: string;
	specialist: string;
	is_dev: boolean;
	scenarios: Array<{ id: string; name: string }>;
	checks: HeatmapCheck[];
	models: string[];
	matrix: Record<
		string,
		Record<
			string,
			Record<string, { specialist: CellResult | null; mcpc: CellResult | null }>
		>
	>;
}

export interface BPCheck {
	id: string;
	name: string;
	severity: string;
}

export interface BPCellResult {
	result: string;
	detail: string;
}

export interface BPHeatmapData {
	skills: string[];
	checks: BPCheck[];
	matrix: Record<string, Record<string, BPCellResult>>;
}

export interface SkillDetail {
	skill: string;
	result: string;
	evidence: string;
	summary: string;
	markdown_response: string;
}

export interface CellDetail {
	scenario_id: string;
	check_id: string;
	models: Record<
		string,
		{ specialist: SkillDetail | null; mcpc: SkillDetail | null }
	>;
}

export interface ScoredRunStartResponse {
	run_id: string;
	total: number;
}

// --- API functions ---

export const api = {
	getScenarios: () => request<ScenarioSummary[]>("/scenarios"),
	getScenario: (id: string) => request<ScenarioSummary>(`/scenarios/${id}`),
	getRawYaml: (sourceFile: string) =>
		request<{ source_file: string; content: string }>(
			`/scenarios/file/${sourceFile}/raw`,
		),
	updateYaml: (sourceFile: string, content: string) =>
		request<{ status: string }>(`/scenarios/file/${sourceFile}`, {
			method: "PUT",
			body: JSON.stringify({ content }),
		}),
	createScenarioFile: (filename: string, content: string) =>
		request<{ status: string; source_file: string }>("/scenarios/file", {
			method: "POST",
			body: JSON.stringify({ filename, content }),
		}),
	deleteScenarioFile: (sourceFile: string) =>
		request<{ status: string }>(`/scenarios/file/${sourceFile}`, {
			method: "DELETE",
		}),
	getScenarioTemplates: () =>
		request<{
			domain: string;
			category: string;
			domains: string[];
			categories: string[];
		}>("/scenarios/templates"),

	getCategories: () => request<CategoriesResponse>("/categories"),

	getSkills: () => request<Record<string, SkillInfo>>("/skills"),
	getSkillContent: (name: string) =>
		request<{ name: string; path: string; content: string; lines: number }>(
			`/skills/${name}/content`,
		),

	getReports: () => request<ReportSummary[]>("/reports"),
	getReport: (filename: string) =>
		request<{ filename: string; content: string }>(`/reports/${filename}`),
	deleteReport: (filename: string) =>
		request<{ status: string }>(`/reports/${filename}`, { method: "DELETE" }),

	// Heatmap
	getHeatmapDomains: () => request<DomainInfo[]>("/heatmap/domains"),
	getHeatmapSkills: () => request<SkillHealth[]>("/heatmap/skills"),
	getHeatmapDomain: (domainId: string) =>
		request<DomainHeatmapData>(`/heatmap/domain/${domainId}`),
	getHeatmapBP: () => request<BPHeatmapData>("/heatmap/bp"),
	getHeatmapModels: () => request<string[]>("/heatmap/models"),
	getHeatmapDetail: (scenarioId: string, checkId: string) =>
		request<CellDetail>(`/heatmap/detail/${scenarioId}/${checkId}`),
	startScoredRun: (opts: {
		domains?: string[];
		models?: string[];
		concurrency?: number;
	}) =>
		request<ScoredRunStartResponse>("/heatmap/run", {
			method: "POST",
			body: JSON.stringify(opts),
		}),
};
