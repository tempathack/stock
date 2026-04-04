import { useState, useEffect } from "react";
import { fetchMacroHistory } from "@/api/client";
import type { MacroHistoryPoint } from "@/api/types";

export function useMacroHistory(days: number = 90): {
  data: MacroHistoryPoint[];
  loading: boolean;
  error: string | null;
} {
  const [data, setData] = useState<MacroHistoryPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchMacroHistory(days)
      .then((points) => {
        if (!cancelled) {
          setData(points);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load macro history");
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [days]);

  return { data, loading, error };
}
