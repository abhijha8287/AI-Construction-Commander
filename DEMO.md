# Demo Script — AI Construction Commander

## Setup (run once)

```bash
docker-compose up -d
sleep 15  # wait for databases to be healthy

docker-compose exec api python scripts/seed.py
docker-compose exec api python scripts/sync_graph.py
docker-compose exec api python scripts/embed_docs.py
```

Frontend:
```bash
cd frontend && npm install && npm run dev
```

Open http://localhost:3000

---

## Demo Flow (8 minutes)

### 1. Dashboard (30s)
Open http://localhost:3000

Point out the red metric cards:
- **2 Delayed Projects** (Tower A, Building B)
- **1 Delayed Shipment** (S-102 from ABC Steel)
- **3 Pending POs** (PO-103, PO-201, PO-202)

### 2. Project Detail (1 min)
Click **Tower A** in the projects table.

Point out:
- Materials: Rebar shows **actual 320 / planned 500 tonnes** — gap of 180
- Shipments: S-102 shows **+9d delay**, status DELAYED
- Purchase Orders: PO-103 is PENDING

Click **"Investigate with AI →"** — this pre-fills the query.

### 3. Core Demo: Why is Tower A delayed? (3 min)

On the Agent page, the query is pre-filled. Click **Investigate**.

Watch the reasoning trace appear one card at a time:

| Step | Tool | What it finds |
|------|------|---------------|
| 1 | get_project_status | Tower A — delayed, Mumbai, ₹85M, planned end 2026-07-15 |
| 2 | get_material_shortages | Rebar: 320 of 500 tonnes received (180 short) |
| 3 | get_delayed_shipments | S-102 from ABC Steel — 9 days late, still in transit |
| 4 | get_vendor_history | ABC Steel rating 2.7/5, 3 of 4 shipments delayed |
| 5 | get_inspection_issues | Qdrant returns inspection report: batch S-102 FAILED tensile test (390 MPa vs 500 MPa spec), full batch rejected |
| 6 | get_graph_relationships | Neo4j confirms: Tower A → Rebar ← S-102 ← ABC Steel, 9 days delay |
| 7 | final_answer | Root cause identified |

**Expected answer:**

> **Primary cause:** ABC Steel's rebar shipment S-102 failed quality inspection (tensile strength 390 MPa vs 500 MPa requirement), causing full batch rejection. Replacement lead time is 12–14 days.
>
> **Secondary cause:** ABC Steel has a pattern of poor delivery performance (3 of 4 shipments delayed, avg 6.7 days, rating 2.7/5).
>
> **Impact:** ~14 days delay to Tower A completion
>
> **Confidence:** 91%
>
> **Recommendation:** Authorize alternate rebar supplier per RFI-047 and expedite PO-103 replacement with a vendor meeting ASTM A615 specifications.

Each evidence item traces to a specific database record — click any step card to expand the raw data.

### 4. Different Project, Different Root Cause (2 min)

Click preset: **"Why is Building B delayed?"**

Watch the agent reason about Building B:
- No inspection failures
- No vendor quality issues
- Root cause: **procurement approval bottleneck** — PO-201 and PO-202 both pending, blocking concrete and steel beam delivery

Expected answer identifies procurement process failure, not vendor quality.

**Key message to judges:** Same agent, same tools, completely different diagnosis. Evidence-grounded every time.

### 5. Vendor Question (1 min)

Click preset: **"Which vendors are high risk?"**

Agent will call `get_vendor_history` for each vendor and produce a ranked list with ABC Steel flagged high-risk.

---

## Architecture Talking Points

**Three databases, one query:**
- PostgreSQL → structured facts (quantities, dates, amounts)
- Neo4j → graph traversal (who supplies what to whom)
- Qdrant → semantic search over inspection reports and contracts

**Traceable evidence:** Every sentence in the answer maps to a database record. Click a step card to see the raw query result that produced that sentence.

**SSE streaming:** The reasoning trace is streamed in real-time via Server-Sent Events. The agent is genuinely running LangGraph's ReAct loop — you see each tool call as it happens.

---

## What Can Go Wrong (and how to recover)

| Problem | Fix |
|---------|-----|
| Dashboard shows "Cannot connect to API" | Run `docker-compose up -d` and wait 15s |
| Agent returns no answer | Check `OPENAI_API_KEY` in `.env` is valid |
| Inspection issue not found | Re-run `embed_docs.py` — collection may not have been created |
| Qdrant score below threshold | Normal — re-run embed step, sometimes embeddings need time |
| Neo4j traversal returns empty | Run `sync_graph.py` again |

---

## Validate Everything Works First

```bash
docker-compose exec api python scripts/validate_tools.py
```

All 6 lines must print `PASS`. If any fails, the demo will be incomplete.
