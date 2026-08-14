import type {
  AppConfig,
  CustomerLookupResponse,
  CustomerOption,
  ScoreResponse,
} from "./types";

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data.detail === "string") return data.detail;
    return JSON.stringify(data.detail ?? data);
  } catch {
    return res.statusText || "Request failed";
  }
}

export async function fetchConfig(): Promise<AppConfig> {
  const res = await fetch("/api/config");
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function scoreChurn(body: Record<string, unknown>): Promise<ScoreResponse> {
  const res = await fetch("/api/score/churn", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function scoreDeposit(body: Record<string, unknown>): Promise<ScoreResponse> {
  const res = await fetch("/api/score/deposit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function scoreFraud(body: Record<string, unknown>): Promise<ScoreResponse> {
  const res = await fetch("/api/score/fraud", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function lookupCustomer(customerId: string): Promise<CustomerLookupResponse> {
  const res = await fetch(`/api/lookup/${encodeURIComponent(customerId)}`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function fetchCustomerOptions(): Promise<CustomerOption[]> {
  const res = await fetch("/api/lookup/options");
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}
