# AI Construction Commander

Ask a construction project question in plain English, such as "Why is Tower A delayed?", and an agent queries three databases to find the root cause, showing its reasoning as it goes.

## Why this exists
Construction delays usually trace back across several systems: schedules, supplier records, inspection reports. This project tests whether one agent can follow that trail across a relational database, a graph database and a vector store.

## What it does
- Runs a LangGraph ReAct agent on GPT-4o with six tools
- Queries PostgreSQL for projects, materials, purchase orders and vendors
- Traverses Neo4j for links between projects, materials, shipments and suppliers
- Searches inspection and site documents in Qdrant
- Streams each reasoning step and the evidence behind the final answer to the UI
- Includes seed data and a demo script (Tower A steel failure, Building B approval bottleneck, vendor risk)

## Project structure
```
AI-Construction-Commander/
├── backend/
│   ├── app/agents/   LangGraph agent and tools
│   ├── app/routers/  FastAPI endpoints
│   ├── alembic/      Database migrations
│   └── scripts/      Seed, graph sync, embeddings, tool checks
├── frontend/
│   ├── app/agent/    Agent chat page
│   ├── app/projects/ Projects overview
│   └── lib/          API client
├── DEMO.md           Demo script and expected answers
├── docker-compose.yml  Postgres, Neo4j, Qdrant, API
└── .env.example      Required settings
```

## Getting started
Requirements: Docker and Docker Compose, Node.js 18+, an OpenAI API key.
```bash
git clone https://github.com/abhijha8287/AI-Construction-Commander.git
cd AI-Construction-Commander
cp .env.example .env                                        # set OPENAI_API_KEY
docker-compose up -d                                        # wait until all are healthy
docker-compose exec api python scripts/seed.py              # 1. relational data
docker-compose exec api python scripts/sync_graph.py        # 2. graph data
docker-compose exec api python scripts/embed_docs.py        # 3. document vectors
docker-compose exec api python scripts/validate_tools.py    # 4. all 6 tools should PASS
cd frontend && npm install && npm run dev                   # http://localhost:3000/agent
```
Try: "Why is Tower A delayed?", "Why is Building B delayed?", "Which vendors are high risk?"

## Configuration
| Variable | Purpose |
|:--|:--|
| `OPENAI_API_KEY` | GPT-4o and embeddings |
| `DATABASE_URL` | PostgreSQL connection |
| `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` | Neo4j connection |
| `QDRANT_HOST`, `QDRANT_PORT` | Qdrant connection |
| `AGENT_TOOL_DELAY_MS` | Pause between tool calls, for readable demos |

## Tech stack
Python, FastAPI, LangGraph, OpenAI GPT-4o, PostgreSQL (pgvector), Neo4j, Qdrant, Alembic, Next.js 15, Tailwind CSS, Docker
