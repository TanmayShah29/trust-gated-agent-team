# TrustChain — Trust-Gated Multi-Agent Research Team

A multi-agent research system where specialized agents collaborate on technical due-diligence tasks, and every single agent action is cryptographically logged in a hash-chained audit trail — so any action can be verified as tamper-free after the fact.

## Architecture

### Agent Graph

```
                    ┌──────────────┐
                    │  User Input  │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  Supervisor  │◄──────────────────┐
                    │   (Router)   │                   │
                    └──────┬───────┘                   │
                           │                           │
              ┌────────────┼────────────┐              │
              ▼            ▼            ▼              │
       ┌────────────┐ ┌──────────┐ ┌──────────┐       │
       │ Researcher │ │ Analyst  │ │  DONE    │───────┘
       │   (Web)    │ │(Synth.)  │ │(Output)  │
       └─────┬──────┘ └────┬─────┘ └──────────┘
             │              │
             ▼              ▼
       ┌─────────────────────────┐
       │    Verifier (Trust)     │
       │  Checks: citation,      │
       │  schema, contradictions │
       └──────────┬──────────────┘
                  │
         ┌────────┴────────┐
         │                 │
         ▼                 ▼
    ┌─────────┐      ┌──────────┐
    │  PASS   │      │   FAIL   │
    │ → next  │      │ → retry  │
    └─────────┘      └──────────┘
```

### Hash Chain Structure

```
┌─────────────────────────────────────────────────────────────┐
│                      HASH CHAIN                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Entry 0 (Genesis)                                          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ agent_id: supervisor                                │    │
│  │ action: plan                                        │    │
│  │ input_hash: SHA256(input)                           │    │
│  │ output_hash: SHA256(output)                         │    │
│  │ prev_entry_hash: None                               │    │
│  │ entry_hash: SHA256(all fields above)                │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │                                   │
│                         ▼                                   │
│  Entry 1                                                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ agent_id: researcher                                │    │
│  │ action: search                                      │    │
│  │ input_hash: SHA256(input)                           │    │
│  │ output_hash: SHA256(output)                         │    │
│  │ prev_entry_hash: SHA256(entry_0) ──────────────┐    │    │
│  │ entry_hash: SHA256(all fields above)            │    │    │
│  └──────────────────────┬─────────────────────────┼────┘    │
│                         │                          │         │
│                         ▼                          │         │
│  Entry 2                                            │         │
│  ┌─────────────────────────────────────────────┐   │         │
│  │ agent_id: verifier                          │   │         │
│  │ action: verify                              │   │         │
│  │ prev_entry_hash: SHA256(entry_1) ───────┐  │   │         │
│  │ entry_hash: SHA256(all fields above)     │  │   │         │
│  └──────────────────────────────────────────┼──┼───┘         │
│                                             │  │             │
│  Each entry's prev_entry_hash points to ────┘  │             │
│  the previous entry's entry_hash, forming ─────┘             │
│  an unbreakable chain.                                       │
│                                                              │
│  Tamper Detection:                                           │
│  If Entry 1 is modified → its entry_hash changes →           │
│  Entry 2's prev_entry_hash no longer matches →               │
│  Chain is BROKEN from Entry 2 onward.                        │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python, FastAPI |
| Agent Orchestration | LangGraph |
| LLM | Groq + Llama 3.3 |
| Audit Trail | Custom SHA256 hash chain |
| Database | PostgreSQL |
| Frontend | Next.js, TypeScript, TailwindCSS |
| Deployment | Docker Compose |

## Agent Team

| Agent | Role | Trust Policies |
|-------|------|----------------|
| **Supervisor** | Routes tasks, decides when done | Schema check |
| **Researcher** | Gathers facts with citations | Citation required, schema check |
| **Analyst** | Synthesizes findings | Citation required, schema check |
| **Verifier** | Validates all outputs | Rule-based policy enforcement |

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Groq API key (free at console.groq.com)

### 1. Clone & Configure

```bash
git clone https://github.com/TanmayShah29/trust-gated-agent-team.git
cd trust-gated-agent-team
cp backend/.env.example backend/.env
# Edit backend/.env and add your GROQ_API_KEY
```

### 2. Start Backend

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`

### 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

The UI will be available at `http://localhost:3000`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/run` | Submit a research task to the agent team |
| `GET` | `/api/chain/{run_id}` | Get all chain entries for a run |
| `GET` | `/api/chain/{run_id}/verify` | Verify chain integrity |
| `POST` | `/api/chain/{run_id}/tamper` | Tamper with an entry (demo) |
| `GET` | `/api/chain/{run_id}/trust-scores` | Get per-agent trust scores |
| `GET` | `/api/chain/{run_id}/audit-report` | Download full audit report |

## Tamper Demo

1. Run a research task via the UI
2. Go to Audit Trail and click "Verify Chain" — all entries valid
3. Click "Tamper" on any entry
4. Click "Verify Chain" again — chain is now broken from that point onward

## Project Structure

```
trust-gated-agent-team/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Settings & environment
│   │   ├── agents/
│   │   │   └── graph.py         # LangGraph orchestrator
│   │   ├── chain/
│   │   │   ├── hash_chain.py    # Core hash chain logic
│   │   │   ├── models.py        # SQLAlchemy models
│   │   │   └── database.py      # DB session management
│   │   ├── trust/
│   │   │   ├── policy.py        # Trust policy rules
│   │   │   └── scores.py        # Trust score tracking
│   │   └── api/
│   │       ├── routes.py        # API endpoints
│   │       └── schemas.py       # Pydantic models
│   ├── alembic/                 # DB migrations
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx         # Research interface
│   │   │   └── audit/page.tsx   # Audit trail viewer
│   │   ├── components/
│   │   │   ├── AgentChat.tsx    # Agent conversation UI
│   │   │   ├── ChainViewer.tsx  # Hash chain visualization
│   │   │   └── TrustScores.tsx  # Trust dashboard
│   │   └── lib/
│   │       └── api.ts           # API client
│   ├── package.json
│   └── tailwind.config.ts
├── docker-compose.yml
└── README.md
```

## License

MIT
