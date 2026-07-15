import AgentChat from "@/components/AgentChat";

export default function Home() {
  return (
    <div>
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900">Multi-Agent Research Team</h2>
        <p className="text-gray-600 mt-1">
          Submit a technical due-diligence task. Our agent team will research, analyze, and verify findings — every action cryptographically logged.
        </p>
      </div>
      <AgentChat />
    </div>
  );
}
