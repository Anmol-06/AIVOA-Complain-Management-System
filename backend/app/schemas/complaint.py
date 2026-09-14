from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ComplaintBase(BaseModel):
    """
    Base schema containing domain fields for customer complaints.
    All fields are optional/nullable to reflect real-world incomplete complaints.
    """
    complaint_source: Optional[str] = None
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    product_strength_grade: Optional[str] = None
    batch_lot_number: Optional[str] = None
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    quantity_affected: Optional[int] = None
    complaint_type: Optional[str] = None
    complaint_date: Optional[date] = None
    detailed_description: Optional[str] = None
    initial_severity: Optional[str] = None
    priority: Optional[str] = None


class ComplaintCreate(ComplaintBase):
    """
    Schema for creating a new complaint record via POST /api/complaints.
    Inherits all complaint domain fields from ComplaintBase.
    """
    pass


class ComplaintUpdate(BaseModel):
    """
    Schema for partial updates via PATCH /api/complaints/{id}.
    Every field is optional. Unsupplied fields will NOT be modified in PostgreSQL.
    """
    complaint_source: Optional[str] = None
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    product_strength_grade: Optional[str] = None
    batch_lot_number: Optional[str] = None
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    quantity_affected: Optional[int] = None
    complaint_type: Optional[str] = None
    complaint_date: Optional[date] = None
    detailed_description: Optional[str] = None
    initial_severity: Optional[str] = None
    priority: Optional[str] = None


class ComplaintResponse(ComplaintBase):
    """
    Schema for responses returning a complaint record.
    Includes database-generated UUID and audit timestamps.
    """
    id: UUID
    created_at: datetime
    updated_at: datetime

    # Pydantic v2 configuration to allow serialization directly from SQLAlchemy ORM models
    model_config = ConfigDict(from_attributes=True)
