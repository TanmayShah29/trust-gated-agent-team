from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class RunRequest(BaseModel):
    task: str = Field(..., description="Research task for the agent team to work on")
    run_id: Optional[str] = Field(None, description="Optional run ID to resume")


class ChainEntryResponse(BaseModel):
    id: str
    run_id: str
    agent_id: str
    action: str
    input_hash: str
    output_hash: Optional[str]
    prev_entry_hash: Optional[str]
    entry_hash: str
    timestamp: str
    sequence_num: int
    input_data: str
    output_data: Optional[str]


class VerifyResponse(BaseModel):
    is_valid: bool
    total_entries: int
    valid_entries: int
    broken_at_entry: Optional[str]
    broken_at_sequence: Optional[int]
    details: str


class TrustScoreResponse(BaseModel):
    agent_id: str
    total: int
    passed: int
    rejected: int
    ratio: float


class RunResponse(BaseModel):
    run_id: str
    final_output: str
    chain_entries: list[dict]
    trust_scores: dict


class AuditReport(BaseModel):
    run_id: str
    task: str
    created_at: str
    chain_entries: list[ChainEntryResponse]
    verification: VerifyResponse
    trust_scores: dict[str, TrustScoreResponse]
    summary: str


class TamperRequest(BaseModel):
    entry_id: str
