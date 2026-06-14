import uuid
from datetime import datetime, date
from sqlalchemy import (
    String, Text, Numeric, Integer, Boolean, Date, DateTime,
    ForeignKey, JSON, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


def new_uuid():
    return str(uuid.uuid4())


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(255))
    budget: Mapped[float | None] = mapped_column(Numeric(15, 2))
    planned_start_date: Mapped[date | None] = mapped_column(Date)
    planned_end_date: Mapped[date | None] = mapped_column(Date)
    actual_end_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(50), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    materials: Mapped[list["Material"]] = relationship(back_populates="project")
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(back_populates="project")
    documents: Mapped[list["Document"]] = relationship(back_populates="project")
    ai_analyses: Mapped[list["AIAnalysis"]] = relationship(back_populates="project")


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    contact_person: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    sla_days: Mapped[int | None] = mapped_column(Integer)
    rating: Mapped[float | None] = mapped_column(Numeric(3, 2))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(back_populates="vendor")
    shipments: Mapped[list["Shipment"]] = relationship(back_populates="vendor")


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    unit: Mapped[str | None] = mapped_column(String(50))
    planned_quantity: Mapped[float | None] = mapped_column(Numeric(12, 2))
    actual_quantity: Mapped[float | None] = mapped_column(Numeric(12, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="materials")
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(back_populates="material")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    po_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False)
    vendor_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vendors.id"), nullable=False)
    material_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("materials.id"), nullable=False)
    quantity: Mapped[float | None] = mapped_column(Numeric(12, 2))
    unit_price: Mapped[float | None] = mapped_column(Numeric(12, 2))
    total_price: Mapped[float | None] = mapped_column(Numeric(15, 2))
    expected_delivery: Mapped[date | None] = mapped_column(Date)
    approval_status: Mapped[str] = mapped_column(String(50), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="purchase_orders")
    vendor: Mapped["Vendor"] = relationship(back_populates="purchase_orders")
    material: Mapped["Material"] = relationship(back_populates="purchase_orders")
    shipments: Mapped[list["Shipment"]] = relationship(back_populates="purchase_order")


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    shipment_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    purchase_order_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("purchase_orders.id"), nullable=False)
    vendor_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vendors.id"), nullable=False)
    origin: Mapped[str | None] = mapped_column(String(255))
    destination: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="pending")
    planned_delivery: Mapped[date | None] = mapped_column(Date)
    actual_delivery: Mapped[date | None] = mapped_column(Date)
    delay_days: Mapped[int] = mapped_column(Integer, default=0)
    tracking_reference: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    purchase_order: Mapped["PurchaseOrder"] = relationship(back_populates="shipments")
    vendor: Mapped["Vendor"] = relationship(back_populates="shipments")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str | None] = mapped_column(Text)
    uploaded_by: Mapped[str | None] = mapped_column(String(255))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    embedding_status: Mapped[str] = mapped_column(String(50), default="pending")

    project: Mapped["Project"] = relationship(back_populates="documents")


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False)
    analysis_type: Mapped[str] = mapped_column(String(100), nullable=False)
    risk_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    summary: Mapped[str | None] = mapped_column(Text)
    recommendation: Mapped[str | None] = mapped_column(Text)
    evidence: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="ai_analyses")
