import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { api } from '../api/client';

export function Reports() {
  const queryClient = useQueryClient();
  const { data: reports, isLoading } = useQuery({ queryKey: ['reports'], queryFn: api.getReports });

  const deleteMutation = useMutation({
    mutationFn: api.deleteReport,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['reports'] }),
  });

  if (isLoading) return <div className="text-gray-500">Loading...</div>;
  if (!reports) return null;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Reports</h1>

      {reports.length === 0 ? (
        <div className="text-gray-500 p-8 text-center bg-white rounded-lg border">
          No reports yet. <Link to="/run" className="text-blue-600 hover:underline">Run some scenarios</Link> to generate reports.
        </div>
      ) : (
        <div className="bg-white rounded-lg border shadow-sm divide-y">
          {reports.map(r => (
            <div key={r.filename} className="flex items-center justify-between px-4 py-3 hover:bg-gray-50">
              <Link to={`/reports/${r.filename}`} className="flex-1">
                <span className="font-mono text-sm font-medium">{r.filename}</span>
                <span className="text-xs text-gray-400 ml-3">
                  {r.models?.join(', ')} — {r.scenario_count} scenarios
                </span>
              </Link>
              <button
                onClick={(e) => {
                  e.preventDefault();
                  if (confirm(`Delete ${r.filename}?`)) {
                    deleteMutation.mutate(r.filename);
                  }
                }}
                className="text-xs text-red-500 hover:text-red-700 px-2 py-1"
              >
                Delete
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
