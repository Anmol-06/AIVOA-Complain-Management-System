import uuid
from sqlalchemy import Column, Text, Integer, Date, DateTime, text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Complaint(Base):
    """
    SQLAlchemy model representing the initial pharmaceutical customer complaints table.
    
    IMPORTANT ARCHITECTURAL & DATA DESIGN PRINCIPLES:
    1. Direct Assignment Alignment: Fields correspond strictly to the assignment's complaint intake form.
    2. Intentional Nullability: All domain fields are nullable because real-world complaints can be
       reported with partial information. NULL strictly indicates missing/unprovided data.
       Never use artificial placeholders like "unknown", 0, or dummy dates.
    3. UUID Identification: Primary key uses UUIDv4 to avoid predictable sequential ID enumeration.
       Note: UUIDs provide non-sequential uniqueness, but do NOT replace authorization/access controls.
    4. Quantity Limitation: `quantity_affected` is stored as an INTEGER as specified in the assignment.
       Note: Approximation semantics (e.g. "approx 100 vials") cannot be preserved purely as an integer.
    5. Absence of ENUMs: `initial_severity`, `priority`, and `complaint_type` are stored as TEXT to allow
       flexible application-level validation and normalization without early database migration lock-in.
    6. No AI-Derived Fields: Risk scores, CAPA actions, root-cause analyses, and AI confidence ratings
       belong to the AI workflow layer and are intentionally omitted from this baseline facts table.
    """

    __tablename__ = "complaints"

    # 1. Primary Identifier (UUID)
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        nullable=False,
        doc="Unique complaint identifier (UUIDv4)",
    )

    # 2. Intake Source
    complaint_source = Column(
        Text,
        nullable=True,
        doc="Intake channel (e.g., email, phone, web portal)",
    )

    # 3. Complainant / Customer
    customer_name = Column(
        Text,
        nullable=True,
        doc="Name of customer, hospital, clinic, or patient",
    )

    # 4. Drug Product Details
    product_name = Column(
        Text,
        nullable=True,
        doc="Brand or generic pharmaceutical product name",
    )

    # 5. Product Strength / Grade
    product_strength_grade = Column(
        Text,
        nullable=True,
        doc="Dosage strength or pharmaceutical grade (e.g., '500 mg', '10 mg/mL')",
    )

    # 6. Manufacturing Batch / Lot
    batch_lot_number = Column(
        Text,
        nullable=True,
        doc="Manufacturing batch or lot number for quality traceability",
    )

    # 7. Manufacturing Date
    manufacturing_date = Column(
        Date,
        nullable=True,
        doc="Date product was manufactured",
    )

    # 8. Product Expiration Date
    expiry_date = Column(
        Date,
        nullable=True,
        doc="Expiration date of the batch",
    )

    # 9. Affected Units Count
    quantity_affected = Column(
        Integer,
        nullable=True,
        doc="Number of units affected. Note: approximation semantics cannot be preserved in an integer.",
    )

    # 10. Complaint Classification
    complaint_type = Column(
        Text,
        nullable=True,
        doc="Defect category (e.g., packaging, contamination, labeling, efficacy)",
    )

    # 11. Date of Incident / Report
    complaint_date = Column(
        Date,
        nullable=True,
        doc="Date complaint was received or occurred",
    )

    # 12. Unstructured Narrative Description
    detailed_description = Column(
        Text,
        nullable=True,
        doc="Detailed narrative account of the complaint issue",
    )

    # 13. Triage Severity
    initial_severity = Column(
        Text,
        nullable=True,
        doc="Initial severity assessment (e.g., Critical, Major, Minor)",
    )

    # 14. QA Priority
    priority = Column(
        Text,
        nullable=True,
        doc="Investigation priority level (e.g., High, Medium, Low)",
    )

    # 15. Audit: Creation Timestamp
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Timestamp when complaint record was created",
    )

    # 16. Audit: Last Update Timestamp
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        doc="Timestamp when complaint record was last modified",
    )
