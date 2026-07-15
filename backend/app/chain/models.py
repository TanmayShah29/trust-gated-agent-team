import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, Float, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship
import enum


class Base(DeclarativeBase):
    pass


class AgentActionType(str, enum.Enum):
    PLAN = "plan"
    SEARCH = "search"
    ANALYZE = "analyze"
    VERIFY = "verify"
    REJECT = "reject"
    RETRY = "retry"
    FINALIZE = "finalize"


class ChainEntry(Base):
    __tablename__ = "chain_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    agent_id = Column(String(100), nullable=False)
    action = Column(SAEnum(AgentActionType), nullable=False)
    input_data = Column(Text, nullable=False)
    output_data = Column(Text, nullable=True)
    input_hash = Column(String(64), nullable=False)
    output_hash = Column(String(64), nullable=True)
    prev_entry_hash = Column(String(64), nullable=True)
    entry_hash = Column(String(64), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    sequence_num = Column(Integer, nullable=False, default=0)
    metadata_json = Column(Text, nullable=True)


class TrustScore(Base):
    __tablename__ = "trust_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    agent_id = Column(String(100), nullable=False)
    total_outputs = Column(Integer, default=0)
    passed_outputs = Column(Integer, default=0)
    rejected_outputs = Column(Integer, default=0)
    trust_ratio = Column(Float, default=1.0)


class VerificationResult(Base):
    __tablename__ = "verification_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    is_valid = Column(Integer, nullable=False)
    total_entries = Column(Integer, nullable=False)
    valid_entries = Column(Integer, nullable=False)
    broken_at_entry = Column(UUID(as_uuid=True), nullable=True)
    broken_at_sequence = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    verified_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
