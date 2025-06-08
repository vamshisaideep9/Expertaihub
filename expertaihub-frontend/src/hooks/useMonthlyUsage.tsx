// src/hooks/useMonthlyUsage.tsx
"use client";

import { useEffect, useRef, useState } from "react";
import apiPrivate from "@/lib/apiprivate";

type Usage = { used: number; limit: number };

/**
 * Subscribe to the caller’s monthly-usage counter.
 *
 * 1.  Bootstrap with a one-shot REST call  →  /monthly-usage/
 * 2.  Stay fresh via WebSocket             →  /ws/usage/:userId/?token=…
 *
 * The hook auto-reconnects on drop.  Call the returned `refresh()` anytime
 * you want to re-fetch the numbers explicitly.
 */
export function useMonthlyUsage(userId: number) {
  const [usage, setUsage] = useState<Usage>({ used: 0, limit: 15 }); // safe default
  const wsRef = useRef<WebSocket | null>(null);

  /* ───────── helpers ───────── */

  /** Gracefully close an existing socket */
  const closeSocket = () => {
    try {
      wsRef.current?.close();
    } catch {
      /* ignore */
    }
    wsRef.current = null;
  };

  /** Translate NEXT_PUBLIC_WS_BASE (optional) → ws://… */
  const wsOrigin = () => {
    const env = process.env.NEXT_PUBLIC_WS_BASE?.trim();
    return (env || location.origin).replace(/^http/, "ws").replace(/\/$/, "");
  };

  /** One-shot REST fetch (also exposed as `refresh`) */
  const refresh = async () => {
    try {
      const { data } = await apiPrivate.get<{ count: number; limit: number }>(
        "/monthly-usage/"
      );
      setUsage({ used: data.count, limit: data.limit });
    } catch (err) {
      console.error("usage-refresh error:", err);
    }
  };

  /* ───────── REST bootstrap ───────── */
  useEffect(() => {
    if (userId) refresh();
  }, [userId]);

  /* ───────── live WebSocket ───────── */
  useEffect(() => {
    if (!userId) return;

    const openSocket = () => {
      closeSocket();

      const token =
        document.cookie.match(/(?:^|; )token=([^;]+)/)?.[1] || "";
      if (!token) {
        console.error("Monthly-usage WS: auth token missing");
        return;
      }

      const ws = new WebSocket(`${wsOrigin()}/ws/usage/${userId}/?token=${token}`);
      wsRef.current = ws;

      ws.onmessage = (ev) => {
        try {
          const { count } = JSON.parse(ev.data);
          setUsage((u) => ({ ...u, used: count }));
        } catch (err) {
          console.error("usage-socket bad payload:", err, ev.data);
        }
      };

      ws.onerror = (evt) => {
        console.error("usage-socket error", {
          type: evt.type,
          url: (evt.currentTarget as WebSocket).url,
          readyState: ws.readyState,
        });
      };

      ws.onclose = (evt) => {
        console.warn(
          "usage-socket closed",
          evt.code,
          evt.reason || "(no reason)",
          "readyState:", ws.readyState
        );
        wsRef.current = null;
        // Reconnect after 5 s while component is still mounted
        setTimeout(() => userId && openSocket(), 5_000);
      };
    };

    openSocket();
    return closeSocket; // cleanup on unmount / userId change
  }, [userId]);

  return { ...usage, refresh }; // { used, limit, refresh }
}
