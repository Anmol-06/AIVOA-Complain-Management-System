from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field


class AIComplaintExtraction(BaseModel):
    """
    Structured extraction schema for pharmaceutical customer complaints.
    Rules:
    - Extract ONLY information directly stated or clearly implied in the input narrative.
    - NEVER invent, assume, or fabricate missing values.
    - Set any unavailable or unmentioned field to None (null).
    """
    complaint_source: Optional[str] = Field(
        default=None,
        description="Originating channel (e.g., 'Email', 'Phone Call', 'Customer Portal', 'Healthcare Provider'). None if not mentioned."
    )
    customer_name: Optional[str] = Field(
        default=None,
        description="Name of reporting customer, hospital, pharmacy, or distributor. None if not mentioned."
    )
    product_name: Optional[str] = Field(
        default=None,
        description="Commercial or generic drug/product name. None if not mentioned."
    )
    product_strength_grade: Optional[str] = Field(
        default=None,
        description="Dosage strength, concentration, or formulation grade (e.g., '500 mg', '10 mg/mL'). None if not mentioned."
    )
    batch_lot_number: Optional[str] = Field(
        default=None,
        description="Manufacturing batch or lot identifier (e.g., 'B1234', 'LOT-9821'). None if not mentioned."
    )
    manufacturing_date: Optional[date] = Field(
        default=None,
        description="Date of manufacture in YYYY-MM-DD format if explicitly specified. None if not mentioned."
    )
    expiry_date: Optional[date] = Field(
        default=None,
        description="Expiration date in YYYY-MM-DD format if explicitly specified. None if not mentioned."
    )
    quantity_affected: Optional[int] = Field(
        default=None,
        description="Exact integer count of affected dosage units or packages. None if not mentioned or unknown."
    )
    complaint_type: Optional[str] = Field(
        default=None,
        description="Category of defect (e.g., 'Packaging Defect', 'Discoloration/Physical Appearance', 'Labeling/Packaging Error', 'Contamination/Foreign Matter', 'Adverse Event'). None if not mentioned."
    )
    complaint_date: Optional[date] = Field(
        default=None,
        description="Date the complaint event occurred or was reported in YYYY-MM-DD format. None if not mentioned."
    )
    detailed_description: Optional[str] = Field(
        default=None,
        description="Comprehensive summary of the customer complaint narrative, preserving all factual observations."
    )


class AIRiskAssessment(BaseModel):
    """
    Initial AI risk triage and recommended investigative actions.
    Note: This is an initial AI recommendation for human QA review, NOT a final regulatory determination.
    """
    initial_severity: Optional[str] = Field(
        default=None,
        description="Initial triage severity: 'Low', 'Medium', 'High', or 'Critical'."
    )
    priority: Optional[str] = Field(
        default=None,
        description="Initial QA handling priority: 'Low', 'Medium', 'High', or 'Urgent'."
    )
    risk_reasoning: str = Field(
        description="Concise rationale explaining why this severity and priority were assigned based solely on provided facts."
    )
    recommended_next_actions: List[str] = Field(
        default_factory=list,
        description="List of practical, immediate investigative next steps for the QA team."
    )


class AIComplaintIntakeRequest(BaseModel):
    """Request payload for AI complaint text analysis."""
    text: str = Field(
        ...,
        min_length=1,
        description="Unstructured natural language customer complaint narrative or message."
    )


class AIComplaintIntakeResponse(BaseModel):
    """Structured response payload returned by the AI complaint intake pipeline."""
    complaint: AIComplaintExtraction
    risk_assessment: AIRiskAssessment


# =====================================================================
# UNIT 6: EDIT COMPLAINT SCHEMAS & ALLOWLIST
# =====================================================================

EDITABLE_COMPLAINT_FIELDS = {
    "complaint_source",
    "customer_name",
    "product_name",
    "product_strength_grade",
    "batch_lot_number",
    "manufacturing_date",
    "expiry_date",
    "quantity_affected",
    "complaint_type",
    "complaint_date",
    "detailed_description",
}


