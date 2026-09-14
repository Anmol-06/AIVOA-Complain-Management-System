from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...db.models import Complaint
from ...schemas.complaint import (
    ComplaintCreate,
    ComplaintUpdate,
    ComplaintResponse,
)

router = APIRouter(
    prefix="/api/complaints",
    tags=["Complaints"],
)


@router.post(
    "",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new customer complaint record",
)
def create_complaint(
    complaint_in: ComplaintCreate,
    db: Session = Depends(get_db),
):
    """
    Creates a new complaint in PostgreSQL.
    Validates payload using ComplaintCreate schema and returns the persisted record.
    """
    # Exclude unset fields or pass all provided fields (defaults to None for missing)
    complaint_data = complaint_in.model_dump()
    complaint = Complaint(**complaint_data)
    
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint


@router.get(
    "",
    response_model=List[ComplaintResponse],
    status_code=status.HTTP_200_OK,
    summary="List all complaint records (newest first)",
)
def list_complaints(
    db: Session = Depends(get_db),
):
    """
    Retrieves all customer complaints from PostgreSQL, ordered by created_at descending.
    """
    complaints = db.query(Complaint).order_by(Complaint.created_at.desc()).all()
    return complaints


@router.get(
    "/{complaint_id}",
    response_model=ComplaintResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a single complaint by UUID",
)
def get_complaint(
    complaint_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Retrieves a single complaint record by its unique UUID.
    Returns HTTP 404 if the record does not exist.
    """
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint with ID '{complaint_id}' was not found.",
        )
    return complaint


@router.patch(
    "/{complaint_id}",
    response_model=ComplaintResponse,
    status_code=status.HTTP_200_OK,
    summary="Partially update a complaint record",
)
def update_complaint(
    complaint_id: UUID,
    complaint_update: ComplaintUpdate,
    db: Session = Depends(get_db),
):
    """
    Applies a partial update to an existing complaint in PostgreSQL.
    
    ARCHITECTURAL RULE:
    The database record is authoritative. Only fields explicitly supplied
    in the PATCH payload (`exclude_unset=True`) are updated.
    Omitted fields retain their existing values and are NEVER overwritten with None.
    """
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint with ID '{complaint_id}' was not found.",
        )

    # Extract only fields that were explicitly set in the incoming request
    update_data = complaint_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(complaint, field, value)

    db.commit()
    db.refresh(complaint)
    return complaint
