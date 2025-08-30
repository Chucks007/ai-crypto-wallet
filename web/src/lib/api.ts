import axios from "axios";
export const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE || "http://localhost:8000" });
export async function getHealth() { const r = await api.get("/v1/health"); return r.data; }
export async function getBalances() { const r = await api.get("/v1/balances"); return r.data; }
export async function listSuggestions(limit = 50) { const r = await api.get(`/v1/suggestions`, { params: { limit } }); return r.data; }
export async function createSuggestion(body: any) { const r = await api.post(`/v1/suggestions`, body); return r.data; }
export async function listDecisions(limit = 50) { const r = await api.get(`/v1/decisions`, { params: { limit } }); return r.data; }
export async function createDecision(body: any) { const r = await api.post(`/v1/decisions`, body); return r.data; }
export async function evaluateApproval(body: any) { const r = await api.post(`/v1/approvals/evaluate`, body); return r.data; }
