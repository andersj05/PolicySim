import { useEffect, useState } from 'react';

function requestError(error: unknown): string {
  return error instanceof Error && !(error instanceof TypeError)
    ? error.message
    : 'Cannot reach the research server. Check that the app is running and retry.';
}

async function responsePayload(response: Response): Promise<unknown> {
  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new Error(
      'The research server returned an incomplete response. Please retry.',
    );
  }
  if (!response.ok) {
    const detail =
      payload && typeof payload === 'object' && 'detail' in payload
        ? payload.detail
        : undefined;
    throw new Error(
      typeof detail === 'string'
        ? detail
        : 'Check the selected inputs and retry.',
    );
  }
  return payload;
}

export async function post<T>(
  url: string,
  body: unknown,
  signal?: AbortSignal,
): Promise<T> {
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal,
    });
    return (await responsePayload(response)) as T;
  } catch (error) {
    throw new Error(requestError(error), { cause: error });
  }
}

export function useAnalysis<T>(url: string, body: unknown) {
  const serialized = JSON.stringify(body);
  const [result, setResult] = useState<{
    key: string;
    data?: T;
    error?: string;
  }>();
  const [retry, setRetry] = useState(0);
  const key = `${serialized}-${retry}`;
  useEffect(() => {
    const controller = new AbortController();
    void post<T>(url, JSON.parse(serialized), controller.signal).then(
      (data) => {
        if (!controller.signal.aborted) setResult({ key, data });
      },
      (error: unknown) => {
        if (!controller.signal.aborted)
          setResult({
            key,
            error: error instanceof Error ? error.message : 'Analysis failed.',
          });
      },
    );
    return () => controller.abort();
  }, [url, serialized, key]);
  return {
    data: result?.key === key ? result.data : undefined,
    error: result?.key === key ? result.error : undefined,
    loading: result?.key !== key,
    retry: () => setRetry((v) => v + 1),
  };
}

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
        const payload = await responsePayload(response);
        if (!controller.signal.aborted)
          setResult({ url: url!, refresh, data: payload as T });
      } catch (error) {
        if (!controller.signal.aborted)
          setResult({
            url: url!,
            refresh,
            error: requestError(error),
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
