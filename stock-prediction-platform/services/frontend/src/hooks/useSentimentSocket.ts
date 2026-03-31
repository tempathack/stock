/**
 * useSentimentSocket — WebSocket hook for /ws/sentiment/{ticker}.
 *
 * Opens a WebSocket connection to the sentiment endpoint when ticker is provided.
 * Pushes received SentimentData into state. Reconnects with exponential backoff
 * (max 5 retries, max 30 seconds delay) on unexpected close. Closes on unmount
 * or when ticker becomes null.
 */
import { useState, useEffect, useRef } from "react";

export type WebSocketStatus = "connecting" | "connected" | "disconnected" | "error";

export interface SentimentData {
  ticker: string;
  avg_sentiment: number | null;
  mention_count: number | null;
  positive_ratio: number | null;
  negative_ratio: number | null;
  top_subreddit: string | null;
  available: boolean;
  sampled_at: string | null;
}

export interface UseSentimentSocketReturn {
  data: SentimentData | null;
  status: WebSocketStatus;
}

export function useSentimentSocket(ticker: string | null): UseSentimentSocketReturn {
  const [data, setData] = useState<SentimentData | null>(null);
  const [status, setStatus] = useState<WebSocketStatus>("disconnected");
  const wsRef = useRef<WebSocket | null>(null);
  const retryCountRef = useRef(0);
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const MAX_RETRIES = 5;

  useEffect(() => {
    if (!ticker) {
      setStatus("disconnected");
      setData(null);
      return;
    }

    const wsBase = (import.meta.env.VITE_API_URL || "http://localhost:8000")
      .replace(/^http/, "ws");
    const url = `${wsBase}/ws/sentiment/${encodeURIComponent(ticker)}`;

    function connect(): void {
      setStatus("connecting");
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus("connected");
        retryCountRef.current = 0;
      };

      ws.onmessage = (event: MessageEvent) => {
        try {
          const parsed = JSON.parse(event.data as string) as SentimentData;
          setData(parsed);
        } catch {
          // ignore malformed JSON
        }
      };

      ws.onerror = () => {
        setStatus("error");
      };

      ws.onclose = (e: CloseEvent) => {
        setStatus("disconnected");
        wsRef.current = null;
        // code 1000 = normal close (drawer closed); don't retry
        if (e.code !== 1000 && retryCountRef.current < MAX_RETRIES) {
          const delay = Math.min(1000 * Math.pow(2, retryCountRef.current), 30_000);
          retryCountRef.current += 1;
          retryTimerRef.current = setTimeout(connect, delay);
        }
      };
    }

    connect();

    return () => {
      // Cancel any pending retry
      if (retryTimerRef.current) {
        clearTimeout(retryTimerRef.current);
        retryTimerRef.current = null;
      }
      // Close WebSocket with code 1000 (normal close — suppresses retry)
      if (wsRef.current) {
        wsRef.current.close(1000);
        wsRef.current = null;
      }
      setStatus("disconnected");
      setData(null);
    };
  }, [ticker]);

  return { data, status };
}
