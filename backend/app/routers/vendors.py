from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db

router = APIRouter(prefix="/api/vendors", tags=["vendors"])


@router.get("")
async def list_vendors(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(text(
        """
        SELECT v.id, v.name, v.rating, v.sla_days, v.contact_person, v.email, v.active,
               COUNT(s.id) AS total_shipments,
               COUNT(CASE WHEN s.delay_days > 0 THEN 1 END) AS delayed,
               COALESCE(AVG(CASE WHEN s.delay_days > 0 THEN s.delay_days END), 0) AS avg_delay
        FROM vendors v
        LEFT JOIN shipments s ON s.vendor_id = v.id
        GROUP BY v.id, v.name, v.rating, v.sla_days, v.contact_person, v.email, v.active
        ORDER BY v.rating ASC
        """
    ))).fetchall()

    return [
        {
            "id": str(r[0]),
            "name": r[1],
            "rating": float(r[2] or 0),
            "sla_days": r[3],
            "contact_person": r[4],
            "email": r[5],
            "active": r[6],
            "total_shipments": r[7],
            "delayed_shipments": r[8],
            "on_time_rate": round((r[7] - r[8]) / r[7], 2) if r[7] > 0 else 1.0,
            "avg_delay_days": round(float(r[9]), 1),
        }
        for r in rows
    ]
