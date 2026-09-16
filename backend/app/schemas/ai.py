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
