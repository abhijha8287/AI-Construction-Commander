from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("")
async def list_projects(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(text(
        """
        SELECT p.id, p.name, p.status, p.location, p.budget,
               p.planned_start_date, p.planned_end_date,
               COUNT(DISTINCT po.id) AS total_pos,
               COUNT(DISTINCT CASE WHEN po.approval_status='pending' THEN po.id END) AS pending_pos,
               COUNT(DISTINCT s.id) AS total_shipments,
               COUNT(DISTINCT CASE WHEN s.delay_days > 0 THEN s.id END) AS delayed_shipments,
               COUNT(DISTINCT doc.id) AS total_docs
        FROM projects p
        LEFT JOIN purchase_orders po ON po.project_id = p.id
        LEFT JOIN shipments s ON s.purchase_order_id = po.id
        LEFT JOIN documents doc ON doc.project_id = p.id
        GROUP BY p.id, p.name, p.status, p.location, p.budget, p.planned_start_date, p.planned_end_date
        ORDER BY p.created_at DESC
        """
    ))).fetchall()

    def risk_score(total_s, delayed_s, total_p, pending_p):
        s = (delayed_s / total_s * 0.5) if total_s > 0 else 0
        p = (pending_p / total_p * 0.3) if total_p > 0 else 0
        return round(min((s + p) * 100, 100), 1)

    return [
        {
            "id": str(r[0]),
            "name": r[1],
            "status": r[2],
            "location": r[3],
            "budget": float(r[4] or 0),
            "planned_start_date": str(r[5]) if r[5] else None,
            "planned_end_date": str(r[6]) if r[6] else None,
            "total_pos": r[7],
            "pending_pos": r[8],
            "total_shipments": r[9],
            "delayed_shipments": r[10],
            "total_documents": r[11],
            "risk_score": risk_score(r[9], r[10], r[7], r[8]),
        }
        for r in rows
    ]


@router.get("/{project_id}")
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    project = (await db.execute(text(
        "SELECT id, name, description, status, location, budget, planned_start_date, planned_end_date, actual_end_date FROM projects WHERE id=:id"
    ), {"id": project_id})).fetchone()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    shipments = (await db.execute(text(
        """
        SELECT s.shipment_number, s.status, s.delay_days, s.planned_delivery, s.actual_delivery,
               v.name AS vendor, m.name AS material, po.po_number
        FROM shipments s
        JOIN vendors v ON s.vendor_id = v.id
        JOIN purchase_orders po ON s.purchase_order_id = po.id
        JOIN materials m ON po.material_id = m.id
        WHERE po.project_id = :pid
        ORDER BY s.delay_days DESC
        """
    ), {"pid": project_id})).fetchall()

    purchase_orders = (await db.execute(text(
        """
        SELECT po.po_number, po.approval_status, po.total_price, po.expected_delivery,
               v.name AS vendor, m.name AS material
        FROM purchase_orders po
        JOIN vendors v ON po.vendor_id = v.id
        JOIN materials m ON po.material_id = m.id
        WHERE po.project_id = :pid
        ORDER BY po.created_at DESC
        """
    ), {"pid": project_id})).fetchall()

    materials = (await db.execute(text(
        "SELECT name, category, unit, planned_quantity, actual_quantity FROM materials WHERE project_id=:pid"
    ), {"pid": project_id})).fetchall()

    analyses = (await db.execute(text(
        "SELECT analysis_type, risk_score, summary, recommendation FROM ai_analyses WHERE project_id=:pid ORDER BY created_at DESC LIMIT 4"
    ), {"pid": project_id})).fetchall()

    return {
        "id": str(project[0]),
        "name": project[1],
        "description": project[2],
        "status": project[3],
        "location": project[4],
        "budget": float(project[5] or 0),
        "planned_start_date": str(project[6]) if project[6] else None,
        "planned_end_date": str(project[7]) if project[7] else None,
        "actual_end_date": str(project[8]) if project[8] else None,
        "shipments": [
            {
                "shipment_number": s[0], "status": s[1], "delay_days": s[2],
                "planned_delivery": str(s[3]) if s[3] else None,
                "actual_delivery": str(s[4]) if s[4] else None,
                "vendor": s[5], "material": s[6], "po_number": s[7],
            }
            for s in shipments
        ],
        "purchase_orders": [
            {
                "po_number": p[0], "approval_status": p[1],
                "total_price": float(p[2] or 0),
                "expected_delivery": str(p[3]) if p[3] else None,
                "vendor": p[4], "material": p[5],
            }
            for p in purchase_orders
        ],
        "materials": [
            {
                "name": m[0], "category": m[1], "unit": m[2],
                "planned_quantity": float(m[3] or 0),
                "actual_quantity": float(m[4] or 0),
            }
            for m in materials
        ],
        "ai_analyses": [
            {
                "analysis_type": a[0], "risk_score": float(a[1] or 0),
                "summary": a[2], "recommendation": a[3],
            }
            for a in analyses
        ],
    }
