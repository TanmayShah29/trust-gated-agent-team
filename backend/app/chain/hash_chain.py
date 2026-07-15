import hashlib
import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import ChainEntry, AgentActionType


def compute_hash(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def compute_entry_hash(
    agent_id: str,
    action: str,
    input_hash: str,
    output_hash: Optional[str],
    timestamp: str,
    prev_entry_hash: Optional[str],
    sequence_num: int,
) -> str:
    payload = json.dumps(
        {
            "agent_id": agent_id,
            "action": action,
            "input_hash": input_hash,
            "output_hash": output_hash or "",
            "timestamp": timestamp,
            "prev_entry_hash": prev_entry_hash or "",
            "sequence_num": sequence_num,
        },
        sort_keys=True,
    )
    return compute_hash(payload)


class HashChain:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_last_entry(self, run_id: UUID) -> Optional[ChainEntry]:
        result = await self.session.execute(
            select(ChainEntry)
            .where(ChainEntry.run_id == run_id)
            .order_by(ChainEntry.sequence_num.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def append_entry(
        self,
        run_id: UUID,
        agent_id: str,
        action: AgentActionType,
        input_data: str,
        output_data: Optional[str] = None,
        metadata_json: Optional[str] = None,
    ) -> ChainEntry:
        last_entry = await self.get_last_entry(run_id)

        sequence_num = (last_entry.sequence_num + 1) if last_entry else 0
        prev_hash = last_entry.entry_hash if last_entry else None

        input_hash = compute_hash(input_data)
        output_hash = compute_hash(output_data) if output_data else None
        timestamp = datetime.now(timezone.utc).isoformat()

        entry_hash = compute_entry_hash(
            agent_id=agent_id,
            action=action.value,
            input_hash=input_hash,
            output_hash=output_hash,
            timestamp=timestamp,
            prev_entry_hash=prev_hash,
            sequence_num=sequence_num,
        )

        entry = ChainEntry(
            id=uuid4(),
            run_id=run_id,
            agent_id=agent_id,
            action=action,
            input_data=input_data,
            output_data=output_data,
            input_hash=input_hash,
            output_hash=output_hash,
            prev_entry_hash=prev_hash,
            entry_hash=entry_hash,
            timestamp=datetime.fromisoformat(timestamp),
            sequence_num=sequence_num,
            metadata_json=metadata_json,
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def verify_chain(self, run_id: UUID) -> dict:
        result = await self.session.execute(
            select(ChainEntry)
            .where(ChainEntry.run_id == run_id)
            .order_by(ChainEntry.sequence_num.asc())
        )
        entries = list(result.scalars().all())

        if not entries:
            return {
                "is_valid": True,
                "total_entries": 0,
                "valid_entries": 0,
                "broken_at_entry": None,
                "broken_at_sequence": None,
                "details": "No entries to verify",
            }

        prev_hash = None
        valid_count = 0

        for entry in entries:
            expected_hash = compute_entry_hash(
                agent_id=entry.agent_id,
                action=entry.action.value,
                input_hash=entry.input_hash,
                output_hash=entry.output_hash,
                timestamp=entry.timestamp.isoformat(),
                prev_entry_hash=prev_hash,
                sequence_num=entry.sequence_num,
            )

            hash_match = expected_hash == entry.entry_hash
            prev_chain_match = entry.prev_entry_hash == prev_hash

            if hash_match and prev_chain_match:
                valid_count += 1
            else:
                return {
                    "is_valid": False,
                    "total_entries": len(entries),
                    "valid_entries": valid_count,
                    "broken_at_entry": str(entry.id),
                    "broken_at_sequence": entry.sequence_num,
                    "details": json.dumps(
                        {
                            "entry_id": str(entry.id),
                            "sequence": entry.sequence_num,
                            "agent_id": entry.agent_id,
                            "hash_match": hash_match,
                            "prev_chain_match": prev_chain_match,
                            "expected_hash": expected_hash,
                            "actual_hash": entry.entry_hash,
                            "expected_prev": prev_hash,
                            "actual_prev": entry.prev_entry_hash,
                        }
                    ),
                }

            prev_hash = entry.entry_hash

        return {
            "is_valid": True,
            "total_entries": len(entries),
            "valid_entries": valid_count,
            "broken_at_entry": None,
            "broken_at_sequence": None,
            "details": "Chain integrity verified — all entries valid",
        }

    async def tamper_entry(self, entry_id: UUID) -> Optional[ChainEntry]:
        result = await self.session.execute(
            select(ChainEntry).where(ChainEntry.id == entry_id)
        )
        entry = result.scalar_one_or_none()
        if not entry:
            return None

        entry.output_hash = compute_hash("TAMPERED_DATA_" + str(entry.id))
        await self.session.flush()
        return entry
