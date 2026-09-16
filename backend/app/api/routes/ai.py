"""
FastAPI Router for AI-Powered Complaint Intake.

Endpoints:
- POST /api/ai/complaint-intake: Ingests unstructured complaint text, executes
  the LangGraph extraction & risk triage workflow, and returns structured data
  for human review.

Security & Governance Invariants:
- NEVER exposes Groq API keys.
- NEVER writes directly to PostgreSQL (Human-in-the-Loop requirement).
- Fails gracefully with HTTP 503 if AI configuration is missing.
"""

import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...db.models import Complaint
from ...schemas.ai import (
    AIComplaintIntakeRequest,
    AIComplaintIntakeResponse,
    AIComplaintEditRequest,
    AIComplaintEditProposal,
)
from ...ai.groq_client import GroqConfigurationError, is_groq_configured
from ...ai.complaint_graph import complaint_intake_graph, complaint_edit_graph

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI Intake & Edit"])


@router.post(
    "/complaint-intake",
    response_model=AIComplaintIntakeResponse,
    status_code=status.HTTP_200_OK,
    summary="Process natural language complaint narrative with AI",
    description=(
        "Executes a LangGraph workflow to extract structured pharmaceutical complaint fields "
        "and perform initial preliminary risk triage. Returned data requires human QA review "
        "and is NOT automatically committed to PostgreSQL."
    ),
)
async def process_complaint_intake(request: AIComplaintIntakeRequest):
    """
    Ingests unstructured narrative text and executes LangGraph + Groq extraction workflow.
    """
    clean_text = request.text.strip()
    if not clean_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Complaint text cannot be empty or only whitespace.",
        )

    # 1. Configuration check
    if not is_groq_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Groq AI service is not configured. Please specify GROQ_API_KEY and "
                "GROQ_MODEL in backend/.env."
            ),
        )

    # 2. Invoke LangGraph workflow
    try:
        result = await complaint_intake_graph.ainvoke({"input_text": clean_text})
    except GroqConfigurationError as e:
        logger.error(f"Groq configuration error during AI intake: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error executing AI intake workflow: {e}", exc_info=True)
        error_type = type(e).__name__
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI workflow failed during execution ({error_type}). Please try again.",
        )

    # 3. Check for workflow error
    if result.get("error"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=result["error"],
        )

    complaint = result.get("complaint")
    risk_assessment = result.get("risk_assessment")

    if not complaint or not risk_assessment:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI workflow failed to produce complete extraction and risk assessment.",
        )

    # 4. Return structured response for human review
    return AIComplaintIntakeResponse(
        complaint=complaint,
        risk_assessment=risk_assessment,
    )


@router.post(
    "/complaint-edit",
    response_model=AIComplaintEditProposal,
    status_code=status.HTTP_200_OK,
    summary="Propose structured edits to a complaint from natural language instruction",
    description=(
        "Analyzes an existing complaint and natural-language edit instruction using LangGraph. "
        "Extracts ONLY the requested changes, validates against an editable allowlist, "
        "and recalculates preliminary risk. Returned proposal requires human QA review and "
        "is NEVER written directly to PostgreSQL."
    ),
)
async def process_complaint_edit(
    request: AIComplaintEditRequest,
    db: Session = Depends(get_db),
):
    """
    Ingests natural language correction and outputs structured change proposal for human review.
    """
    clean_instruction = request.edit_instruction.strip()
    if not clean_instruction:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Edit instruction cannot be empty or only whitespace.",
        )

    # 1. Authoritative Complaint Resolution (Unit 6 Adjustment 3)
    current_data: dict = {}
    if request.complaint_id:
        try:
            complaint_uuid = UUID(request.complaint_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: '{request.complaint_id}'",
            )

        db_complaint = db.query(Complaint).filter(Complaint.id == complaint_uuid).first()
        if not db_complaint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Complaint with ID '{request.complaint_id}' was not found in PostgreSQL.",
            )

        current_data = {
            "id": str(db_complaint.id),
            "complaint_source": db_complaint.complaint_source,
            "customer_name": db_complaint.customer_name,
            "product_name": db_complaint.product_name,
            "product_strength_grade": db_complaint.product_strength_grade,
            "batch_lot_number": db_complaint.batch_lot_number,
            "manufacturing_date": db_complaint.manufacturing_date.isoformat() if db_complaint.manufacturing_date else None,
            "expiry_date": db_complaint.expiry_date.isoformat() if db_complaint.expiry_date else None,
            "quantity_affected": db_complaint.quantity_affected,
            "complaint_type": db_complaint.complaint_type,
            "complaint_date": db_complaint.complaint_date.isoformat() if db_complaint.complaint_date else None,
            "detailed_description": db_complaint.detailed_description,
            "initial_severity": db_complaint.initial_severity,
            "priority": db_complaint.priority,
        }
    elif request.current_complaint is not None:
        current_data = request.current_complaint
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either 'complaint_id' (for persisted complaints) or 'current_complaint' (for unsaved complaints) must be provided.",
        )

    # 2. Configuration check
    if not is_groq_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Groq AI service is not configured. Please specify GROQ_API_KEY and GROQ_MODEL in backend/.env.",
        )

    # 3. Invoke LangGraph edit workflow
    try:
        result = await complaint_edit_graph.ainvoke({
            "complaint_id": request.complaint_id,
            "current_complaint": current_data,
            "edit_instruction": clean_instruction,
        })
    except GroqConfigurationError as e:
        logger.error(f"Groq configuration error during AI edit: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error executing AI edit workflow: {e}", exc_info=True)
        error_type = type(e).__name__
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI edit workflow failed during execution ({error_type}). Please try again.",
        )

    # 4. Check for unrecoverable workflow error
    if result.get("error") and not result.get("needs_clarification"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=result["error"],
        )

    # 5. Return structured proposal for human review (Zero DB Writes)
    return AIComplaintEditProposal(
        complaint_id=request.complaint_id,
        is_valid_edit=result.get("is_valid_edit", True),
        needs_clarification=result.get("needs_clarification", False),
        clarification_message=result.get("clarification_message"),
        original_complaint=result.get("original_complaint", current_data),
        requested_changes=result.get("requested_changes", {}),
        updated_complaint=result.get("updated_complaint", current_data),
        risk_assessment=result.get("risk_assessment"),
    )

