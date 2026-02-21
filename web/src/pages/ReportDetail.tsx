import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { MarkdownViewer } from '../components/MarkdownViewer';

export function ReportDetail() {
  const { filename } = useParams<{ filename: string }>();

  const { data: report, isLoading, error } = useQuery({
    queryKey: ['report', filename],
    queryFn: () => api.getReport(filename!),
    enabled: !!filename,
  });

  if (isLoading) return <div className="text-gray-500">Loading...</div>;
  if (error) return <div className="text-red-600">Error: {String(error)}</div>;
  if (!report) return null;

  return (
    <div>
      <div className="mb-4">
        <Link to="/reports" className="text-sm text-blue-600 hover:underline">&larr; Back to Reports</Link>
      </div>

      <div className="bg-white rounded-lg border shadow-sm p-6">
        <h1 className="font-mono text-lg font-bold mb-4">{filename}</h1>
        {'content' in report ? (
          <MarkdownViewer content={report.content} />
        ) : (
          <pre className="text-xs overflow-auto p-4 bg-gray-50 rounded">
            {JSON.stringify(report, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}
