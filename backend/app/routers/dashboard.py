from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    projects = (await db.execute(text("SELECT status, COUNT(*) FROM projects GROUP BY status"))).fetchall()
    status_counts = {row[0]: row[1] for row in projects}

    total_shipments = (await db.execute(text("SELECT COUNT(*) FROM shipments"))).scalar() or 1
    delayed_shipments = (await db.execute(text("SELECT COUNT(*) FROM shipments WHERE delay_days > 0"))).scalar() or 0
    total_pos = (await db.execute(text("SELECT COUNT(*) FROM purchase_orders"))).scalar() or 1
    pending_pos = (await db.execute(text("SELECT COUNT(*) FROM purchase_orders WHERE approval_status='pending'"))).scalar() or 0
    total_docs = (await db.execute(text("SELECT COUNT(*) FROM documents"))).scalar() or 0

    avg_risk = (await db.execute(text("SELECT AVG(risk_score) FROM ai_analyses"))).scalar()

    at_risk_projects = (await db.execute(text(
        """
        SELECT p.name, p.status, p.location,
               COALESCE(
                 (COUNT(CASE WHEN s.delay_days > 0 THEN 1 END)::float / NULLIF(COUNT(s.id), 0)) * 0.5 +
                 (COUNT(CASE WHEN po.approval_status = 'pending' THEN 1 END)::float / NULLIF(COUNT(po.id), 0)) * 0.3,
                 0
               ) AS risk_score
        FROM projects p
        LEFT JOIN purchase_orders po ON po.project_id = p.id
        LEFT JOIN shipments s ON s.purchase_order_id = po.id
        GROUP BY p.id, p.name, p.status, p.location
        ORDER BY risk_score DESC
        LIMIT 5
        """
    ))).fetchall()

    return {
        "summary": {
            "total_projects": sum(status_counts.values()),
            "active_projects": status_counts.get("active", 0),
            "delayed_projects": status_counts.get("delayed", 0),
            "total_vendors": (await db.execute(text("SELECT COUNT(*) FROM vendors WHERE active=true"))).scalar(),
            "delayed_shipments": delayed_shipments,
            "pending_pos": pending_pos,
            "total_documents": total_docs,
            "avg_risk_score": round(float(avg_risk or 0), 1),
        },
        "at_risk_projects": [
            {
                "name": r[0],
                "status": r[1],
                "location": r[2],
                "risk_score": round(float(r[3] or 0) * 100, 1),
            }
            for r in at_risk_projects
        ],
    }
