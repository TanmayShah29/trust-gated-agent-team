from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..chain.models import TrustScore


class TrustScoreManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_pass(self, run_id: UUID, agent_id: str):
        result = await self.session.execute(
            select(TrustScore).where(
                TrustScore.run_id == run_id,
                TrustScore.agent_id == agent_id,
            )
        )
        score = result.scalar_one_or_none()

        if score:
            score.total_outputs += 1
            score.passed_outputs += 1
            score.trust_ratio = score.passed_outputs / score.total_outputs if score.total_outputs > 0 else 1.0
        else:
            score = TrustScore(
                run_id=run_id,
                agent_id=agent_id,
                total_outputs=1,
                passed_outputs=1,
                rejected_outputs=0,
                trust_ratio=1.0,
            )
            self.session.add(score)
        await self.session.flush()

    async def record_rejection(self, run_id: UUID, agent_id: str):
        result = await self.session.execute(
            select(TrustScore).where(
                TrustScore.run_id == run_id,
                TrustScore.agent_id == agent_id,
            )
        )
        score = result.scalar_one_or_none()

        if score:
            score.total_outputs += 1
            score.rejected_outputs += 1
            score.trust_ratio = score.passed_outputs / score.total_outputs if score.total_outputs > 0 else 0.0
        else:
            score = TrustScore(
                run_id=run_id,
                agent_id=agent_id,
                total_outputs=1,
                passed_outputs=0,
                rejected_outputs=1,
                trust_ratio=0.0,
            )
            self.session.add(score)
        await self.session.flush()

    async def get_scores(self, run_id: UUID) -> dict[str, dict]:
        result = await self.session.execute(
            select(TrustScore).where(TrustScore.run_id == run_id)
        )
        scores = {s.agent_id: {
            "total": s.total_outputs,
            "passed": s.passed_outputs,
            "rejected": s.rejected_outputs,
            "ratio": round(s.trust_ratio, 2),
        } for s in result.scalars().all()}
        return scores
