import { useEffect, useState } from 'react';

interface Props {
  scenarioIds: string[];
  models: string[];
  progress: Record<string, Record<string, string>>;
  isRunning: boolean;
}

const cellColors: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-400',
  running: 'bg-blue-100 text-blue-700 animate-pulse',
  ok: 'bg-green-100 text-green-700',
  error: 'bg-red-100 text-red-700',
};

function ElapsedTimer({ running }: { running: boolean }) {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    if (!running) return;
    setSeconds(0);
    const interval = setInterval(() => setSeconds(s => s + 1), 1000);
    return () => clearInterval(interval);
  }, [running]);

  if (!running && seconds === 0) return null;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return <span className="text-xs text-gray-400 ml-2">{m}:{s.toString().padStart(2, '0')}</span>;
}

export function RunProgress({ scenarioIds, models, progress, isRunning }: Props) {
  const total = scenarioIds.length * models.length;
  const completed = Object.values(progress).flatMap(m => Object.values(m)).filter(s => s === 'ok' || s === 'error').length;
  const running = Object.values(progress).flatMap(m => Object.values(m)).filter(s => s === 'running').length;

  return (
    <div>
      <div className="mb-3 flex items-center gap-3">
        <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 transition-all duration-300"
            style={{ width: `${total ? (completed / total) * 100 : 0}%` }}
          />
        </div>
        <span className="text-sm text-gray-600">
          {completed}/{total}
          {running > 0 && <span className="text-blue-600 ml-1">({running} running)</span>}
        </span>
        <ElapsedTimer running={isRunning} />
      </div>

      {isRunning && completed === 0 && (
        <p className="text-xs text-gray-400 mb-2">
          claude -p calls can take 1-3 min each (especially opus). Be patient.
        </p>
      )}

      <div className="overflow-x-auto">
        <table className="text-sm border-collapse">
          <thead>
            <tr>
              <th className="px-3 py-1 text-left text-gray-500 font-normal">Scenario</th>
              {models.map(m => (
                <th key={m} className="px-3 py-1 text-center font-medium">{m}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {scenarioIds.map(sid => (
              <tr key={sid}>
                <td className="px-3 py-1 font-mono text-xs">{sid}</td>
                {models.map(m => {
                  const status = progress[sid]?.[m] || 'pending';
                  return (
                    <td key={m} className="px-3 py-1 text-center">
                      <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${cellColors[status]}`}>
                        {status}
                      </span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
