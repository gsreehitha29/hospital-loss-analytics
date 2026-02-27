from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List

from backend.database import get_db
from backend.schemas import HospitalLossItem
from backend.services.fraud_analytics_service import get_hospital_loss
import logging

logger = logging.getLogger("analytics_router")
router = APIRouter()

@router.get("/hospital-loss", response_model=List[HospitalLossItem])
def hospital_loss(
    range: Optional[str] = Query(None, pattern=r"^(7d|30d|all)$"),
    db: Session = Depends(get_db)
):
    try:
        return get_hospital_loss(db, range)
    except Exception as exc:
        logger.error("Failed to compute hospital loss", exc_info=exc)
        raise HTTPException(status_code=500, detail="Internal server error")
