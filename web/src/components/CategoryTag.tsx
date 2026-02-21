import { SeverityBadge } from './SeverityBadge';

interface Props {
  id: string;
  name: string | null;
  severity: string | null;
  description: string | null;
}

export function CategoryTag({ id, name, severity, description }: Props) {
  return (
    <span className="group relative inline-flex items-center gap-1 mr-1 mb-1">
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-gray-100 border border-gray-200 text-xs font-mono">
        <SeverityBadge severity={severity} />
        {id}
      </span>
      {(name || description) && (
        <span className="absolute bottom-full left-0 mb-1 hidden group-hover:block z-10 w-64 p-2 rounded bg-gray-800 text-white text-xs shadow-lg">
          <strong>{id}: {name}</strong>
          {description && <p className="mt-1 opacity-80">{description}</p>}
        </span>
      )}
    </span>
  );
}
