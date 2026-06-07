"use client";
import { useEffect, useRef, useCallback, useState } from "react";
import { WebSocketMessage } from "@/types/tracker";

type Status = "connecting" | "open" | "closed" | "error";

export function useWebSocket(url: string | null, onMessage: (m: WebSocketMessage) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState<Status>("closed");
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const retryCount = useRef(0);

  const connect = useCallback(() => {
    if (!url) return;
    setStatus("connecting");
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => { setStatus("open"); retryCount.current = 0; };
    ws.onmessage = (e) => {
      try { onMessage(JSON.parse(e.data)); } catch { /* ignore malformed */ }
    };
    ws.onerror = () => setStatus("error");
    ws.onclose = () => {
      setStatus("closed");
      // exponential backoff up to 30s
      const delay = Math.min(1000 * 2 ** retryCount.current, 30000);
      retryCount.current += 1;
      retryRef.current = setTimeout(connect, delay);
    };
  }, [url, onMessage]);

  useEffect(() => {
    connect();
    return () => {
      if (retryRef.current) clearTimeout(retryRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const disconnect = useCallback(() => {
    if (retryRef.current) clearTimeout(retryRef.current);
    wsRef.current?.close();
    wsRef.current = null;
  }, []);

  return { status, disconnect };
}
