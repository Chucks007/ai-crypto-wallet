import axios from "axios";
export const api = axios.create({ baseURL: "http://localhost:8000" });
export async function getHealth() { const r = await api.get("/v1/health"); return r.data; }
