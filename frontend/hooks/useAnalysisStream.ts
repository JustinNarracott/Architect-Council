import { useState, useEffect, useRef, useCallback } from 'react';
import { AgentMessage, AgentState } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8011";

export function useAnalysisStream(streamUrl: string | null) {
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [agentStates, setAgentStates] = useState<Record<string, AgentState['status']>>({});
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectAttemptRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number>(0);

  const handleMessage = useCallback((data: AgentMessage) => {
    setMessages((prev) => [...prev, data]);

    // Update agent panel state
    setAgentStates((prev) => {
      const newStates = { ...prev };
      if (data.message_type === 'thinking') {
        newStates[data.agent_id] = 'thinking';
      } else if (data.agent_id !== 'system') {
        // Any non-thinking message from a real agent marks them done
        newStates[data.agent_id] = 'done';
      }
      return newStates;
    });
  }, []);

  const closeStream = useCallback((src: EventSource) => {
    src.close();
    eventSourceRef.current = null;
    setIsConnected(false);
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const connect = useCallback((url: string) => {
    // Close any existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const fullUrl = `${API_BASE_URL}${url}`;
    const eventSource = new EventSource(fullUrl);
    eventSourceRef.current = eventSource;

    // ── Standard 'message' event (agent updates) ──────────────────────────
    eventSource.addEventListener('message', (event) => {
      try {
        const data = JSON.parse(event.data) as AgentMessage;
        handleMessage(data);
      } catch (err) {
        console.error('Error parsing SSE message:', err);
      }
    });

    // ── 'complete' event — review finished ────────────────────────────────
    eventSource.addEventListener('complete', () => {
      closeStream(eventSource);
      reconnectAttemptRef.current = 0;
    });

    // ── 'timeout' event — server-side timeout ─────────────────────────────
    eventSource.addEventListener('timeout', () => {
      setError('Review timed out. The evaluation took too long — please try again.');
      closeStream(eventSource);
    });

    // ── 'heartbeat' event — keepalive, ignore ─────────────────────────────
    eventSource.addEventListener('heartbeat', () => {
      // No-op: just keeps connection alive through proxies
    });

    // ── Connection error ──────────────────────────────────────────────────
    eventSource.onerror = () => {
      if (eventSource.readyState === EventSource.CLOSED) {
        // Stream closed naturally after complete — not an error
        return;
      }

      // Attempt ONE reconnect before showing error
      if (reconnectAttemptRef.current === 0) {
        reconnectAttemptRef.current = 1;
        console.warn('SSE connection dropped — attempting reconnect…');
        closeStream(eventSource);
        setTimeout(() => {
          setIsConnected(true);
          connect(url);
        }, 2000);
      } else {
        setError('Connection lost. The review may still be running — refresh to check.');
        closeStream(eventSource);
      }
    };
  }, [handleMessage, closeStream]);

  useEffect(() => {
    if (!streamUrl) return;

    // Reset all state for a new submission
    setMessages([]);
    setAgentStates({});
    setError(null);
    setElapsedSeconds(0);
    reconnectAttemptRef.current = 0;
    setIsConnected(true);
    startTimeRef.current = Date.now();

    // Start elapsed timer
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - startTimeRef.current) / 1000));
    }, 1000);

    connect(streamUrl);

    return () => {
      eventSourceRef.current?.close();
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [streamUrl, connect]);

  return { messages, agentStates, isConnected, error, elapsedSeconds };
}
