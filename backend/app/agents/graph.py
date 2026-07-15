import asyncio
import json
import logging
import time
from typing import Annotated
from uuid import UUID

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing import TypedDict

from ..config import get_settings
from ..chain.hash_chain import HashChain
from ..chain.models import AgentActionType
from ..trust.policy import run_trust_policies
from ..trust.scores import TrustScoreManager

settings = get_settings()
logger = logging.getLogger(__name__)

RESEARCHER_SYSTEM = """You are a Research Agent on a technical due-diligence team.
Your job is to gather factual information about the given topic.
For EVERY claim you make, you MUST include a source URL or citation.
Structure your findings as a list of facts, each with a source.
Always include at least one URL in your response. Be thorough and accurate.
Keep your response under 500 words."""

ANALYST_SYSTEM = """You are an Analyst Agent on a technical due-diligence team.
You receive research findings and must synthesize them into a structured analysis.
Your analysis MUST include:
1. A summary of key findings
2. An assessment of the findings (strengths, risks, concerns)
3. A conclusion with recommendations
Always reference the sources from the research. Format as structured text.
Keep your response under 500 words."""


class AgentState(TypedDict):
    run_id: str
    task: str
    researcher_output: str
    analyst_output: str
    verified_facts: list[str]
    final_output: str
    chain_entries: list[dict]


_last_call_time = 0.0
_MIN_INTERVAL = 2.5


def _rate_limit():
    global _last_call_time
    now = time.monotonic()
    elapsed = now - _last_call_time
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _last_call_time = time.monotonic()


def make_llm():
    return ChatGroq(
        groq_api_key=settings.groq_api_key,
        model_name=settings.groq_model,
        temperature=0.3,
        max_retries=3,
        request_timeout=30,
    )


def _invoke_llm(llm, messages, retries=4):
    for attempt in range(retries):
        try:
            _rate_limit()
            return llm.invoke(messages)
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                wait = 2 ** (attempt + 2)
                logger.warning(f"Rate limit hit, waiting {wait}s before retry {attempt + 1}/{retries}")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("LLM rate limit exceeded after all retries")


