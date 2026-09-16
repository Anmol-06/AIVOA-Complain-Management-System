"""
LangGraph Workflow for Pharmaceutical Complaint Intake.

Target Flow:
START -> extract_fields -> validate_normalize -> risk_assessment -> build_result -> END

Architectural Invariants:
1. Strict Anti-Hallucination: Unprovided fields remain None (null).
2. Deterministic & Normalized: Quantitative & categorical fields validated via Pydantic.
3. Human-in-the-Loop: Workflow produces suggestions for human review; NEVER writes to PostgreSQL.
"""

import copy
import logging
from typing import Optional, TypedDict
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

from ..schemas.ai import (
    AIComplaintExtraction,
    AIRiskAssessment,
    AIComplaintEditExtraction,
    ComplaintChanges,
    EDITABLE_COMPLAINT_FIELDS,
)
from .groq_client import get_chat_groq
from .prompts import (
    EXTRACTION_SYSTEM_PROMPT,
    RISK_ASSESSMENT_SYSTEM_PROMPT,
    EDIT_EXTRACTION_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)

VALID_SEVERITIES = {"Low", "Medium", "High", "Critical"}
VALID_PRIORITIES = {"Low", "Medium", "High", "Urgent"}


def assess_complaint_risk(complaint_data: dict, fallback_narrative: str = "") -> AIRiskAssessment:
    """
    Shared helper to perform preliminary QA risk triage on complaint facts via Groq.
    Used by both the intake workflow and the edit reassessment workflow.
    """
    p_name = complaint_data.get("product_name") or "Unknown / Not specified"
    p_str = complaint_data.get("product_strength_grade") or "Unknown / Not specified"
    b_num = complaint_data.get("batch_lot_number") or "Unknown / Not specified"
    qty = complaint_data.get("quantity_affected")
    qty_str = str(qty) if qty is not None else "Unknown / Not specified"
    c_type = complaint_data.get("complaint_type") or "Unknown / General Defect"
    c_name = complaint_data.get("customer_name") or "Unknown / Not specified"
    desc = complaint_data.get("detailed_description") or fallback_narrative or "No details provided"

    complaint_summary = (
        f"Product Name: {p_name}\n"
        f"Dosage Strength / Grade: {p_str}\n"
        f"Batch / Lot Number: {b_num}\n"
        f"Quantity Affected: {qty_str}\n"
        f"Complaint Type: {c_type}\n"
        f"Customer / Reporter: {c_name}\n"
        f"Detailed Description: {desc}\n"
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
    risk = AIRiskAssessment.model_validate(raw_risk) if isinstance(raw_risk, dict) else raw_risk

    severity = (risk.initial_severity or "").strip().capitalize()
    if severity not in VALID_SEVERITIES:
        severity = "Medium"

    priority = (risk.priority or "").strip().capitalize()
    if priority not in VALID_PRIORITIES:
        priority = "Medium"

    return AIRiskAssessment(
        initial_severity=severity,
        priority=priority,
        risk_reasoning=risk.risk_reasoning.strip(),
        recommended_next_actions=[a.strip() for a in risk.recommended_next_actions if a.strip()],
    )


# =====================================================================
# UNIT 5: INTAKE WORKFLOW
# =====================================================================

class ComplaintGraphState(TypedDict, total=False):
    """Explicit state container passed between LangGraph intake nodes."""
    input_text: str
    complaint: Optional[AIComplaintExtraction]
    risk_assessment: Optional[AIRiskAssessment]
    error: Optional[str]


def extract_fields_node(state: ComplaintGraphState) -> ComplaintGraphState:
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
    extraction = (
        AIComplaintExtraction.model_validate(raw_result)
        if isinstance(raw_result, dict)
        else raw_result
    )
    return {"complaint": extraction}


def validate_normalize_node(state: ComplaintGraphState) -> ComplaintGraphState:
    complaint = state.get("complaint")
    if not complaint:
        return {"error": "Missing complaint extraction in state"}

    complaint_dict = complaint.model_dump()
    for field, val in complaint_dict.items():
        if isinstance(val, str):
            trimmed = val.strip()
            complaint_dict[field] = trimmed if trimmed else None

    qty = complaint_dict.get("quantity_affected")
    if qty is not None and qty < 0:
        complaint_dict["quantity_affected"] = None

    if not complaint_dict.get("detailed_description"):
        complaint_dict["detailed_description"] = state.get("input_text", "").strip()

    normalized_complaint = AIComplaintExtraction.model_validate(complaint_dict)
    return {"complaint": normalized_complaint}


def risk_assessment_node(state: ComplaintGraphState) -> ComplaintGraphState:
    complaint = state.get("complaint")
    if not complaint:
        return {"error": "Missing complaint data for risk assessment"}

    normalized_risk = assess_complaint_risk(
        complaint.model_dump(),
        fallback_narrative=state.get("input_text", ""),
    )
    return {"risk_assessment": normalized_risk}


def build_result_node(state: ComplaintGraphState) -> ComplaintGraphState:
    return {
        "complaint": state.get("complaint"),
        "risk_assessment": state.get("risk_assessment"),
    }


def create_complaint_graph():
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


complaint_intake_graph = create_complaint_graph()


# =====================================================================
# UNIT 6: EDIT COMPLAINT WORKFLOW (CONDITIONAL STATEGRAPH)
# =====================================================================

class ComplaintEditGraphState(TypedDict, total=False):
    """Explicit state container passed between LangGraph edit nodes."""
    complaint_id: Optional[str]
    current_complaint: dict
    edit_instruction: str
    extraction: Optional[AIComplaintEditExtraction]
    should_proceed: bool
    is_valid_edit: bool
    needs_clarification: bool
    clarification_message: Optional[str]
    requested_changes: dict
    updated_complaint: dict
    risk_assessment: Optional[AIRiskAssessment]
    error: Optional[str]


def extract_edit_changes_node(state: ComplaintEditGraphState) -> ComplaintEditGraphState:
    """
    Node 1: extract_edit_changes
    Sends the current complaint context and user edit instruction to Groq
    with the structured AIComplaintEditExtraction schema.
    """
    edit_instruction = state.get("edit_instruction", "").strip()
    current = state.get("current_complaint", {})
    if not edit_instruction:
        return {
            "error": "Edit instruction cannot be empty",
            "should_proceed": False,
            "is_valid_edit": False,
            "needs_clarification": True,
            "clarification_message": "Edit instruction cannot be empty.",
            "requested_changes": {},
            "updated_complaint": current,
        }

    # Format existing facts cleanly
    context_lines = [
        f"- {k}: {v}"
        for k, v in current.items()
        if v is not None and v != "" and k not in {"id", "created_at", "updated_at"}
    ]
    current_context = "\n".join(context_lines) if context_lines else "No prior complaint details recorded."

    llm = get_chat_groq(temperature=0.0)
    structured_extractor = llm.with_structured_output(AIComplaintEditExtraction)

    messages = [
        SystemMessage(content=EDIT_EXTRACTION_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"CURRENT COMPLAINT FACTS:\n\"\"\"\n{current_context}\n\"\"\"\n\n"
                f"USER EDIT INSTRUCTION:\n\"\"\"\n{edit_instruction}\n\"\"\"\n\n"
                f"Extract ONLY the explicitly requested changes into the schema."
            )
        ),
    ]

    raw_result = structured_extractor.invoke(messages)
    extraction = (
        AIComplaintEditExtraction.model_validate(raw_result)
        if isinstance(raw_result, dict)
        else raw_result
    )
    return {"extraction": extraction}


