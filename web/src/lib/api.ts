import axios from "axios";
export const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE || "http://localhost:8000" });
export async function getHealth() { const r = await api.get("/v1/health"); return r.data; }
export async function getBalances() { const r = await api.get("/v1/balances"); return r.data; }
export async function listSuggestions(limit = 50) { const r = await api.get(`/v1/suggestions`, { params: { limit } }); return r.data; }
export async function createSuggestion(body: any) { const r = await api.post(`/v1/suggestions`, body); return r.data; }
export async function listDecisions(limit = 50) { const r = await api.get(`/v1/decisions`, { params: { limit } }); return r.data; }
export async function createDecision(body: any) { const r = await api.post(`/v1/decisions`, body); return r.data; }
export async function evaluateApproval(body: any) { const r = await api.post(`/v1/approvals/evaluate`, body); return r.data; }
export async function commitApproval(body: any) { const r = await api.post(`/v1/approvals/commit`, body); return r.data; }
export async function listRuntimeFlags() { const r = await api.get(`/v1/runtime-flags`); return r.data; }
export async function getEmergencyStop() { const r = await api.get(`/v1/runtime-flags/emergency-stop`); return r.data; }
export async function setEmergencyStop(enabled: boolean) { const r = await api.put(`/v1/runtime-flags/emergency-stop`, { enabled }); return r.data; }
export async function getAutoMode(): Promise<boolean> {
  try {
    const r = await api.get(`/v1/runtime-flags/auto_mode`);
    const v = String(r.data?.value ?? "").toLowerCase();
    return ["1","true","on","yes"].includes(v);
  } catch (e: any) {
    if (e?.response?.status === 404) return false;
    throw e;
  }
}
export async function setAutoMode(enabled: boolean) {
  const r = await api.put(`/v1/runtime-flags/auto_mode`, { value: String(enabled) });
  return r.data;
}
export async function getRuntimeFlag(key: string): Promise<{ key: string; value: string; updated_at: string } | null> {
  try {
    const r = await api.get(`/v1/runtime-flags/${encodeURIComponent(key)}`);
    return r.data;
  } catch (e: any) {
    if (e?.response?.status === 404) return null;
    throw e;
  }
}
