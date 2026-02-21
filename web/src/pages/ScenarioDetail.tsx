import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { CategoryTag } from '../components/CategoryTag';
import { MarkdownViewer } from '../components/MarkdownViewer';

export function ScenarioDetail() {
  const { id } = useParams<{ id: string }>();
  const { data: scenario, isLoading } = useQuery({
    queryKey: ['scenario', id],
    queryFn: () => api.getScenario(id!),
    enabled: !!id,
  });
  const { data: skillContent } = useQuery({
    queryKey: ['skill-content', scenario?.target_skill],
    queryFn: () => api.getSkillContent(scenario!.target_skill),
    enabled: !!scenario,
  });

  if (isLoading) return <div className="text-gray-500">Loading...</div>;
  if (!scenario) return <div className="text-red-600">Scenario not found</div>;

  return (
    <div>
      <div className="mb-4">
        <Link to="/scenarios" className="text-sm text-blue-600 hover:underline">&larr; Back to Scenarios</Link>
      </div>

      <div className="bg-white rounded-lg border shadow-sm p-6 mb-6">
        <div className="flex items-center gap-3 mb-2">
          <span className="font-mono text-lg font-bold text-blue-600">{scenario.id}</span>
          <h1 className="text-xl font-bold">{scenario.name}</h1>
        </div>
        <div className="text-sm text-gray-500 mb-4">
          Skill: <span className="font-mono">{scenario.target_skill}</span> | File: <span className="font-mono">{scenario.source_file}</span>
        </div>

        <div className="mb-4">
          <h3 className="text-sm font-medium text-gray-500 mb-1">User Prompt</h3>
          <div className="p-3 bg-gray-50 rounded border text-sm italic">{scenario.prompt}</div>
        </div>

        <div className="mb-4">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Expected Complexities</h3>
          <div className="flex flex-wrap">
            {scenario.expected_complexities.map(c => (
              <CategoryTag key={c.id} id={c.id} name={c.name} severity={c.severity} description={c.description} />
            ))}
          </div>
        </div>

        <Link
          to={`/run?scenario=${scenario.id}`}
          className="inline-block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
        >
          Run This Scenario
        </Link>
      </div>

      {skillContent && (
        <div className="bg-white rounded-lg border shadow-sm p-6">
          <h2 className="font-semibold mb-1">SKILL.md Content</h2>
          <p className="text-xs text-gray-400 mb-4">{skillContent.path} ({skillContent.lines} lines)</p>
          <div className="max-h-[600px] overflow-y-auto border rounded p-4 bg-gray-50">
            <MarkdownViewer content={skillContent.content} />
          </div>
        </div>
      )}
    </div>
  );
}
