import { useCallback, useRef, useState } from 'react';

interface SSEEvent {
  event: string;
  data: Record<string, unknown>;
}

interface UseSSEReturn {
  events: SSEEvent[];
  isConnected: boolean;
  connect: (runId: string) => void;
  disconnect: () => void;
}

export function useSSE(): UseSSEReturn {
  const [events, setEvents] = useState<SSEEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const sourceRef = useRef<EventSource | null>(null);

  const disconnect = useCallback(() => {
    if (sourceRef.current) {
      sourceRef.current.close();
      sourceRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const connect = useCallback((runId: string) => {
    disconnect();
    setEvents([]);

    const source = new EventSource(`/api/runs/${runId}/stream`);
    sourceRef.current = source;
    setIsConnected(true);

    const handleEvent = (type: string) => (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      setEvents(prev => [...prev, { event: type, data }]);
      if (type === 'completed' || type === 'error') {
        disconnect();
      }
    };

    source.addEventListener('started', handleEvent('started'));
    source.addEventListener('progress', handleEvent('progress'));
    source.addEventListener('completed', handleEvent('completed'));
    source.addEventListener('error', handleEvent('error'));

    source.onerror = () => {
      disconnect();
    };
  }, [disconnect]);

  return { events, isConnected, connect, disconnect };
}
