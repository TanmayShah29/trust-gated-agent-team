"use client";

import { useState } from "react";
import { ChainEntry, verifyChain, tamperEntry, VerifyResult } from "@/lib/api";

interface Props {
  entries: ChainEntry[];
  runId: string;
  onRefresh: () => void;
}

const ACTION_ICONS: Record<string, string> = {
  plan: "📋",
  search: "🔍",
  analyze: "📊",
  verify: "✅",
  reject: "❌",
  retry: "🔄",
  finalize: "🏁",
};

export default function ChainViewer({ entries, runId, onRefresh }: Props) {
  const [verification, setVerification] = useState<VerifyResult | null>(null);
  const [selectedEntry, setSelectedEntry] = useState<string | null>(null);
  const [tampering, setTampering] = useState<string | null>(null);

  const handleVerify = async () => {
    try {
      const result = await verifyChain(runId);
      setVerification(result);
    } catch (err) {
      console.error(err);
    }
  };

  const handleTamper = async (entryId: string) => {
    setTampering(entryId);
    try {
      await tamperEntry(runId, entryId);
      const result = await verifyChain(runId);
      setVerification(result);
      onRefresh();
    } catch (err) {
      console.error(err);
    } finally {
      setTampering(null);
    }
  };

  const isBroken = (seq: number): boolean => {
    if (!verification || verification.is_valid) return false;
    return seq >= (verification.broken_at_sequence ?? Infinity);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-700">Hash Chain ({entries.length} entries)</h3>
        <div className="flex gap-2">
          <button
            onClick={handleVerify}
            className="bg-emerald-600 text-white px-4 py-2 rounded-lg text-xs font-medium hover:bg-emerald-700 transition-colors"
          >
            Verify Chain
          </button>
        </div>
      </div>

      {verification && (
        <div className={`rounded-lg p-4 text-sm ${
          verification.is_valid
            ? "bg-green-50 border border-green-200 text-green-800"
            : "bg-red-50 border border-red-200 text-red-800"
        }`}>
          <div className="font-semibold mb-1">
            {verification.is_valid ? "Chain Valid" : "Chain BROKEN"}
          </div>
          <p className="text-xs">
            {verification.valid_entries}/{verification.total_entries} entries verified
          </p>
          {!verification.is_valid && (
            <p className="text-xs mt-1">
              Broken at sequence #{verification.broken_at_sequence}
            </p>
          )}
        </div>
      )}

      <div className="space-y-2">
        {entries.map((entry) => {
          const broken = isBroken(entry.sequence_num);
          const selected = selectedEntry === entry.id;

          return (
            <div
              key={entry.id}
              className={`rounded-lg border p-3 cursor-pointer transition-all ${
                broken
                  ? "border-red-300 bg-red-50"
                  : selected
                  ? "border-indigo-300 bg-indigo-50"
                  : "border-gray-200 bg-white hover:border-gray-300"
              }`}
              onClick={() => setSelectedEntry(selected ? null : entry.id)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm">{ACTION_ICONS[entry.action] || "📌"}</span>
                  <span className="text-xs font-medium text-gray-700 capitalize">{entry.agent_id}</span>
                  <span className="text-xs text-gray-400">#{entry.sequence_num}</span>
                  <span className="text-xs text-gray-500">{entry.action}</span>
                </div>
                <div className="flex items-center gap-2">
                  {broken && <span className="text-xs text-red-500 font-medium">BROKEN</span>}
                  <button
                    onClick={(e) => { e.stopPropagation(); handleTamper(entry.id); }}
                    disabled={tampering === entry.id}
                    className="text-xs text-red-600 hover:text-red-700 font-medium disabled:opacity-50"
                  >
                    {tampering === entry.id ? "..." : "Tamper"}
                  </button>
                </div>
              </div>

              {selected && (
                <div className="mt-3 space-y-2 text-xs">
                  <div>
                    <span className="font-medium text-gray-600">Entry Hash:</span>
                    <p className="font-mono text-gray-500 break-all bg-gray-100 rounded px-2 py-1 mt-1">{entry.entry_hash}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-600">Input Hash:</span>
                    <p className="font-mono text-gray-500 break-all bg-gray-100 rounded px-2 py-1 mt-1">{entry.input_hash}</p>
                  </div>
                  {entry.output_hash && (
                    <div>
                      <span className="font-medium text-gray-600">Output Hash:</span>
                      <p className="font-mono text-gray-500 break-all bg-gray-100 rounded px-2 py-1 mt-1">{entry.output_hash}</p>
                    </div>
                  )}
                  <div>
                    <span className="font-medium text-gray-600">Prev Hash:</span>
                    <p className="font-mono text-gray-500 break-all bg-gray-100 rounded px-2 py-1 mt-1">
                      {entry.prev_entry_hash || "GENESIS"}
                    </p>
                  </div>
                  {entry.output_data && (
                    <div>
                      <span className="font-medium text-gray-600">Output:</span>
                      <p className="text-gray-600 bg-gray-100 rounded px-2 py-1 mt-1 whitespace-pre-wrap max-h-40 overflow-auto">
                        {entry.output_data}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
