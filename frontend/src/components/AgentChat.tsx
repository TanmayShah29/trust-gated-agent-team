"use client";

import { useState } from "react";
import { runResearch, RunResult } from "@/lib/api";

const AGENT_COLORS: Record<string, string> = {
  supervisor: "bg-purple-100 text-purple-800 border-purple-200",
  researcher: "bg-blue-100 text-blue-800 border-blue-200",
  analyst: "bg-green-100 text-green-800 border-green-200",
  verifier: "bg-amber-100 text-amber-800 border-amber-200",
};

export default function AgentChat() {
  const [task, setTask] = useState("");
  const [result, setResult] = useState<RunResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleRun = async () => {
    if (!task.trim()) return;
    setLoading(true);
    try {
      const res = await runResearch(task);
      setResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Research Task</h2>
        <div className="flex gap-3">
          <textarea
            value={task}
            onChange={(e) => setTask(e.target.value)}
            placeholder="Enter a technical due-diligence research task..."
            className="flex-1 rounded-lg border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
            rows={3}
          />
          <button
            onClick={handleRun}
            disabled={loading || !task.trim()}
            className="bg-indigo-600 text-white px-6 py-3 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed self-end transition-colors"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Running...
              </span>
            ) : (
              "Run Agents"
            )}
          </button>
        </div>
      </div>

      {result && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Agent Handoffs</h2>
              <a
                href={`/audit?runId=${result.run_id}`}
                className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
              >
                View Audit Trail →
              </a>
            </div>
            <div className="space-y-3">
              {result.chain_entries.map((entry, i) => (
                <div key={i} className="flex items-start gap-3">
                  <div className="flex flex-col items-center">
                    <div className="w-3 h-3 rounded-full bg-indigo-500 mt-1.5" />
                    {i < result.chain_entries.length - 1 && <div className="w-0.5 h-8 bg-gray-200" />}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${AGENT_COLORS[entry.agent_id] || "bg-gray-100"}`}>
                        {entry.agent_id}
                      </span>
                      <span className="text-xs text-gray-500">#{entry.sequence}</span>
                      <span className="text-xs text-gray-400">{entry.action}</span>
                    </div>
                    <p className="text-sm text-gray-600 font-mono text-xs break-all">{entry.entry_hash.substring(0, 32)}...</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Final Output</h2>
            <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap">
              {result.final_output}
            </div>
          </div>

          {Object.keys(result.trust_scores).length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Trust Scores</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(result.trust_scores).map(([agent, scores]) => (
                  <div key={agent} className="text-center">
                    <div className={`inline-flex items-center justify-center w-12 h-12 rounded-full text-lg font-bold ${
                      scores.ratio >= 0.8 ? "bg-green-100 text-green-700" :
                      scores.ratio >= 0.5 ? "bg-yellow-100 text-yellow-700" :
                      "bg-red-100 text-red-700"
                    }`}>
                      {Math.round(scores.ratio * 100)}%
                    </div>
                    <p className="text-xs font-medium text-gray-600 mt-2 capitalize">{agent}</p>
                    <p className="text-xs text-gray-400">{scores.passed}/{scores.total} passed</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
