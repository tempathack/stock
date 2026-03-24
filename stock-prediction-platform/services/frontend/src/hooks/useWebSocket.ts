import { useEffect, useRef, useState, useCallback } from "react";
import type {
  WebSocketMessage,
  WebSocketPriceUpdate,
  WebSocketStatus,
} from "@/api/types";

export interface UseWebSocketOptions {
  enabled?: boolean;
  reconnectAttempts?: number;
  reconnectInterval?: number;
  onMessage?: (data: WebSocketMessage) => void;
}

export interface UseWebSocketReturn {
  status: WebSocketStatus;
  lastMessage: WebSocketMessage | null;
  prices: Map<string, WebSocketPriceUpdate>;
}

export default function useWebSocket(
  url: string,
  options: UseWebSocketOptions = {},
): UseWebSocketReturn {
  const {
    enabled = true,
    reconnectAttempts = 5,
    reconnectInterval = 3000,
    onMessage,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const attemptRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout>>();
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  const [status, setStatus] = useState<WebSocketStatus>("disconnected");
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [prices, setPrices] = useState<Map<string, WebSocketPriceUpdate>>(
    () => new Map(),
  );

  const connect = useCallback(() => {
    if (!url) return;
    setStatus("connecting");
    const ws = new WebSocket(url);

    ws.onopen = () => {
      setStatus("connected");
      attemptRef.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WebSocketMessage;
        setLastMessage(data);

        if (data.type === "price_update") {
          setPrices((prev) => {
            const next = new Map(prev);
            for (const p of data.prices) {
              next.set(p.ticker, p);
            }
            return next;
          });
        }

        onMessageRef.current?.(data);
      } catch {
        // ignore malformed messages
      }
    };

    ws.onerror = () => {
      setStatus("error");
    };

    ws.onclose = (event) => {
      setStatus("disconnected");
      wsRef.current = null;

      // Normal closure (1000) — don't reconnect
      if (event.code === 1000) return;

      if (attemptRef.current < reconnectAttempts) {
        const delay = reconnectInterval * (attemptRef.current + 1);
        attemptRef.current += 1;
        reconnectTimerRef.current = setTimeout(() => {
          connect();
        }, delay);
      } else {
        console.warn("useWebSocket: max reconnect attempts reached");
      }
    };

    wsRef.current = ws;
  }, [url, reconnectAttempts, reconnectInterval]);

  useEffect(() => {
    if (!enabled || !url) {
      // Close existing connection if disabled
      if (wsRef.current) {
        wsRef.current.close(1000);
        wsRef.current = null;
      }
      clearTimeout(reconnectTimerRef.current);
      setStatus("disconnected");
      return;
    }

    connect();

    return () => {
      clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) {
        wsRef.current.close(1000);
        wsRef.current = null;
      }
    };
  }, [url, enabled, connect]);

  return { status, lastMessage, prices };
}