def validate_normalize_changes_node(state: ComplaintEditGraphState) -> ComplaintEditGraphState:
    """
    Node 2: validate_normalize_changes
    Enforces:
    1. Ambiguity / clarification check (Unit 6 Adjustment 1):
       If the request is ambiguous, non-edit, or lacks required values,
       we do NOT merge and do NOT reassess risk.
    2. Editable-field allowlist (Unit 6 Adjustment 2):
       Enforces EDITABLE_COMPLAINT_FIELDS. Any unexpected field from LLM is discarded.
    """
    extraction = state.get("extraction")
    current = state.get("current_complaint", {})

    if not extraction:
        return {
            "should_proceed": False,
            "is_valid_edit": False,
            "needs_clarification": True,
            "clarification_message": "Failed to parse edit instruction.",
            "requested_changes": {},
            "updated_complaint": current,
        }

    # If extraction flagged clarification or non-edit request:
    if extraction.needs_clarification or not extraction.is_edit_request:
        msg = extraction.clarification_message or (
            "The instruction did not specify a valid complaint modification. "
            "Please provide specific values to update."
        )
        return {
            "should_proceed": False,
            "is_valid_edit": False,
            "needs_clarification": True,
            "clarification_message": msg,
            "requested_changes": {},
            "updated_complaint": current,
        }

    # Enforce EDITABLE_COMPLAINT_FIELDS allowlist strictly
    raw_changes = extraction.changes.model_dump(exclude_unset=True)
    filtered_changes = {}
    for key, val in raw_changes.items():
        if key in EDITABLE_COMPLAINT_FIELDS and val is not None:
            if isinstance(val, str):
                trimmed = val.strip()
                if trimmed:
                    filtered_changes[key] = trimmed
            elif key == "quantity_affected":
                if isinstance(val, int) and val >= 0:
                    filtered_changes[key] = val
            elif hasattr(val, "isoformat"):
                filtered_changes[key] = val.isoformat()
            else:
                filtered_changes[key] = val

    # If no valid allowed fields were identified:
    if not filtered_changes:
        return {
            "should_proceed": False,
            "is_valid_edit": False,
            "needs_clarification": True,
            "clarification_message": (
                extraction.clarification_message
                or "No valid editable complaint fields found in the instruction. Please specify what to update."
            ),
            "requested_changes": {},
            "updated_complaint": current,
        }

    return {
        "should_proceed": True,
        "is_valid_edit": True,
        "needs_clarification": False,
        "clarification_message": None,
        "requested_changes": filtered_changes,
    }


