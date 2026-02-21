import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import { SeverityBadge } from '../components/SeverityBadge';

export function Dashboard() {
  const scenarios = useQuery({ queryKey: ['scenarios'], queryFn: api.getScenarios });
  const categories = useQuery({ queryKey: ['categories'], queryFn: api.getCategories });
  const skills = useQuery({ queryKey: ['skills'], queryFn: api.getSkills });
  const reports = useQuery({ queryKey: ['reports'], queryFn: api.getReports });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="Scenarios" value={scenarios.data?.length} href="/scenarios" />
        <StatCard label="Skills" value={skills.data ? Object.keys(skills.data).length : undefined} />
        <StatCard label="Categories" value={categories.data?.total} />
        <StatCard label="Reports" value={reports.data?.length} href="/reports" />
      </div>

      {/* Quick run */}
      <div className="mb-8 p-4 bg-white rounded-lg border shadow-sm">
        <h2 className="font-semibold mb-2">Quick Run</h2>
        <div className="flex gap-2">
          <Link to="/run" className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm">
            Run All Scenarios
          </Link>
          <Link to="/run?model=haiku" className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 text-sm">
            Quick Test (Haiku)
          </Link>
        </div>
      </div>

      {/* Recent reports */}
      {reports.data && reports.data.length > 0 && (
        <div className="mb-8">
          <h2 className="font-semibold mb-3">Recent Reports</h2>
          <div className="bg-white rounded-lg border shadow-sm divide-y">
            {reports.data.slice(0, 5).map(r => (
              <Link
                key={r.filename}
                to={`/reports/${r.filename}`}
                className="flex items-center justify-between px-4 py-3 hover:bg-gray-50"
              >
                <span className="font-mono text-sm">{r.filename}</span>
                <span className="text-xs text-gray-500">
                  {r.models?.join(', ')} — {r.scenario_count} scenarios
                </span>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Categories overview */}
      {categories.data && (
        <div>
          <h2 className="font-semibold mb-3">Category Taxonomy</h2>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-white rounded-lg border shadow-sm p-4">
              <h3 className="font-medium text-sm text-gray-500 mb-2">GEN — General Quality ({Object.keys(categories.data.gen).length})</h3>
              <div className="space-y-1">
                {Object.values(categories.data.gen).map(c => (
                  <div key={c.id} className="flex items-center gap-2 text-sm">
                    <SeverityBadge severity={c.severity} />
                    <span className="font-mono text-xs">{c.id}</span>
                    <span>{c.name}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-white rounded-lg border shadow-sm p-4">
              <h3 className="font-medium text-sm text-gray-500 mb-2">APF — Platform Pitfalls ({Object.keys(categories.data.apf).length})</h3>
              <div className="space-y-1">
                {Object.values(categories.data.apf).map(c => (
                  <div key={c.id} className="flex items-center gap-2 text-sm">
                    <SeverityBadge severity={c.severity} />
                    <span className="font-mono text-xs">{c.id}</span>
                    <span>{c.name}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, href }: { label: string; value?: number; href?: string }) {
  const content = (
    <div className="bg-white rounded-lg border shadow-sm p-4">
      <div className="text-3xl font-bold text-blue-600">{value ?? '—'}</div>
      <div className="text-sm text-gray-500 mt-1">{label}</div>
    </div>
  );
  if (href) return <Link to={href}>{content}</Link>;
  return content;
}
