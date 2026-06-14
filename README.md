# AI Construction Commander

AI-powered construction project management with multi-database root cause analysis.

Ask "Why is Tower A delayed?" — the agent queries PostgreSQL, Neo4j, and Qdrant in sequence and produces a streaming reasoning trace with evidence for every statement.

## Stack

- **Backend:** FastAPI + LangGraph (ReAct agent) + GPT-4o
- **Databases:** PostgreSQL (pgvector) + Neo4j + Qdrant
- **Frontend:** Next.js 15 + TailwindCSS

## Prerequisites

- Docker + Docker Compose
- Node.js 18+
- Python 3.12+ (only needed to run scripts locally; otherwise handled by Docker)
- OpenAI API key

## Setup

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-your-key-here
```

### 2. Start databases and API

```bash
docker-compose up -d
```

Wait ~15 seconds for all services to pass their health checks:

```bash
docker-compose ps  # all should show (healthy)
```

### 3. Seed data (Phase 1)

```bash
docker-compose exec api python scripts/seed.py
```

Expected output ends with:
```
Tower A status: delayed ✓
Rebar shortage: 320/500 ✓
S-102 delay: 9 days ✓
ABC Steel rating: 2.7 ✓
Building B pending POs: 2 ✓
Seed complete: 32 rows
```

### 4. Sync graph database (Phase 2)

```bash
docker-compose exec api python scripts/sync_graph.py
```

Expected output ends with:
```
Graph traversal: Tower A | Rebar | S-102 | 9 | ABC Steel ✓
```

### 5. Embed documents (Phase 3)

```bash
docker-compose exec api python scripts/embed_docs.py
```

Expected output ends with 3 search verifications all showing `score > 0.70 ✓`.

### 6. Validate tools (Phase 4)

```bash
docker-compose exec api python scripts/validate_tools.py
```

All 6 lines must print `PASS`.

### 7. Start frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

## Demo Queries

On the Agent page (http://localhost:3000/agent):

- **"Why is Tower A delayed?"** — finds ABC Steel quality failure via inspection report
- **"Why is Building B delayed?"** — finds procurement approval bottleneck
- **"Which vendors are high risk?"** — ranks vendors by delay history

See `DEMO.md` for the full demo script and expected outputs.

## Project Structure

```
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── tools.py        # 6 database tools + final_answer
│   │   │   └── rca_agent.py    # LangGraph ReAct agent
│   │   ├── routers/
│   │   │   ├── agent.py        # SSE streaming endpoint
│   │   │   ├── dashboard.py
│   │   │   ├── projects.py
│   │   │   └── vendors.py
│   │   ├── models.py           # 7 SQLAlchemy models
│   │   ├── database.py         # PG + Neo4j + Qdrant connections
│   │   └── config.py
│   ├── alembic/                # DB migrations
│   └── scripts/
│       ├── seed.py             # Phase 1: load test data
│       ├── sync_graph.py       # Phase 2: sync PG → Neo4j
│       ├── embed_docs.py       # Phase 3: embed docs → Qdrant
│       └── validate_tools.py   # Phase 4: assert all 6 tools work
└── frontend/
    └── app/
        ├── page.tsx            # Dashboard
        ├── projects/[id]/      # Project detail
        └── agent/              # AI investigation interface
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Required. GPT-4o + text-embedding-3-small |
| `DATABASE_URL` | PostgreSQL connection string |
| `NEO4J_URI` | Bolt URI for Neo4j |
| `NEO4J_USER` / `NEO4J_PASSWORD` | Neo4j credentials |
| `QDRANT_HOST` / `QDRANT_PORT` | Qdrant connection |
| `AGENT_TOOL_DELAY_MS` | Artificial delay per tool call for demo pacing (default 200) |
