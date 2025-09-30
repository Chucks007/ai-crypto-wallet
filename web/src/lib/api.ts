import axios, { isAxiosError } from "axios";
export const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE || "http://localhost:8000" });

export type SuggestionCreatePayload = {
  rule: string;
  asset_from?: string | null;
  asset_to?: string | null;
  amount_usd?: number | null;
  confidence?: number | null;
  params_json?: string | null;
  reasoning?: string | null;
};

export type Suggestion = SuggestionCreatePayload & {
  id: number;
  created_at: string;
};

export type BalanceSnapshot = {
  id: number;
  asset: string;
  balance: number;
  usd_price?: number | null;
  usd_value?: number | null;
  source?: string | null;
  captured_at?: string | null;
};

export type DecisionStatus = "approved" | "rejected" | "expired" | "cancelled";

export type Decision = {
  id: number;
  suggestion_id: number;
  decision: DecisionStatus;
  reason: string | null;
  decided_at: string;
};

export type DecisionListParams = {
  status?: DecisionStatus;
  decided_after?: string;
  decided_before?: string;
  page?: number;
  page_size?: number;
};

export type DecisionListResponse = {
  items: Decision[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
};

export type DecisionCreatePayload = {
  suggestion_id: number;
  decision: DecisionStatus;
  reason?: string | null;
};
export async function getHealth() { const r = await api.get("/v1/health"); return r.data; }
export async function getBalances(): Promise<BalanceSnapshot[]> {
  const r = await api.get(`/v1/balances`);
  return (r.data ?? []) as BalanceSnapshot[];
}
export async function listSuggestions(limit = 50): Promise<Suggestion[]> {
  const r = await api.get(`/v1/suggestions`, { params: { limit } });
  return (r.data ?? []) as Suggestion[];
}
export async function createSuggestion(body: SuggestionCreatePayload): Promise<Suggestion> {
  const r = await api.post(`/v1/suggestions`, body);
  return r.data as Suggestion;
}
export async function listDecisions(params: DecisionListParams = {}): Promise<DecisionListResponse> {
  const query = { page: 1, page_size: 50, ...params };
  const r = await api.get(`/v1/decisions`, { params: query });
  return r.data as DecisionListResponse;
}
export async function createDecision(body: DecisionCreatePayload): Promise<Decision> {
  const r = await api.post(`/v1/decisions`, body);
  return r.data as Decision;
}
export type ApprovalEvaluatePayload = {
  asset_from: string;
  asset_to: string;
  suggested_amount_usd: number;
  slippage_bps?: number | null;
  gas_estimate_usd?: number | null;
};

export type ApprovalEvaluateResponse = {
  status: string;
  asset_from: string;
  asset_to: string;
  suggested_amount_usd: number;
  capped_amount_usd: number;
  cap_notes: string[];
  violations: string[];
};

export type ApprovalCommitPayload = ApprovalEvaluatePayload & {
  suggestion_id: number;
  reason?: string | null;
};

export type ApprovalCommitResponse = {
  evaluation: ApprovalEvaluateResponse;
  created: boolean;
  decision?: Decision | null;
};

export async function evaluateApproval(body: ApprovalEvaluatePayload): Promise<ApprovalEvaluateResponse> {
  const r = await api.post(`/v1/approvals/evaluate`, body);
  return r.data as ApprovalEvaluateResponse;
}
export async function commitApproval(body: ApprovalCommitPayload): Promise<ApprovalCommitResponse> {
  const r = await api.post(`/v1/approvals/commit`, body);
  return r.data as ApprovalCommitResponse;
}

export type RuntimeFlag = {
  key: string;
  value: string;
  updated_at: string;
};

export type EmergencyStopState = {
  enabled: boolean;
  updated_at: string | null;
};

export async function listRuntimeFlags(): Promise<RuntimeFlag[]> {
  const r = await api.get(`/v1/runtime-flags`);
  return (r.data ?? []) as RuntimeFlag[];
}
export async function getEmergencyStop(): Promise<EmergencyStopState> {
  const r = await api.get(`/v1/runtime-flags/emergency-stop`);
  return r.data as EmergencyStopState;
}
export async function setEmergencyStop(enabled: boolean): Promise<EmergencyStopState> {
  const r = await api.put(`/v1/runtime-flags/emergency-stop`, { enabled });
  return r.data as EmergencyStopState;
}
export type TradeStatus = "submitted" | "confirmed" | "failed" | "cancelled";

export type Trade = {
  id: number;
  suggestion_id: number;
  executed_at: string | null;
  status: TradeStatus;
  tx_hash: string | null;
  asset_from: string | null;
  amount_from: number | null;
  asset_to: string | null;
  amount_to: number | null;
  slippage_bps: number | null;
  gas_est_usd: number | null;
  error: string | null;
};

export async function listTrades(limit = 50): Promise<Trade[]> {
  const r = await api.get(`/v1/trades`, { params: { limit } });
  return (r.data ?? []) as Trade[];
}
export async function getAutoMode(): Promise<boolean> {
  try {
    const r = await api.get(`/v1/runtime-flags/auto_mode`);
    const v = String(r.data?.value ?? "").toLowerCase();
    return ["1","true","on","yes"].includes(v);
  } catch (error: unknown) {
    if (isAxiosError(error) && error.response?.status === 404) return false;
    throw error;
  }
}
export async function setAutoMode(enabled: boolean): Promise<RuntimeFlag> {
  const r = await api.put(`/v1/runtime-flags/auto_mode`, { value: String(enabled) });
  return r.data as RuntimeFlag;
}
export async function getRuntimeFlag(key: string): Promise<RuntimeFlag | null> {
  try {
    const r = await api.get(`/v1/runtime-flags/${encodeURIComponent(key)}`);
    return r.data as RuntimeFlag;
  } catch (error: unknown) {
    if (isAxiosError(error) && error.response?.status === 404) return null;
    throw error;
  }
}
export type DailyMetrics = {
  today: {
    suggestions: number;
    decisions: Record<string, number>;
    trades: Record<string, number>;
  };
  last_worker: {
    last_start: string | null;
    last_finish: string | null;
  };
};
export async function getDailyMetrics(): Promise<DailyMetrics> {
  const r = await api.get(`/v1/metrics/daily`);
  return r.data as DailyMetrics;
}

export type ExecutionStatus = {
  execution_enabled: boolean;
  allowed_chain_ids: number[];
  configured_chain_id: number | null;
  signer_ready: boolean;
  signer_address: string | null;
  signer_error: string | null;
  permit2: {
    enabled: boolean;
    ready: boolean;
    status: string;
    contract: string | null;
    default_spender: string | null;
  };
};

export type ExecutionToken = {
  chain_id: number;
  symbol: string;
  address?: string | null;
  decimals: number;
  usd_price?: number | null;
  price_source: string;
  min_trade_usd?: number | null;
  coingecko_id?: string | null;
};

export async function getExecutionStatus(): Promise<ExecutionStatus> {
  const r = await api.get(`/v1/execution/status`);
  return r.data as ExecutionStatus;
}

export async function getExecutionTokens(chainId?: number): Promise<ExecutionToken[]> {
  const params = typeof chainId === "number" ? { chain_id: chainId } : undefined;
  const r = await api.get(`/v1/execution/tokens`, params ? { params } : undefined);
  return r.data as ExecutionToken[];
}
