"""
Phase 4: The 6 tool functions.
Each queries a real data source. Each can be tested in isolation.
No LLM involved here — only data retrieval.
"""
import asyncio
import os
from datetime import date
from langchain_core.tools import tool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from neo4j import AsyncGraphDatabase
from openai import OpenAI
from qdrant_client import QdrantClient
from app.config import settings

_engine = create_async_engine(settings.database_url, echo=False)
_Session = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


async def _delay():
    ms = settings.agent_tool_delay_ms
    if ms > 0:
        await asyncio.sleep(ms / 1000)


# ── Tool 1 ────────────────────────────────────────────────────────────────────

@tool
async def get_project_status(project_name: str) -> dict:
    """Fetch project timeline, status, and budget for a given project name."""
    await _delay()
    async with _Session() as db:
        result = await db.execute(text(
            """
            SELECT name, status, location, budget,
                   planned_start_date, planned_end_date, actual_end_date
            FROM projects WHERE name = :name
            """
        ), {"name": project_name})
        row = result.fetchone()
    if not row:
        return {"error": f"Project '{project_name}' not found"}
    return {
        "name": row[0],
        "status": row[1],
        "location": row[2],
        "budget": float(row[3] or 0),
        "planned_start_date": str(row[4]) if row[4] else None,
        "planned_end_date": str(row[5]) if row[5] else None,
        "actual_end_date": str(row[6]) if row[6] else None,
    }


# ── Tool 2 ────────────────────────────────────────────────────────────────────

@tool
async def get_material_shortages(project_name: str) -> list[dict]:
    """Find materials where actual quantity is below planned quantity for a project."""
    await _delay()
    async with _Session() as db:
        result = await db.execute(text(
            """
            SELECT m.name, m.category, m.unit, m.planned_quantity, m.actual_quantity
            FROM materials m
            JOIN projects p ON m.project_id = p.id
            WHERE p.name = :name
              AND m.actual_quantity < m.planned_quantity
            ORDER BY (m.planned_quantity - m.actual_quantity) DESC
            """
        ), {"name": project_name})
        rows = result.fetchall()
    if not rows:
        return []
    return [
        {
            "name": r[0],
            "category": r[1],
            "unit": r[2],
            "planned_quantity": float(r[3] or 0),
            "actual_quantity": float(r[4] or 0),
            "shortage": float(r[3] or 0) - float(r[4] or 0),
        }
        for r in rows
    ]


# ── Tool 3 ────────────────────────────────────────────────────────────────────

@tool
async def get_delayed_shipments(project_name: str) -> list[dict]:
    """Find all delayed shipments for a project, including vendor and material info."""
    await _delay()
    async with _Session() as db:
        result = await db.execute(text(
            """
            SELECT s.shipment_number, s.status, s.delay_days,
                   s.planned_delivery, s.actual_delivery,
                   v.name AS vendor_name,
                   m.name AS material_name,
                   po.po_number
            FROM shipments s
            JOIN vendors v ON s.vendor_id = v.id
            JOIN purchase_orders po ON s.purchase_order_id = po.id
            JOIN materials m ON po.material_id = m.id
            JOIN projects p ON po.project_id = p.id
            WHERE p.name = :name AND s.delay_days > 0
            ORDER BY s.delay_days DESC
            """
        ), {"name": project_name})
        rows = result.fetchall()
    if not rows:
        return []
    return [
        {
            "shipment_number": r[0],
            "status": r[1],
            "delay_days": r[2],
            "planned_delivery": str(r[3]) if r[3] else None,
            "actual_delivery": str(r[4]) if r[4] else None,
            "vendor_name": r[5],
            "material_name": r[6],
            "po_number": r[7],
        }
        for r in rows
    ]


# ── Tool 4 ────────────────────────────────────────────────────────────────────

