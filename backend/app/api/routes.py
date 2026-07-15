import json
from uuid import UUID, uuid4
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..chain.database import get_session
from ..chain.hash_chain import HashChain
from ..chain.models import ChainEntry, VerificationResult
from ..trust.scores import TrustScoreManager
from ..agents.graph import TrustChainOrchestrator
from .schemas import (
    RunRequest, RunResponse, VerifyResponse, ChainEntryResponse,
    TrustScoreResponse, AuditReport, TamperRequest,
)

router = APIRouter()


@router.post("/run", response_model=RunResponse)
async def run_research(request: RunRequest, session: AsyncSession = Depends(get_session)):
    run_id = UUID(request.run_id) if request.run_id else uuid4()

    orchestrator = TrustChainOrchestrator(session, run_id)
    graph = orchestrator.build_graph()

    initial_state = {
        "messages": [],
        "run_id": str(run_id),
        "task": request.task,
        "current_agent": "",
        "researcher_output": "",
        "analyst_output": "",
        "verified_facts": [],
        "attempts": 0,
        "final_output": "",
        "chain_entries": [],
    }

    try:
        result = await graph.ainvoke(initial_state)
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")

    await session.commit()

    scores_manager = TrustScoreManager(session)
    trust_scores = await scores_manager.get_scores(run_id)

    return RunResponse(
        run_id=str(run_id),
        final_output=result.get("final_output", "No output produced"),
        chain_entries=orchestrator.chain_entries,
        trust_scores=trust_scores,
    )


@router.get("/chain/{run_id}", response_model=list[ChainEntryResponse])
async def get_chain(run_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(ChainEntry)
        .where(ChainEntry.run_id == UUID(run_id))
        .order_by(ChainEntry.sequence_num.asc())
    )
    entries = result.scalars().all()

    return [
        ChainEntryResponse(
            id=str(e.id),
            run_id=str(e.run_id),
            agent_id=e.agent_id,
            action=e.action.value,
            input_hash=e.input_hash,
            output_hash=e.output_hash,
            prev_entry_hash=e.prev_entry_hash,
            entry_hash=e.entry_hash,
            timestamp=e.timestamp.isoformat(),
            sequence_num=e.sequence_num,
            input_data=e.input_data,
            output_data=e.output_data,
        )
        for e in entries
    ]


@router.get("/chain/{run_id}/verify", response_model=VerifyResponse)
async def verify_chain(run_id: str, session: AsyncSession = Depends(get_session)):
    chain = HashChain(session)
    result = await chain.verify_chain(UUID(run_id))

    vr = VerificationResult(
        run_id=UUID(run_id),
        is_valid=1 if result["is_valid"] else 0,
        total_entries=result["total_entries"],
        valid_entries=result["valid_entries"],
        broken_at_entry=UUID(result["broken_at_entry"]) if result["broken_at_entry"] else None,
        broken_at_sequence=result["broken_at_sequence"],
        details=result["details"],
    )
    session.add(vr)
    await session.commit()

    return VerifyResponse(**result)


@router.post("/chain/{run_id}/tamper")
async def tamper_entry(run_id: str, request: TamperRequest, session: AsyncSession = Depends(get_session)):
    chain = HashChain(session)
    entry = await chain.tamper_entry(UUID(request.entry_id))

    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    await session.commit()

    verification = await chain.verify_chain(UUID(run_id))

    return {
        "message": f"Entry {request.entry_id} tampered",
        "tampered_entry_id": request.entry_id,
        "verification_after_tamper": verification,
    }


@router.get("/chain/{run_id}/trust-scores")
async def get_trust_scores(run_id: str, session: AsyncSession = Depends(get_session)):
    manager = TrustScoreManager(session)
    scores = await manager.get_scores(UUID(run_id))
    return scores


@router.get("/chain/{run_id}/audit-report")
async def get_audit_report(run_id: str, session: AsyncSession = Depends(get_session)):
    chain = HashChain(session)
    verification = await chain.verify_chain(UUID(run_id))

    entries_result = await session.execute(
        select(ChainEntry)
        .where(ChainEntry.run_id == UUID(run_id))
        .order_by(ChainEntry.sequence_num.asc())
    )
    entries = entries_result.scalars().all()

    manager = TrustScoreManager(session)
    trust_scores = await manager.get_scores(UUID(run_id))

    report = AuditReport(
        run_id=run_id,
        task=entries[0].input_data if entries else "Unknown",
        created_at=entries[0].timestamp.isoformat() if entries else datetime.now(timezone.utc).isoformat(),
        chain_entries=[
            ChainEntryResponse(
                id=str(e.id),
                run_id=str(e.run_id),
                agent_id=e.agent_id,
                action=e.action.value,
                input_hash=e.input_hash,
                output_hash=e.output_hash,
                prev_entry_hash=e.prev_entry_hash,
                entry_hash=e.entry_hash,
                timestamp=e.timestamp.isoformat(),
                sequence_num=e.sequence_num,
                input_data=e.input_data,
                output_data=e.output_data,
            )
            for e in entries
        ],
        verification=VerifyResponse(**verification),
        trust_scores={k: TrustScoreResponse(agent_id=k, **v) for k, v in trust_scores.items()},
        summary=f"Run {run_id}: {'VALID' if verification['is_valid'] else 'TAMPERED'} — "
                f"{verification['total_entries']} entries, "
                f"{verification['valid_entries']} verified",
    )

    return report
