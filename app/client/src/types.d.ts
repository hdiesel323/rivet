interface Message {
  role: string;
  content: string;
}

interface RivetOptions {
  slot: "none" | "rules" | "jev" | "classifier:heuristic";
  route: "cascade" | "pin-local" | "pin-frontier";
  residency: "any" | "local";
  max_usd: number;
  split_challenger_pct: number;
}

interface ClassifierReceipt {
  slot: string;
  labels: Record<string, unknown> | null;
  confidence: number | null;
}

interface RivetReceipt {
  receipt_id: string;
  model_used: string;
  provider: string;
  why: string;
  vendor_usd: number;
  rivet_usd: number;
  escalated: boolean;
  fallback: boolean;
  cache_hit: boolean;
  classifier: ClassifierReceipt;
  experiment_cell: string;
  cluster: string;
  latency_ms: number;
}

interface ChatCompletionResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: { index: number; message: Message; finish_reason: string }[];
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  rivet: RivetReceipt;
}

interface ApiError {
  error: { message: string; type: string; code: string };
}

interface Connector {
  id: string;
  kind: string;
  status: string;
  models: string[];
}

interface HealthResponse {
  status: "ok" | "error";
  version: string;
  demo: boolean;
  connectors: string[];
  ledger_rows: number;
}

interface LedgerRow {
  id: string;
  created_at: string;
  model_used: string;
  provider: string;
  vendor_usd: number;
  rivet_usd: number;
  why: string;
  cache_hit: number;
  slot: string;
  cluster: string;
}

interface EvalCompareResponse {
  slots: string[];
  quality_delta: number | null;
  note: string;
  columns: {
    slot: string;
    n: number;
    vendor_usd: number;
    by_model: Record<string, number>;
    escalated: number;
  }[];
}