def route_after_edit_validation(state: ComplaintEditGraphState) -> str:
    """
    Conditional router (Unit 6 Adjustment 1):
    If should_proceed is True -> proceeds to merge_changes & reassess_risk.
    Otherwise -> skips merge and risk reassessment directly to build_edit_proposal.
    """
    if state.get("should_proceed"):
        return "merge_changes"
    return "build_edit_proposal"


def merge_changes_node(state: ComplaintEditGraphState) -> ComplaintEditGraphState:
    """
    Node 3: merge_changes
    Merges filtered changes onto a copy of current_complaint.
    Strictly preserves all unmentioned fields.
    """
    current = copy.deepcopy(state.get("current_complaint", {}))
    changes = state.get("requested_changes", {})

    merged = copy.deepcopy(current)
    for field, new_val in changes.items():
        merged[field] = new_val

    return {"updated_complaint": merged}


def reassess_risk_node(state: ComplaintEditGraphState) -> ComplaintEditGraphState:
    """
    Node 4: reassess_risk
    Recalculates a fresh preliminary risk assessment on the updated complaint facts.
    """
    updated = state.get("updated_complaint", {})
    instruction = state.get("edit_instruction", "")

    risk = assess_complaint_risk(updated, fallback_narrative=instruction)
    return {"risk_assessment": risk}


def build_edit_proposal_node(state: ComplaintEditGraphState) -> ComplaintEditGraphState:
    """
    Node 5: build_edit_proposal
    Constructs the final proposal payload. Zero database writes.
    """
    return {
        "complaint_id": state.get("complaint_id"),
        "is_valid_edit": state.get("is_valid_edit", True),
        "needs_clarification": state.get("needs_clarification", False),
        "clarification_message": state.get("clarification_message"),
        "original_complaint": state.get("current_complaint", {}),
        "requested_changes": state.get("requested_changes", {}),
        "updated_complaint": state.get("updated_complaint", state.get("current_complaint", {})),
        "risk_assessment": state.get("risk_assessment"),
    }


def create_complaint_edit_graph():
    """
    Builds and compiles the conditional LangGraph workflow for AI complaint editing.
    Conditional flow:
    START -> extract_edit_changes -> validate_normalize_changes
        -> (if valid) merge_changes -> reassess_risk -> build_edit_proposal -> END
        -> (if invalid / ambiguous) build_edit_proposal -> END
    """
    workflow = StateGraph(ComplaintEditGraphState)

    workflow.add_node("extract_edit_changes", extract_edit_changes_node)
    workflow.add_node("validate_normalize_changes", validate_normalize_changes_node)
    workflow.add_node("merge_changes", merge_changes_node)
    workflow.add_node("reassess_risk", reassess_risk_node)
    workflow.add_node("build_edit_proposal", build_edit_proposal_node)

    workflow.add_edge(START, "extract_edit_changes")
    workflow.add_edge("extract_edit_changes", "validate_normalize_changes")
    workflow.add_conditional_edges(
        "validate_normalize_changes",
        route_after_edit_validation,
        {
            "merge_changes": "merge_changes",
            "build_edit_proposal": "build_edit_proposal",
        },
    )
    workflow.add_edge("merge_changes", "reassess_risk")
    workflow.add_edge("reassess_risk", "build_edit_proposal")
    workflow.add_edge("build_edit_proposal", END)

    return workflow.compile()


complaint_edit_graph = create_complaint_edit_graph()

