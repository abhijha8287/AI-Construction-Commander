"""
Phase 1: seed.py
Exact row counts: projects=2, vendors=3, materials=4, purchase_orders=5,
                  shipments=6, documents=8, ai_analyses=4   Total: 32
"""
import asyncio
import uuid
import os
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from app.config import settings
from app.models import (
    Base, Project, Vendor, Material, PurchaseOrder, Shipment, Document, AIAnalysis
)

engine = create_async_engine(settings.database_url, echo=False)
Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


INSPECTION_REPORT_CONTENT = """INSPECTION REPORT — ABC Steel Rebar, Batch S-102
Date: 2026-05-02
Inspector: John Matthews, Site QC
Project: Tower A, Floor 8 Reinforcement
Material: Rebar Batch RB-2026-119

INSPECTION RESULT: FAILED

Failure Reason:
Yield strength measured at 390 MPa. Specification requires minimum 500 MPa.
Sample failure rate: 4 of 10 test bars failed tensile test.

Action Taken:
Full batch rejected. Vendor ABC Steel notified.
Replacement batch requested. Estimated fabrication lead time: 12-14 days.

Impact:
Expected project delay of 9 days minimum due to rebar shortage on Floor 8 reinforcement.
Shipment S-102 has been rejected. Replacement shipment pending fabrication."""


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with Session() as db:
        # ── Projects (2) ──────────────────────────────────────────────────────
        tower_a_id = str(uuid.uuid4())
        building_b_id = str(uuid.uuid4())

        tower_a = Project(
            id=tower_a_id,
            name="Tower A",
            description="42-floor commercial tower, Mumbai central district",
            location="Mumbai",
            budget=85_000_000.00,
            planned_start_date=date(2025, 1, 15),
            planned_end_date=date(2026, 7, 15),
            actual_end_date=None,
            status="delayed",
        )
        building_b = Project(
            id=building_b_id,
            name="Building B",
            description="8-floor residential complex, Pune",
            location="Pune",
            budget=32_000_000.00,
            planned_start_date=date(2025, 6, 1),
            planned_end_date=date(2026, 9, 30),
            actual_end_date=None,
            status="delayed",
        )
        db.add_all([tower_a, building_b])
        await db.flush()

        # ── Vendors (3) ───────────────────────────────────────────────────────
        abc_steel_id = str(uuid.uuid4())
        prime_concrete_id = str(uuid.uuid4())
        metro_logistics_id = str(uuid.uuid4())

        abc_steel = Vendor(
            id=abc_steel_id,
            name="ABC Steel",
            contact_person="Vikram Mehta",
            email="vikram@abcsteel.in",
            phone="+91-9876543210",
            sla_days=5,
            rating=2.7,
            active=True,
        )
        prime_concrete = Vendor(
            id=prime_concrete_id,
            name="Prime Concrete",
            contact_person="Anita Sharma",
            email="anita@primeconcrete.in",
            phone="+91-9988776655",
            sla_days=7,
            rating=4.6,
            active=True,
        )
        metro_logistics = Vendor(
            id=metro_logistics_id,
            name="Metro Logistics",
            contact_person="Rajesh Kumar",
            email="rajesh@metrologistics.in",
            phone="+91-8765432109",
            sla_days=3,
            rating=4.2,
            active=True,
        )
        db.add_all([abc_steel, prime_concrete, metro_logistics])
        await db.flush()

        # ── Materials (4) ─────────────────────────────────────────────────────
        rebar_id = str(uuid.uuid4())
        concrete_id = str(uuid.uuid4())
        steel_beams_id = str(uuid.uuid4())
        glass_panels_id = str(uuid.uuid4())

        rebar = Material(
            id=rebar_id,
            project_id=tower_a_id,
            name="Rebar",
            category="structural",
            unit="tonnes",
            planned_quantity=500.00,
            actual_quantity=320.00,
        )
        concrete = Material(
            id=concrete_id,
            project_id=building_b_id,
            name="Concrete",
            category="structural",
            unit="m3",
            planned_quantity=1200.00,
            actual_quantity=0.00,
        )
        steel_beams = Material(
            id=steel_beams_id,
            project_id=building_b_id,
            name="Steel Beams",
            category="structural",
            unit="tonnes",
            planned_quantity=80.00,
            actual_quantity=0.00,
        )
        glass_panels = Material(
            id=glass_panels_id,
            project_id=tower_a_id,
            name="Glass Panels",
            category="finishing",
            unit="units",
            planned_quantity=2400.00,
            actual_quantity=2400.00,
        )
        db.add_all([rebar, concrete, steel_beams, glass_panels])
        await db.flush()

        # ── Purchase Orders (5) ───────────────────────────────────────────────
        po101_id = str(uuid.uuid4())
        po102_id = str(uuid.uuid4())
        po103_id = str(uuid.uuid4())
        po201_id = str(uuid.uuid4())
        po202_id = str(uuid.uuid4())

        # Tower A POs
        po101 = PurchaseOrder(
            id=po101_id,
            po_number="PO-101",
            project_id=tower_a_id,
            vendor_id=abc_steel_id,
            material_id=rebar_id,
            quantity=200.00,
            unit_price=850.00,
            total_price=170_000.00,
            expected_delivery=date(2026, 5, 1),
            approval_status="approved",
        )
        po102 = PurchaseOrder(
            id=po102_id,
            po_number="PO-102",
            project_id=tower_a_id,
            vendor_id=abc_steel_id,
            material_id=rebar_id,
            quantity=150.00,
            unit_price=850.00,
            total_price=127_500.00,
            expected_delivery=date(2026, 4, 15),
            approval_status="approved",
        )
        po103 = PurchaseOrder(
            id=po103_id,
            po_number="PO-103",
            project_id=tower_a_id,
            vendor_id=abc_steel_id,
            material_id=rebar_id,
            quantity=30.00,
            unit_price=850.00,
            total_price=25_500.00,
            expected_delivery=date(2026, 6, 1),
            approval_status="pending",
        )
        # Building B POs — stuck in pending (root cause of Building B delay)
        po201 = PurchaseOrder(
            id=po201_id,
            po_number="PO-201",
            project_id=building_b_id,
            vendor_id=prime_concrete_id,
            material_id=concrete_id,
            quantity=300.00,
            unit_price=6500.00,
            total_price=1_950_000.00,
            expected_delivery=date(2026, 6, 15),
            approval_status="pending",
        )
        po202 = PurchaseOrder(
            id=po202_id,
            po_number="PO-202",
            project_id=building_b_id,
            vendor_id=metro_logistics_id,
            material_id=steel_beams_id,
            quantity=40.00,
            unit_price=55_000.00,
            total_price=2_200_000.00,
            expected_delivery=date(2026, 6, 20),
            approval_status="pending",
        )
        db.add_all([po101, po102, po103, po201, po202])
        await db.flush()

        # ── Shipments (6) ─────────────────────────────────────────────────────
        # S-102 is THE critical shipment — 9 days late, inspection FAILED
        s102 = Shipment(
            id=str(uuid.uuid4()),
            shipment_number="S-102",
            purchase_order_id=po101_id,
            vendor_id=abc_steel_id,
            origin="Bhilai",
            destination="Mumbai",
            status="delayed",
            planned_delivery=date(2026, 5, 1),
            actual_delivery=date(2026, 5, 10),
            delay_days=9,
            tracking_reference="TRACK-S102",
        )
        # ABC Steel history — recurring delays (used by get_vendor_history)
        s089 = Shipment(
            id=str(uuid.uuid4()),
            shipment_number="S-089",
            purchase_order_id=po102_id,
            vendor_id=abc_steel_id,
            origin="Bhilai",
            destination="Mumbai",
            status="delivered",
            planned_delivery=date(2026, 3, 10),
            actual_delivery=date(2026, 3, 16),
            delay_days=6,
            tracking_reference="TRACK-S089",
        )
        s095 = Shipment(
            id=str(uuid.uuid4()),
            shipment_number="S-095",
            purchase_order_id=po102_id,
            vendor_id=abc_steel_id,
            origin="Bhilai",
            destination="Mumbai",
            status="delivered",
            planned_delivery=date(2026, 4, 5),
            actual_delivery=date(2026, 4, 9),
            delay_days=4,
            tracking_reference="TRACK-S095",
        )
        s098 = Shipment(
            id=str(uuid.uuid4()),
            shipment_number="S-098",
            purchase_order_id=po102_id,
            vendor_id=abc_steel_id,
            origin="Bhilai",
            destination="Mumbai",
            status="delivered",
            planned_delivery=date(2026, 4, 20),
            actual_delivery=date(2026, 4, 27),
            delay_days=7,
            tracking_reference="TRACK-S098",
        )
        # Building B shipments — in transit but POs not approved, so effectively blocked
        s201 = Shipment(
            id=str(uuid.uuid4()),
            shipment_number="S-201",
            purchase_order_id=po201_id,
            vendor_id=prime_concrete_id,
            origin="Pune Industrial Area",
            destination="Pune Site B",
            status="pending",
            planned_delivery=date(2026, 6, 15),
            actual_delivery=None,
            delay_days=0,
            tracking_reference="TRACK-S201",
        )
        s202 = Shipment(
            id=str(uuid.uuid4()),
            shipment_number="S-202",
            purchase_order_id=po202_id,
            vendor_id=metro_logistics_id,
            origin="Mumbai",
            destination="Pune Site B",
            status="pending",
            planned_delivery=date(2026, 6, 20),
            actual_delivery=None,
            delay_days=0,
            tracking_reference="TRACK-S202",
        )
        db.add_all([s102, s089, s095, s098, s201, s202])
        await db.flush()

        # ── Documents (8) ─────────────────────────────────────────────────────
        doc_inspection = Document(
            id=str(uuid.uuid4()),
            project_id=tower_a_id,
            document_type="inspection_report",
            title="ABC Steel Rebar Inspection — Batch S-102",
            file_path="docs_storage/tower_a_inspection_s102.txt",
            content=INSPECTION_REPORT_CONTENT,
            uploaded_by="john.matthews",
            embedding_status="pending",
        )
        doc_contract_abc = Document(
            id=str(uuid.uuid4()),
            project_id=tower_a_id,
            document_type="contract",
            title="Supply Agreement — ABC Steel Rebar",
            file_path="docs_storage/tower_a_contract_abc_steel.txt",
            content="""SUPPLY AGREEMENT
Vendor: ABC Steel | Project: Tower A
Material: Rebar (Fe500 grade)
Delivery SLA: 5 business days from PO approval
Quality Standard: IS 1786:2008 minimum yield strength 500 MPa
Penalty clause: 2% of order value per day of delay beyond SLA
Applicable from: 2025-01-01""",
            uploaded_by="procurement_team",
            embedding_status="pending",
        )
        doc_site_report = Document(
            id=str(uuid.uuid4()),
            project_id=tower_a_id,
            document_type="site_report",
            title="Tower A Weekly Site Report — Week 19",
            file_path="docs_storage/tower_a_site_report_w19.txt",
            content="""WEEKLY SITE REPORT — Tower A
Week: 19 (May 5-11, 2026)
Reported by: Site Manager Priya Nair

Work Status:
- Floor 8 reinforcement: BLOCKED — rebar shortage
- Floor 7 formwork: COMPLETED
- Electrical rough-in floors 1-6: ON TRACK

Delay Note:
Rebar shortage has stalled Floor 8 since May 2. Replacement batch from ABC Steel
expected by May 15. Project timeline revised: completion now estimated July 29, 2026.
""",
            uploaded_by="priya.nair",
            embedding_status="pending",
        )
        doc_rfi = Document(
            id=str(uuid.uuid4()),
            project_id=tower_a_id,
            document_type="rfi",
            title="RFI-047 — Alternate Rebar Supplier Authorization",
            file_path="docs_storage/tower_a_rfi_047.txt",
            content="""REQUEST FOR INFORMATION — RFI-047
Project: Tower A | Date: 2026-05-03
Submitted by: Site Manager

Subject: Authorization to procure rebar from alternate supplier

Current Situation:
ABC Steel batch S-102 has been rejected (inspection failure). Replacement batch
lead time: 12-14 days. This causes critical path delay.

Request:
Authorize procurement of 200T rebar from Tata Steel (pre-approved vendor) at
rate ₹920/tonne to reduce delay to 3-4 days.

Approval Required: Project Director
""",
            uploaded_by="priya.nair",
            embedding_status="pending",
        )
        doc_po101_doc = Document(
            id=str(uuid.uuid4()),
            project_id=tower_a_id,
            document_type="po",
            title="Purchase Order PO-101 — ABC Steel Rebar",
            file_path="docs_storage/tower_a_po_101.txt",
            content="PO-101 | ABC Steel | Rebar 200T | ₹850/T | Expected: 2026-05-01 | Status: APPROVED",
            uploaded_by="procurement_team",
            embedding_status="pending",
        )
        # Building B documents
        doc_building_b_status = Document(
            id=str(uuid.uuid4()),
            project_id=building_b_id,
            document_type="site_report",
            title="Building B Status Report — June 2026",
            file_path="docs_storage/building_b_status_jun.txt",
            content="""STATUS REPORT — Building B
Date: 2026-06-10
Project Manager: Suresh Patel

Current Status: DELAYED

Root Cause:
PO-201 (Concrete, 300m3, Prime Concrete) and PO-202 (Steel Beams, Metro Logistics)
both pending finance department approval since June 1. Approval delay has prevented
vendor scheduling and material delivery.

No vendor performance issues. Both vendors rated above 4.0 on delivery.

Impact:
Concrete pour for floors 3-5 cannot begin until POs approved.
Estimated delay: 9 days if approved by June 15, 21 days if delayed further.
""",
            uploaded_by="suresh.patel",
            embedding_status="pending",
        )
        doc_building_b_contract = Document(
            id=str(uuid.uuid4()),
            project_id=building_b_id,
            document_type="contract",
            title="Supply Agreement — Prime Concrete",
            file_path="docs_storage/building_b_contract_prime.txt",
            content="SUPPLY AGREEMENT | Prime Concrete | Building B | Concrete M30 | SLA: 7 days | Rating: 4.6",
            uploaded_by="procurement_team",
            embedding_status="pending",
        )
        doc_building_b_invoice = Document(
            id=str(uuid.uuid4()),
            project_id=building_b_id,
            document_type="invoice",
            title="Advance Invoice — Prime Concrete PO-201",
            file_path="docs_storage/building_b_invoice_po201.txt",
            content="INVOICE | Prime Concrete | PO-201 | ₹1,950,000 | Advance 30% = ₹585,000 | Due on PO approval",
            uploaded_by="prime_concrete",
            embedding_status="pending",
        )
        db.add_all([
            doc_inspection, doc_contract_abc, doc_site_report, doc_rfi,
            doc_po101_doc, doc_building_b_status, doc_building_b_contract,
            doc_building_b_invoice
        ])
        await db.flush()

        # ── AI Analyses (4) ───────────────────────────────────────────────────
        analysis_ta_rc = AIAnalysis(
            id=str(uuid.uuid4()),
            project_id=tower_a_id,
            analysis_type="root_cause",
            risk_score=91.00,
            summary="Rebar shipment S-102 rejected due to quality failure (yield strength 390 MPa vs 500 MPa required). 14-day projected schedule slip.",
            recommendation="Switch future rebar procurement to alternate approved vendor. Escalate RFI-047 for immediate authorization.",
            evidence={
                "shipment": "S-102",
                "vendor": "ABC Steel",
                "delay_days": 9,
                "inspection_result": "FAILED",
                "reason": "yield strength below specification",
                "impact_days": 14
            },
        )
        analysis_ta_vr = AIAnalysis(
            id=str(uuid.uuid4()),
            project_id=tower_a_id,
            analysis_type="vendor_risk",
            risk_score=87.00,
            summary="ABC Steel has 25% on-time delivery rate across 4 shipments. Average delay 6.5 days. SLA of 5 days consistently violated.",
            recommendation="Place ABC Steel on vendor review. Require dual-sourcing for all critical materials.",
            evidence={
                "vendor": "ABC Steel",
                "total_shipments": 4,
                "delayed_shipments": 4,
                "on_time_rate": 0.25,
                "avg_delay_days": 6.5,
                "sla_days": 5
            },
        )
        analysis_bb_rc = AIAnalysis(
            id=str(uuid.uuid4()),
            project_id=building_b_id,
            analysis_type="root_cause",
            risk_score=74.00,
            summary="Procurement approval bottleneck. PO-201 (Prime Concrete, ₹19.5L) and PO-202 (Metro Logistics, ₹22L) both pending finance approval since June 1.",
            recommendation="Escalate PO-201 and PO-202 to finance director. No vendor or quality issues — this is a process failure.",
            evidence={
                "pending_pos": ["PO-201", "PO-202"],
                "total_blocked_value": 4_150_000,
                "days_pending": 9,
                "vendor_performance": "not_an_issue"
            },
        )
        analysis_bb_pr = AIAnalysis(
            id=str(uuid.uuid4()),
            project_id=building_b_id,
            analysis_type="procurement_risk",
            risk_score=74.00,
            summary="2 of 2 active POs for Building B are pending approval. No concrete or steel can be ordered until resolved.",
            recommendation="Streamline PO approval workflow for critical path materials. Consider pre-approving POs above ₹15L at project kickoff.",
            evidence={
                "pending_pos": 2,
                "approved_pos": 0,
                "total_pos": 2,
                "blocked_materials": ["Concrete", "Steel Beams"]
            },
        )
        db.add_all([analysis_ta_rc, analysis_ta_vr, analysis_bb_rc, analysis_bb_pr])
        await db.commit()

    print("\n✓ Seed complete. Row counts:")
    async with Session() as db:
        for table in ["projects", "vendors", "materials", "purchase_orders", "shipments", "documents", "ai_analyses"]:
            result = await db.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"  {table:<20} {count}")

    print("\nPhase 1 spot checks:")
    async with Session() as db:
        r = await db.execute(text("SELECT status FROM projects WHERE name = 'Tower A'"))
        status = r.scalar()
        print(f"  Tower A status:          {status}  {'✓' if status == 'delayed' else '✗ FAIL'}")

        r = await db.execute(text(
            "SELECT planned_quantity, actual_quantity FROM materials WHERE name='Rebar'"
        ))
        row = r.fetchone()
        print(f"  Rebar planned/actual:    {row[0]}/{row[1]}  {'✓' if float(row[1]) < float(row[0]) else '✗ FAIL'}")

        r = await db.execute(text(
            "SELECT delay_days, actual_delivery FROM shipments WHERE shipment_number='S-102'"
        ))
        row = r.fetchone()
        print(f"  S-102 delay_days:        {row[0]}  {'✓' if row[0] == 9 else '✗ FAIL'}")

        r = await db.execute(text("SELECT rating FROM vendors WHERE name='ABC Steel'"))
        rating = r.scalar()
        print(f"  ABC Steel rating:        {rating}  {'✓' if float(rating) == 2.7 else '✗ FAIL'}")

        r = await db.execute(text("""
            SELECT COUNT(*) FROM purchase_orders po
            JOIN projects p ON po.project_id = p.id
            WHERE p.name='Building B' AND po.approval_status='pending'
        """))
        count = r.scalar()
        print(f"  Building B pending POs:  {count}  {'✓' if count == 2 else '✗ FAIL'}")

    print("\nPhase 1 complete if all counts match design doc and all spot checks show ✓")


if __name__ == "__main__":
    asyncio.run(seed())
