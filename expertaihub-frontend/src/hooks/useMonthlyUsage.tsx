// src/hooks/useMonthlyUsage.tsx
"use client";

import { useCallback, useEffect, useState } from "react";
import apiPrivate from "@/lib/apiprivate";

type Usage = { used: number; limit: number };

export function useMonthlyUsage(userId: number) {
  const [usage, setUsage] = useState<Usage>({ used: 0, limit: 15 }); // sensible fallback

  /** Fetch the latest counter from the API. Safe to call any time. */
  const refresh = useCallback(async () => {
    if (!userId) return;
    try {
      const r = await apiPrivate.get<{ count: number; limit: number }>("/monthly-usage/");
      setUsage({ used: r.data.count, limit: r.data.limit });
    } catch (err) {
      console.error("monthly-usage fetch error:", err);
    }
  }, [userId]);

  useEffect(() => {
        refresh();
      }, [refresh]);
    

  return { ...usage, refresh };   // { used, limit, refresh }
} 
