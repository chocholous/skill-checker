const colors: Record<string, string> = {
  CRITICAL: 'bg-red-600 text-white',
  HIGH: 'bg-orange-500 text-white',
  MEDIUM: 'bg-yellow-400 text-gray-900',
  LOW: 'bg-green-500 text-white',
};

export function SeverityBadge({ severity }: { severity: string | null }) {
  if (!severity) return null;
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${colors[severity] || 'bg-gray-300'}`}>
      {severity}
    </span>
  );
}
