const API_BASE_URL = import.meta.env.DEV ? "" : "http://127.0.0.1:8000";

async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  });
  const data: unknown = await response.json().catch(() => ({}));
  if (!response.ok) {
    const err = data as ApiError;
    const message = err.error?.message || `HTTP ${response.status}`;
    throw new Error(message);
  }
  return data as T;
}

export const api = {
  health(): Promise<HealthResponse> {
    return apiRequest<HealthResponse>("/health");
  },
  connectors(): Promise<{ connectors: Connector[] }> {
    return apiRequest("/v1/connectors");
  },
  chat(body: {
    model: string;
    messages: Message[];
    rivet: RivetOptions;
  }): Promise<ChatCompletionResponse> {
    return apiRequest("/v1/chat/completions", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },
  ledger(limit = 20): Promise<{ data: LedgerRow[] }> {
    return apiRequest(`/v1/ledger?limit=${limit}`);
  },
  compare(limit = 20): Promise<EvalCompareResponse> {
    return apiRequest("/v1/eval/compare", {
      method: "POST",
      body: JSON.stringify({ slots: ["rules", "none"], limit }),
    });
  },
};
