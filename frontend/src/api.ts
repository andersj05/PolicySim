import { useEffect, useState } from 'react';

export function useRemote<T>(url: string | null, refresh = 0) {
  const [result, setResult] = useState<{
    url: string;
    refresh: number;
    data?: T;
    error?: string;
  }>();
  useEffect(() => {
    if (!url) return;
    const controller = new AbortController();
    async function load() {
      try {
        const response = await fetch(url!, { signal: controller.signal });
        const payload: unknown = await response.json();
        if (!response.ok) {
          const detail = (payload as { detail?: unknown }).detail;
          throw new Error(
            typeof detail === 'string'
              ? detail
              : 'This request could not be completed. Check the inputs and retry.',
          );
        }
        if (!controller.signal.aborted)
          setResult({ url: url!, refresh, data: payload as T });
      } catch (error) {
        if (!controller.signal.aborted)
          setResult({
            url: url!,
            refresh,
            error:
              error instanceof Error
                ? error.message
                : 'Unable to reach the research server.',
          });
      }
    }
    void load();
    return () => controller.abort();
  }, [url, refresh]);
  const current =
    result?.url === url && result?.refresh === refresh ? result : undefined;
  return {
    data: current?.data,
    error: current?.error,
    loading: Boolean(url && !current),
  };
}