@tool
async def get_vendor_history(vendor_name: str) -> dict:
    """Get vendor rating, SLA, and full delivery history (on-time rate, avg delay)."""
    await _delay()
    async with _Session() as db:
        vendor_result = await db.execute(text(
            "SELECT id, name, rating, sla_days, email, contact_person FROM vendors WHERE name = :name"
        ), {"name": vendor_name})
        vendor = vendor_result.fetchone()
        if not vendor:
            return {"error": f"Vendor '{vendor_name}' not found"}

        shipment_result = await db.execute(text(
            """
            SELECT shipment_number, delay_days, status, planned_delivery, actual_delivery
            FROM shipments WHERE vendor_id = :vid
            ORDER BY planned_delivery DESC
            """
        ), {"vid": str(vendor[0])})
        shipments = shipment_result.fetchall()

    total = len(shipments)
    delayed = sum(1 for s in shipments if s[1] > 0)
    on_time = total - delayed
    avg_delay = sum(s[1] for s in shipments) / total if total > 0 else 0

    return {
        "name": vendor[1],
        "rating": float(vendor[2] or 0),
        "sla_days": vendor[3],
        "contact_person": vendor[5],
        "email": vendor[4],
        "total_shipments": total,
        "delayed_shipments": delayed,
        "on_time_shipments": on_time,
        "on_time_rate": round(on_time / total, 2) if total > 0 else 0,
        "avg_delay_days": round(avg_delay, 1),
        "shipment_history": [
            {
                "shipment_number": s[0],
                "delay_days": s[1],
                "status": s[2],
                "planned_delivery": str(s[3]) if s[3] else None,
                "actual_delivery": str(s[4]) if s[4] else None,
            }
            for s in shipments
        ],
    }


# ── Tool 5 ────────────────────────────────────────────────────────────────────

@tool
async def get_inspection_issues(project_name: str) -> list[dict]:
    """Search for inspection reports for a project using semantic search on Qdrant."""
    await _delay()
    openai_client = OpenAI(api_key=settings.openai_api_key)
    qdrant = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)

    # Semantic search for inspection failures related to this project
    query = f"inspection failure {project_name} rejected shipment quality"
    try:
        response = openai_client.embeddings.create(input=query, model="text-embedding-3-small")
        vec = response.data[0].embedding
        results = qdrant.search(
            collection_name=settings.qdrant_collection,
            query_vector=vec,
            limit=5,
            with_payload=True,
            query_filter=None,
        )
    except Exception as e:
        return [{"error": f"Qdrant search failed: {str(e)}"}]

    inspection_results = []
    for r in results:
        payload = r.payload
        if payload.get("document_type") == "inspection_report" and r.score > 0.30:
            text_content = payload.get("text", "")
            status = "FAILED" if "FAILED" in text_content else "PASSED" if "PASSED" in text_content else "UNKNOWN"
            inspection_results.append({
                "title": payload.get("title"),
                "status": status,
                "content": text_content,
                "score": round(r.score, 3),
                "doc_id": payload.get("doc_id"),
            })

    return inspection_results


# ── Tool 6 ────────────────────────────────────────────────────────────────────

@tool
async def get_graph_relationships(project_name: str) -> dict:
    """Traverse Neo4j to find the vendor-shipment-material causal chain for a project."""
    await _delay()
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        async with driver.session() as neo:
            result = await neo.run(
                """
                MATCH path =
                  (p:Project {name: $name})-[:USES]->(m:Material)
                  <-[:DELIVERS]-(s:Shipment)<-[:FULFILLS]-(v:Vendor)
                WHERE s.delay_days > 0
                RETURN p.name AS project, m.name AS material,
                       s.shipment_number AS shipment,
                       s.delay_days AS delay_days,
                       v.name AS vendor
                ORDER BY s.delay_days DESC
                LIMIT 5
                """,
                name=project_name
            )
            rows = await result.data()
    finally:
        await driver.close()

    if not rows:
        return {
            "message": f"No delayed shipment chain found for {project_name}",
            "project": project_name,
            "vendor": None,
            "shipment": None,
            "material": None,
            "delay_days": 0,
        }

    top = rows[0]
    return {
        "project": top["project"],
        "material": top["material"],
        "shipment": top["shipment"],
        "delay_days": top["delay_days"],
        "vendor": top["vendor"],
        "all_paths": rows,
    }


# ── Completion tool ────────────────────────────────────────────────────────────

@tool
def final_answer(
    primary_cause: str,
    secondary_cause: str | None,
    evidence: list[dict],
    impact_days: int,
    confidence: float,
    recommendation: str,
) -> dict:
    """
    Call this tool when you have gathered enough evidence to conclude the root cause.
    Provide a complete structured answer with evidence citations.
    """
    return {
        "primary_cause": primary_cause,
        "secondary_cause": secondary_cause,
        "evidence": evidence,
        "impact_days": impact_days,
        "confidence": confidence,
        "recommendation": recommendation,
    }


ALL_TOOLS = [
    get_project_status,
    get_material_shortages,
    get_delayed_shipments,
    get_vendor_history,
    get_inspection_issues,
    get_graph_relationships,
    final_answer,
]