class ComplaintChanges(BaseModel):
    """
    Minimal schema containing ONLY explicitly editable complaint domain fields.
    All fields default to None. Only fields that the user explicitly requests
    to modify will be populated.
    """
    complaint_source: Optional[str] = Field(
        default=None,
        description="Updated originating channel. None if not requested."
    )
    customer_name: Optional[str] = Field(
        default=None,
        description="Updated customer or complainant name. None if not requested."
    )
    product_name: Optional[str] = Field(
        default=None,
        description="Updated product or drug name. None if not requested."
    )
    product_strength_grade: Optional[str] = Field(
        default=None,
        description="Updated dosage strength or grade. None if not requested."
    )
    batch_lot_number: Optional[str] = Field(
        default=None,
        description="Updated manufacturing batch or lot identifier. None if not requested."
    )
    manufacturing_date: Optional[date] = Field(
        default=None,
        description="Updated manufacturing date (YYYY-MM-DD). None if not requested."
    )
    expiry_date: Optional[date] = Field(
        default=None,
        description="Updated expiration date (YYYY-MM-DD). None if not requested."
    )
    quantity_affected: Optional[int] = Field(
        default=None,
        description="Updated integer count of affected units. None if not requested."
    )
    complaint_type: Optional[str] = Field(
        default=None,
        description="Updated defect category. None if not requested."
    )
    complaint_date: Optional[date] = Field(
        default=None,
        description="Updated complaint date (YYYY-MM-DD). None if not requested."
    )
    detailed_description: Optional[str] = Field(
        default=None,
        description="Updated complaint description or observation. None if not requested."
    )


class AIComplaintEditExtraction(BaseModel):
    """
    Structured extraction schema for AI complaint edit requests.
    Enforces distinction between existing facts and requested changes.
    """
    is_edit_request: bool = Field(
        description="True if user instruction is an actual request to edit, correct, or add info to the complaint."
    )
    needs_clarification: bool = Field(
        description="True if the edit request is ambiguous, lacks a required value (e.g. 'Change the quantity'), or cannot be safely executed."
    )
    clarification_message: Optional[str] = Field(
        default=None,
        description="Human-friendly clarification guidance asking the user for missing or ambiguous values. None if unambiguous."
    )
    changes: ComplaintChanges = Field(
        default_factory=ComplaintChanges,
        description="Only the fields explicitly requested to change. Unmentioned fields must remain null/None."
    )
    reasoning: Optional[str] = Field(
        default=None,
        description="Short rationale of what was modified and what was preserved."
    )


class AIComplaintEditRequest(BaseModel):
    """
    Request payload for AI complaint editing.
    Supports either:
    - complaint_id: UUID of an already persisted complaint (PostgreSQL is authoritative).
    - current_complaint: Dictionary representing the current form state (for unsaved complaints).
    """
    complaint_id: Optional[str] = Field(
        default=None,
        description="Optional UUID of a persisted complaint record in PostgreSQL."
    )
    current_complaint: Optional[dict] = Field(
        default=None,
        description="Optional dictionary representing the active client-side complaint form."
    )
    edit_instruction: str = Field(
        ...,
        min_length=1,
        description="Natural language edit, modification, or correction instruction."
    )


class AIComplaintEditProposal(BaseModel):
    """
    Structured response payload returned by the AI complaint edit pipeline.
    This is an advisory proposal for human review. It is NEVER written directly to PostgreSQL.
    """
    complaint_id: Optional[str] = None
    is_valid_edit: bool = True
    needs_clarification: bool = False
    clarification_message: Optional[str] = None
    original_complaint: dict
    requested_changes: dict = Field(
        default_factory=dict,
        description="Dictionary of ONLY the changed fields (new values)."
    )
    updated_complaint: dict = Field(
        default_factory=dict,
        description="Original complaint merged with requested changes."
    )
    risk_assessment: Optional[AIRiskAssessment] = None

