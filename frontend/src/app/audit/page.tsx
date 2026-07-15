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
  const [inputRunId, setInputRunId] = useState(runId);

  const fetchData = async (rid: string) => {
    if (!rid) return;
    setLoading(true);
    try {
      const [chainData, reportData] = await Promise.all([
        getChain(rid),
        getAuditReport(rid),
      ]);
      setEntries(chainData);
      setReport(reportData);
    } catch (err) {
      console.error(err);
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
              className="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
            >
              Download Report
            </button>
          )}
        </div>
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
