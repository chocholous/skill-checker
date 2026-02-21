const BASE = '/api';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
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
  type: 'GEN' | 'APF';
}

export interface ExpectedComplexity {
  id: string;
  type: string;
  severity: string | null;
  name: string | null;
  description: string | null;
}

export interface ScenarioSummary {
  id: string;
  name: string;
  prompt: string;
  target_skill: string;
  source_file: string;
  expected_complexities: ExpectedComplexity[];
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

export interface RunStartResponse {
  run_id: string;
  total: number;
  scenarios: number;
  models: string[];
}

export interface RunResultResponse {
  run_id: string;
  status: string;
  models: string[];
  scenario_ids: string[];
  progress: Record<string, Record<string, string>>;
  started_at: string;
  completed_at: string;
  error: string | null;
  result_count: number;
  results: Array<{
    scenario_id: string;
    model: string;
    response: string;
    duration_s: number;
    cost_info: string;
    error: string | null;
  }>;
}

export interface CategoriesResponse {
  gen: Record<string, CategoryInfo>;
  apf: Record<string, CategoryInfo>;
  total: number;
}

// --- API functions ---

export const api = {
  getScenarios: () => request<ScenarioSummary[]>('/scenarios'),
  getScenario: (id: string) => request<ScenarioSummary>(`/scenarios/${id}`),
  getRawYaml: (sourceFile: string) => request<{ source_file: string; content: string }>(`/scenarios/file/${sourceFile}/raw`),
  updateYaml: (sourceFile: string, content: string) =>
    request<{ status: string }>(`/scenarios/file/${sourceFile}`, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    }),

  getCategories: () => request<CategoriesResponse>('/categories'),

  getSkills: () => request<Record<string, SkillInfo>>('/skills'),
  getSkillContent: (name: string) => request<{ name: string; path: string; content: string; lines: number }>(`/skills/${name}/content`),

  startRun: (opts: { scenario_ids?: string[]; models?: string[]; concurrency?: number }) =>
    request<RunStartResponse>('/runs', {
      method: 'POST',
      body: JSON.stringify(opts),
    }),
  getRunResult: (runId: string) => request<RunResultResponse>(`/runs/${runId}/result`),

  getReports: () => request<ReportSummary[]>('/reports'),
  getReport: (filename: string) => request<{ filename: string; content: string }>(`/reports/${filename}`),
  deleteReport: (filename: string) => request<{ status: string }>(`/reports/${filename}`, { method: 'DELETE' }),
};
