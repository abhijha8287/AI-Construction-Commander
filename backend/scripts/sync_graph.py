"""
Phase 2: sync_graph.py
Reads PostgreSQL and creates Neo4j nodes + edges.
Verification: MATCH path returns Tower A | Rebar | S-102 | 9 | ABC Steel
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from neo4j import AsyncGraphDatabase
from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def sync():
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )

    async with Session() as db:
        projects = (await db.execute(text("SELECT id, name, status, location FROM projects"))).fetchall()
        vendors = (await db.execute(text("SELECT id, name, rating, sla_days FROM vendors"))).fetchall()
        materials = (await db.execute(text("SELECT id, name, project_id FROM materials"))).fetchall()
        purchase_orders = (await db.execute(text(
            "SELECT id, po_number, project_id, vendor_id, material_id, approval_status FROM purchase_orders"
        ))).fetchall()
        shipments = (await db.execute(text(
            "SELECT id, shipment_number, purchase_order_id, vendor_id, delay_days, status FROM shipments"
        ))).fetchall()

    async with driver.session() as neo:
        # Clear existing graph
        await neo.run("MATCH (n) DETACH DELETE n")
        print("  Cleared existing graph")

        # Create Project nodes
        for p in projects:
            await neo.run(
                "MERGE (p:Project {id: $id}) SET p.name=$name, p.status=$status, p.location=$location",
                id=str(p[0]), name=p[1], status=p[2], location=p[3] or ""
            )
        print(f"  Created {len(projects)} Project nodes")

        # Create Vendor nodes
        for v in vendors:
            await neo.run(
                "MERGE (v:Vendor {id: $id}) SET v.name=$name, v.rating=$rating, v.sla_days=$sla_days",
                id=str(v[0]), name=v[1], rating=float(v[2] or 0), sla_days=v[3] or 0
            )
        print(f"  Created {len(vendors)} Vendor nodes")

        # Create Material nodes + USES relationship to Project
        for m in materials:
            await neo.run(
                "MERGE (m:Material {id: $id}) SET m.name=$name",
                id=str(m[0]), name=m[1]
            )
            await neo.run(
                """
                MATCH (p:Project {id: $pid})
                MATCH (m:Material {id: $mid})
                MERGE (p)-[:USES]->(m)
                """,
                pid=str(m[2]), mid=str(m[0])
            )
        print(f"  Created {len(materials)} Material nodes + USES edges")

        # Build lookup maps for PO resolution
        po_map = {str(po[0]): po for po in purchase_orders}

        # Create PurchaseOrder nodes + FULFILLS (Vendor→PO) + ORDERS (PO→Material)
        for po in purchase_orders:
            await neo.run(
                "MERGE (po:PurchaseOrder {id: $id}) SET po.po_number=$po_number, po.approval_status=$status",
                id=str(po[0]), po_number=po[1], status=po[5]
            )
            await neo.run(
                """
                MATCH (v:Vendor {id: $vid})
                MATCH (po:PurchaseOrder {id: $poid})
                MERGE (v)-[:FULFILLS]->(po)
                """,
                vid=str(po[3]), poid=str(po[0])
            )
            await neo.run(
                """
                MATCH (po:PurchaseOrder {id: $poid})
                MATCH (m:Material {id: $mid})
                MERGE (po)-[:ORDERS]->(m)
                """,
                poid=str(po[0]), mid=str(po[4])
            )

        print(f"  Created {len(purchase_orders)} PurchaseOrder nodes + FULFILLS/ORDERS edges")

        # Create Shipment nodes + DELIVERS (Shipment→Material) + FULFILLS (Vendor→Shipment)
        for s in shipments:
            await neo.run(
                "MERGE (s:Shipment {id: $id}) SET s.shipment_number=$sn, s.delay_days=$dd, s.status=$st",
                id=str(s[0]), sn=s[1], dd=s[4] or 0, st=s[5]
            )
            # Vendor FULFILLS Shipment
            await neo.run(
                """
                MATCH (v:Vendor {id: $vid})
                MATCH (s:Shipment {id: $sid})
                MERGE (v)-[:FULFILLS]->(s)
                """,
                vid=str(s[3]), sid=str(s[0])
            )
            # Shipment DELIVERS Material (via PO)
            po = po_map.get(str(s[2]))
            if po:
                await neo.run(
                    """
                    MATCH (s:Shipment {id: $sid})
                    MATCH (m:Material {id: $mid})
                    MERGE (s)-[:DELIVERS]->(m)
                    """,
                    sid=str(s[0]), mid=str(po[4])
                )
        print(f"  Created {len(shipments)} Shipment nodes + DELIVERS/FULFILLS edges")

    # ── Verification ──────────────────────────────────────────────────────────
    print("\nPhase 2 verification:")
    async with driver.session() as neo:
        result = await neo.run(
            """
            MATCH path =
              (p:Project {name: "Tower A"})-[:USES]->(m:Material)
              <-[:DELIVERS]-(s:Shipment)<-[:FULFILLS]-(v:Vendor)
            WHERE s.delay_days > 0
            RETURN p.name AS project, m.name AS material,
                   s.shipment_number AS shipment, s.delay_days AS delay_days, v.name AS vendor
            ORDER BY s.delay_days DESC
            """
        )
        rows = await result.data()
        if rows:
            for row in rows:
                print(f"  {row['project']} | {row['material']} | {row['shipment']} | {row['delay_days']} | {row['vendor']}")
            expected = rows[0]
            ok = (
                expected['project'] == 'Tower A' and
                expected['material'] == 'Rebar' and
                expected['shipment'] == 'S-102' and
                expected['delay_days'] == 9 and
                expected['vendor'] == 'ABC Steel'
            )
            print(f"\n  Traversal result: {'✓ PASS' if ok else '✗ FAIL — check seed data and graph sync'}")
        else:
            print("  ✗ FAIL — no results returned. Check seed and sync.")

        # Node count verification
        for label, expected_count in [("Project", 2), ("Vendor", 3), ("Material", 4), ("Shipment", 6)]:
            r = await neo.run(f"MATCH (n:{label}) RETURN COUNT(n) AS c")
            data = await r.data()
            count = data[0]['c']
            print(f"  {label:<15} {count}  {'✓' if count == expected_count else f'✗ expected {expected_count}'}")

    await driver.close()
    print("\nPhase 2 complete if traversal shows ✓ PASS")


if __name__ == "__main__":
    asyncio.run(sync())
