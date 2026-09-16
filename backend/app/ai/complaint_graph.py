"""
LangGraph Workflow for Pharmaceutical Complaint Intake.

Target Flow:
START -> extract_fields -> validate_normalize -> risk_assessment -> build_result -> END

Architectural Invariants:
1. Strict Anti-Hallucination: Unprovided fields remain None (null).
2. Deterministic & Normalized: Quantitative & categorical fields validated via Pydantic.
3. Human-in-the-Loop: Workflow produces suggestions for human review; NEVER writes to PostgreSQL.
"""

import logging
from typing import Optional, TypedDict
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

from ..schemas.ai import AIComplaintExtraction, AIRiskAssessment
from .groq_client import get_chat_groq
from .prompts import EXTRACTION_SYSTEM_PROMPT, RISK_ASSESSMENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

VALID_SEVERITIES = {"Low", "Medium", "High", "Critical"}
VALID_PRIORITIES = {"Low", "Medium", "High", "Urgent"}


class ComplaintGraphState(TypedDict, total=False):
    """Explicit state container passed between LangGraph nodes."""
    input_text: str
    complaint: Optional[AIComplaintExtraction]
    risk_assessment: Optional[AIRiskAssessment]
    error: Optional[str]


def extract_fields_node(state: ComplaintGraphState) -> ComplaintGraphState:
    """
    Node 1: extract_fields
    Sends user's raw complaint text to Groq with structured extraction schema.
    """
    input_text = state.get("input_text", "").strip()
    if not input_text:
        return {"error": "Input text cannot be empty"}

    llm = get_chat_groq(temperature=0.0)
    structured_extractor = llm.with_structured_output(AIComplaintExtraction)

    messages = [
        SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
        HumanMessage(
            content=f"Please extract all factual complaint details from this narrative:\n\n\"\"\"\n{input_text}\n\"\"\""
        ),
    ]

    raw_result = structured_extractor.invoke(messages)

    if isinstance(raw_result, dict):
        extraction = AIComplaintExtraction.model_validate(raw_result)
    else:
        extraction = raw_result

    return {"complaint": extraction}


def validate_normalize_node(state: ComplaintGraphState) -> ComplaintGraphState:
    """
    Node 2: validate_normalize
    Validates and normalizes structured extraction output.
    Rules:
    - Strips whitespace; converts empty strings to None.
    - Preserves nulls for missing values (never fabricates).
    - Enforces positive integer for quantity_affected or None.
    - Populates detailed_description with input_text if left empty.
    """
    complaint = state.get("complaint")
    if not complaint:
        return {"error": "Missing complaint extraction in state"}

    complaint_dict = complaint.model_dump()

    # Normalize strings: trim whitespace, convert empty strings to None
    for field, val in complaint_dict.items():
        if isinstance(val, str):
            trimmed = val.strip()
            complaint_dict[field] = trimmed if trimmed else None

    # Quantity affected validation
    qty = complaint_dict.get("quantity_affected")
    if qty is not None and qty < 0:
        complaint_dict["quantity_affected"] = None

    # Fallback description to input text if LLM did not generate one
    if not complaint_dict.get("detailed_description"):
        complaint_dict["detailed_description"] = state.get("input_text", "").strip()

    normalized_complaint = AIComplaintExtraction.model_validate(complaint_dict)
    return {"complaint": normalized_complaint}


def risk_assessment_node(state: ComplaintGraphState) -> ComplaintGraphState:
    """
    Node 3: risk_assessment
    Uses extracted complaint facts to ask Groq for an initial preliminary risk triage.
    """
    complaint = state.get("complaint")
    if not complaint:
        return {"error": "Missing complaint data for risk assessment"}

    complaint_summary = (
        f"Product Name: {complaint.product_name or 'Unknown / Not specified'}\n"
        f"Dosage Strength / Grade: {complaint.product_strength_grade or 'Unknown / Not specified'}\n"
        f"Batch / Lot Number: {complaint.batch_lot_number or 'Unknown / Not specified'}\n"
        f"Quantity Affected: {complaint.quantity_affected if complaint.quantity_affected is not None else 'Unknown / Not specified'}\n"
        f"Complaint Type: {complaint.complaint_type or 'Unknown / General Defect'}\n"
        f"Customer / Reporter: {complaint.customer_name or 'Unknown / Not specified'}\n"
        f"Detailed Description: {complaint.detailed_description or state.get('input_text', '')}\n"
    )

    llm = get_chat_groq(temperature=0.0)
    structured_risk = llm.with_structured_output(AIRiskAssessment)

    messages = [
        SystemMessage(content=RISK_ASSESSMENT_SYSTEM_PROMPT),
        HumanMessage(
            content=f"Perform preliminary QA risk triage on this reported pharmaceutical complaint:\n\n{complaint_summary}"
        ),
    ]

    raw_risk = structured_risk.invoke(messages)
    if isinstance(raw_risk, dict):
        risk = AIRiskAssessment.model_validate(raw_risk)
    else:
        risk = raw_risk

    # Normalize severity to canonical casing
    severity = (risk.initial_severity or "").strip().capitalize()
    if severity not in VALID_SEVERITIES:
        severity = "Medium"

    # Normalize priority to canonical casing
    priority = (risk.priority or "").strip().capitalize()
    if priority not in VALID_PRIORITIES:
        priority = "Medium"

    normalized_risk = AIRiskAssessment(
        initial_severity=severity,
        priority=priority,
        risk_reasoning=risk.risk_reasoning.strip(),
        recommended_next_actions=[a.strip() for a in risk.recommended_next_actions if a.strip()],
    )

    return {"risk_assessment": normalized_risk}


def build_result_node(state: ComplaintGraphState) -> ComplaintGraphState:
    """
    Node 4: build_result
    Assembles final result. Does NOT persist to PostgreSQL.
    """
    return {
        "complaint": state.get("complaint"),
        "risk_assessment": state.get("risk_assessment"),
    }


def create_complaint_graph():
    """Builds and compiles the LangGraph StateGraph workflow."""
    workflow = StateGraph(ComplaintGraphState)

    workflow.add_node("extract_fields", extract_fields_node)
    workflow.add_node("validate_normalize", validate_normalize_node)
    workflow.add_node("risk_assessment", risk_assessment_node)
    workflow.add_node("build_result", build_result_node)

    workflow.add_edge(START, "extract_fields")
    workflow.add_edge("extract_fields", "validate_normalize")
    workflow.add_edge("validate_normalize", "risk_assessment")
    workflow.add_edge("risk_assessment", "build_result")
    workflow.add_edge("build_result", END)

    return workflow.compile()


# Pre-compiled graph instance
complaint_intake_graph = create_complaint_graph()
