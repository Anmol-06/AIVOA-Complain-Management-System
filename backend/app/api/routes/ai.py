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
from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError

from ...schemas.ai import (
    AIComplaintIntakeRequest,
    AIComplaintIntakeResponse,
)
from ...ai.groq_client import GroqConfigurationError, is_groq_configured
from ...ai.complaint_graph import complaint_intake_graph

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI Intake"])


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
        # ainvoke runs the LangGraph state graph asynchronously
        result = await complaint_intake_graph.ainvoke({"input_text": clean_text})
    except GroqConfigurationError as e:
        logger.error(f"Groq configuration error during AI intake: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error executing AI intake workflow: {e}", exc_info=True)
        # Never expose raw exception strings that might contain credentials
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
