import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { api, type ScenarioSummary } from '../api/client';
import { CategoryTag } from '../components/CategoryTag';
import { YamlEditor } from '../components/YamlEditor';

export function Scenarios() {
  const { data: scenarios, isLoading } = useQuery({ queryKey: ['scenarios'], queryFn: api.getScenarios });
  const [editingFile, setEditingFile] = useState<string | null>(null);
  const queryClient = useQueryClient();

  if (isLoading) return <div className="text-gray-500">Loading...</div>;
  if (!scenarios) return null;

  // Group by source_file
  const groups = new Map<string, ScenarioSummary[]>();
  for (const s of scenarios) {
    const list = groups.get(s.source_file) || [];
    list.push(s);
    groups.set(s.source_file, list);
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Scenarios</h1>
      <p className="text-gray-600 mb-6">{scenarios.length} scenarios across {groups.size} files</p>

      {Array.from(groups.entries()).map(([file, items]) => (
        <div key={file} className="mb-8">
          <div className="flex items-center gap-3 mb-3">
            <h2 className="font-semibold font-mono text-sm">{file}</h2>
            <span className="text-xs text-gray-400">{items.length} scenarios</span>
            <button
              onClick={() => setEditingFile(editingFile === file ? null : file)}
              className="text-xs px-2 py-1 rounded border text-gray-600 hover:bg-gray-50"
            >
              {editingFile === file ? 'Close Editor' : 'Edit YAML'}
            </button>
          </div>

          {editingFile === file && (
            <div className="mb-4">
              <YamlEditor
                sourceFile={file}
                onSaved={() => queryClient.invalidateQueries({ queryKey: ['scenarios'] })}
              />
            </div>
          )}

          <div className="bg-white rounded-lg border shadow-sm divide-y">
            {items.map(s => (
              <Link
                key={s.id}
                to={`/scenarios/${s.id}`}
                className="block px-4 py-3 hover:bg-gray-50"
              >
                <div className="flex items-center gap-3 mb-1">
                  <span className="font-mono text-sm font-medium text-blue-600">{s.id}</span>
                  <span className="font-medium">{s.name}</span>
                  <span className="text-xs text-gray-400 ml-auto">{s.target_skill}</span>
                </div>
                <p className="text-sm text-gray-600 mb-2 line-clamp-1">{s.prompt}</p>
                <div className="flex flex-wrap">
                  {s.expected_complexities.map(c => (
                    <CategoryTag key={c.id} id={c.id} name={c.name} severity={c.severity} description={c.description} />
                  ))}
                </div>
              </Link>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