class TrustChainOrchestrator:
    def __init__(self, session, run_id: UUID):
        self.session = session
        self.run_id = run_id
        self.chain = HashChain(session)
        self.scores = TrustScoreManager(session)
        self.verified_facts: list[str] = []
        self.chain_entries: list[dict] = []

    async def log_action(self, agent_id: str, action: AgentActionType, input_data: str, output_data: str = None):
        entry = await self.chain.append_entry(
            run_id=self.run_id,
            agent_id=agent_id,
            action=action,
            input_data=input_data,
            output_data=output_data,
        )
        entry_dict = {
            "id": str(entry.id),
            "agent_id": agent_id,
            "action": action.value,
            "sequence": entry.sequence_num,
            "entry_hash": entry.entry_hash,
        }
        self.chain_entries.append(entry_dict)
        return entry

    async def verify_and_gate(self, agent_id: str, output: str) -> tuple[bool, str]:
        passed, results = run_trust_policies(output, agent_id, self.verified_facts)
        if passed:
            await self.scores.record_pass(self.run_id, agent_id)
            return True, output

        reasons = [r.reason for r in results if not r.passed]
        rejection_msg = f"VERDICT: FAIL — {'; '.join(reasons)}"
        await self.scores.record_rejection(self.run_id, agent_id)
        await self.log_action(
            agent_id="verifier",
            action=AgentActionType.REJECT,
            input_data=output,
            output_data=rejection_msg,
        )
        return False, rejection_msg

    def build_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node("researcher", self._researcher_node)
        graph.add_node("verify_research", self._verify_research_node)
        graph.add_node("analyst", self._analyst_node)
        graph.add_node("verify_analysis", self._verify_analysis_node)
        graph.add_node("finalize", self._finalize_node)

        graph.set_entry_point("researcher")
        graph.add_edge("researcher", "verify_research")
        graph.add_conditional_edges(
            "verify_research",
            self._route_after_research,
            {"analyst": "analyst", "finalize": "finalize"},
        )
        graph.add_edge("analyst", "verify_analysis")
        graph.add_conditional_edges(
            "verify_analysis",
            self._route_after_analysis,
            {"finalize": "finalize", "retry_researcher": "researcher"},
        )
        graph.add_edge("finalize", END)
        return graph.compile()

    async def _researcher_node(self, state: AgentState) -> dict:
        task = state.get("task", "")

        await self.log_action(
            agent_id="supervisor",
            action=AgentActionType.PLAN,
            input_data=task,
            output_data="Assigned to researcher",
        )

        await self.log_action(
            agent_id="researcher",
            action=AgentActionType.SEARCH,
            input_data=task,
        )

        llm = make_llm()
        prompt = f"""Research the following topic for a technical due-diligence report:

{task}

Provide 3-5 factual findings. EACH finding MUST include a source URL.
Format: numbered list, each item ending with (Source: URL)"""

        response = await asyncio.to_thread(
            _invoke_llm, llm,
            [SystemMessage(content=RESEARCHER_SYSTEM), HumanMessage(content=prompt)]
        )
        output = response.content

        await self.log_action(
            agent_id="researcher",
            action=AgentActionType.SEARCH,
            input_data=task,
            output_data=output[:2000],
        )

        for line in output.split("\n"):
            if line.strip() and len(line.strip()) > 20:
                self.verified_facts.append(line.strip())

        return {
            "researcher_output": output,
            "verified_facts": self.verified_facts,
        }

    async def _verify_research_node(self, state: AgentState) -> dict:
        output = state.get("researcher_output", "")
        passed, _ = await self.verify_and_gate("researcher", output)

        if passed:
            return {"analyst_output": state.get("analyst_output", "")}

        return {"researcher_output": "", "analyst_output": ""}

    async def _analyst_node(self, state: AgentState) -> dict:
        researcher_output = state.get("researcher_output", "")

        await self.log_action(
            agent_id="supervisor",
            action=AgentActionType.PLAN,
            input_data=researcher_output[:200],
            output_data="Assigned to analyst",
        )

        await self.log_action(
            agent_id="analyst",
            action=AgentActionType.ANALYZE,
            input_data=researcher_output[:2000],
        )

        llm = make_llm()
        prompt = f"""Based on the following research findings, provide a structured analysis
for a technical due-diligence report:

{researcher_output}

Include: Key Findings, Risk Assessment, and Recommendations.
Always reference sources. Keep under 500 words."""

        response = await asyncio.to_thread(
            _invoke_llm, llm,
            [SystemMessage(content=ANALYST_SYSTEM), HumanMessage(content=prompt)]
        )
        output = response.content

        await self.log_action(
            agent_id="analyst",
            action=AgentActionType.ANALYZE,
            input_data=researcher_output[:2000],
            output_data=output[:2000],
        )

        return {"analyst_output": output}

    async def _verify_analysis_node(self, state: AgentState) -> dict:
        output = state.get("analyst_output", "")
        passed, _ = await self.verify_and_gate("analyst", output)

        if passed:
            return {"final_output": output}

        return {"analyst_output": "", "final_output": ""}

    async def _finalize_node(self, state: AgentState) -> dict:
        final = state.get("final_output", "") or state.get("analyst_output", "") or state.get("researcher_output", "")

        await self.log_action(
            agent_id="supervisor",
            action=AgentActionType.FINALIZE,
            input_data="Finalizing",
            output_data=final[:2000],
        )

        return {"final_output": final}

    def _route_after_research(self, state: AgentState) -> str:
        if state.get("analyst_output") == "" and state.get("researcher_output"):
            return "finalize"
        return "analyst"

    def _route_after_analysis(self, state: AgentState) -> str:
        if state.get("final_output"):
            return "finalize"
        return "retry_researcher"
