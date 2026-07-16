"""Unit tests for backend — hash chain integrity."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


class TestHashChain:
    def test_compute_hash_deterministic(self):
        from app.chain.hash_chain import compute_hash
        h1 = compute_hash("test data")
        h2 = compute_hash("test data")
        assert h1 == h2

    def test_different_inputs_different_hashes(self):
        from app.chain.hash_chain import compute_hash
        h1 = compute_hash("data1")
        h2 = compute_hash("data2")
        assert h1 != h2

    def test_hash_is_hex_64(self):
        from app.chain.hash_chain import compute_hash
        h = compute_hash("test")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_compute_entry_hash_deterministic(self):
        from app.chain.hash_chain import compute_entry_hash
        h1 = compute_entry_hash(
            agent_id="researcher",
            action="research",
            input_hash="abc123",
            output_hash="def456",
            timestamp="2024-01-01T00:00:00Z",
            prev_entry_hash=None,
            sequence_num=0,
        )
        h2 = compute_entry_hash(
            agent_id="researcher",
            action="research",
            input_hash="abc123",
            output_hash="def456",
            timestamp="2024-01-01T00:00:00Z",
            prev_entry_hash=None,
            sequence_num=0,
        )
        assert h1 == h2

    def test_entry_hash_changes_with_sequence(self):
        from app.chain.hash_chain import compute_entry_hash
        h1 = compute_entry_hash(
            agent_id="researcher",
            action="research",
            input_hash="abc",
            output_hash="def",
            timestamp="2024-01-01T00:00:00Z",
            prev_entry_hash=None,
            sequence_num=0,
        )
        h2 = compute_entry_hash(
            agent_id="researcher",
            action="research",
            input_hash="abc",
            output_hash="def",
            timestamp="2024-01-01T00:00:00Z",
            prev_entry_hash=None,
            sequence_num=1,
        )
        assert h1 != h2
