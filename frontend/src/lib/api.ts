const API_BASE = "/api";

export interface ChainEntry {
  id: string;
  run_id: string;
  agent_id: string;
  action: string;
  input_hash: string;
  output_hash: string | null;
  prev_entry_hash: string | null;
  entry_hash: string;
  timestamp: string;
  sequence_num: number;
  input_data: string;
  output_data: string | null;
}

export interface VerifyResult {
  is_valid: boolean;
  total_entries: number;
  valid_entries: number;
  broken_at_entry: string | null;
  broken_at_sequence: number | null;
  details: string;
}

export interface TrustScore {
  agent_id: string;
  total: number;
  passed: number;
  rejected: number;
  ratio: number;
}

export interface RunResult {
  run_id: string;
  final_output: string;
  chain_entries: { id: string; agent_id: string; action: string; sequence: number; entry_hash: string }[];
  trust_scores: Record<string, { total: number; passed: number; rejected: number; ratio: number }>;
}

export interface AuditReport {
  run_id: string;
  task: string;
  created_at: string;
  chain_entries: ChainEntry[];
  verification: VerifyResult;
  trust_scores: Record<string, TrustScore>;
  summary: string;
}

export async function runResearch(task: string): Promise<RunResult> {
  const res = await fetch(`${API_BASE}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task }),
  });
  if (!res.ok) throw new Error(`Run failed: ${res.statusText}`);
  return res.json();
}

export async function getChain(runId: string): Promise<ChainEntry[]> {
  const res = await fetch(`${API_BASE}/chain/${runId}`);
  if (!res.ok) throw new Error(`Failed to fetch chain`);
  return res.json();
}

export async function verifyChain(runId: string): Promise<VerifyResult> {
  const res = await fetch(`${API_BASE}/chain/${runId}/verify`);
  if (!res.ok) throw new Error(`Verification failed`);
  return res.json();
}

export async function tamperEntry(runId: string, entryId: string) {
  const res = await fetch(`${API_BASE}/chain/${runId}/tamper`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ entry_id: entryId }),
  });
  if (!res.ok) throw new Error(`Tamper failed`);
  return res.json();
}

export async function getTrustScores(runId: string): Promise<Record<string, TrustScore>> {
  const res = await fetch(`${API_BASE}/chain/${runId}/trust-scores`);
  if (!res.ok) throw new Error(`Failed to fetch trust scores`);
  return res.json();
}

export async function getAuditReport(runId: string): Promise<AuditReport> {
  const res = await fetch(`${API_BASE}/chain/${runId}/audit-report`);
  if (!res.ok) throw new Error(`Failed to fetch audit report`);
  return res.json();
}
