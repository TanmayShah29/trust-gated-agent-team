"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { ChainEntry, getChain, getAuditReport, AuditReport } from "@/lib/api";
import ChainViewer from "@/components/ChainViewer";
import TrustScores from "@/components/TrustScores";

export default function AuditPage() {
  const searchParams = useSearchParams();
  const runId = searchParams.get("runId") || "";

  const [entries, setEntries] = useState<ChainEntry[]>([]);
  const [report, setReport] = useState<AuditReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [inputRunId, setInputRunId] = useState(runId);

  const fetchData = async (rid: string) => {
    if (!rid) return;
    setLoading(true);
    setError(null);
    try {
      const [chainData, reportData] = await Promise.all([
        getChain(rid),
        getAuditReport(rid),
      ]);
      setEntries(chainData);
      setReport(reportData);
    } catch (err: any) {
      const msg = err?.message || "Failed to load data";
      if (msg.includes("Failed to fetch")) {
        setError("Cannot connect to backend. Make sure the server is running on port 8001.");
      } else {
        setError(`No data found for run ID: ${rid}`);
      }
      setEntries([]);
      setReport(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (runId) fetchData(runId);
  }, [runId]);

  const handleLoad = () => {
    if (inputRunId) fetchData(inputRunId);
  };

  const handleDownloadReport = () => {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `trustchain-audit-${report.run_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-2xl font-bold text-gray-900">Audit Trail Viewer</h2>
        <p className="text-gray-600 mt-1">Enter a run ID to inspect the cryptographic hash chain.</p>

        <div className="flex gap-3 mt-4">
          <input
            value={inputRunId}
            onChange={(e) => setInputRunId(e.target.value)}
            placeholder="Run ID"
            className="flex-1 rounded-lg border border-gray-300 px-4 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <button
            onClick={handleLoad}
            disabled={loading || !inputRunId}
            className="bg-indigo-600 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            {loading ? "Loading..." : "Load Chain"}
          </button>
          {report && (
            <button
              onClick={handleDownloadReport}
              className="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Download Report
            </button>
          )}
        </div>

        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
            {error}
          </div>
        )}
      </div>

      {entries.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 p-6">
            <ChainViewer entries={entries} runId={inputRunId} onRefresh={() => fetchData(inputRunId)} />
          </div>
          <div className="space-y-6">
            {report && <TrustScores scores={report.trust_scores} />}
            {report && (
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Summary</h3>
                <p className="text-sm text-gray-600">{report.summary}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
