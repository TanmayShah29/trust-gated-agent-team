"use client";

interface TrustScore {
  agent_id: string;
  total: number;
  passed: number;
  rejected: number;
  ratio: number;
}

interface Props {
  scores: Record<string, TrustScore>;
}

export default function TrustScores({ scores }: Props) {
  const agents = Object.values(scores);
  if (agents.length === 0) return null;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Trust Score Dashboard</h2>
      <div className="space-y-4">
        {agents.map((agent) => (
          <div key={agent.agent_id} className="flex items-center gap-4">
            <div className="w-24 text-sm font-medium text-gray-700 capitalize">{agent.agent_id}</div>
            <div className="flex-1">
              <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    agent.ratio >= 0.8 ? "bg-green-500" :
                    agent.ratio >= 0.5 ? "bg-yellow-500" :
                    "bg-red-500"
                  }`}
                  style={{ width: `${agent.ratio * 100}%` }}
                />
              </div>
            </div>
            <div className="w-32 text-right text-xs text-gray-500">
              <span className="font-medium text-gray-700">{Math.round(agent.ratio * 100)}%</span>
              {" "}({agent.passed}/{agent.total})
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
