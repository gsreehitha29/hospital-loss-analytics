"""
fraud_analytics_service.py
--------------------------
Hospital-Level Loss Calculation for PM-JAY Fraud Intelligence System.

Computes risk-weighted financial loss exposure per hospital
using a single optimised SQL JOIN query.

High-risk definition:
  composite_index >= 70  (0–100 scale)
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, case
from sqlalchemy.orm import Session

from backend.models import Claim, FraudAnalysis
from backend.schemas import HospitalLossItem

logger = logging.getLogger("fraud_analytics_service")

# ---------------------------------------------------------------------------
# Time-range helper
# ---------------------------------------------------------------------------

_RANGE_DAYS: dict[str, Optional[int]] = {
    "7d": 7,
    "30d": 30,
    "all": None,
}


def _resolve_since(range_param: Optional[str]) -> Optional[datetime]:
    if range_param is None or range_param == "all":
        return None
    days = _RANGE_DAYS.get(range_param)
    if days is None:
        return None
    return datetime.now(timezone.utc) - timedelta(days=days)


def get_hospital_loss(
    db: Session,
    range_param: Optional[str] = None,
) -> list[HospitalLossItem]:

    since = _resolve_since(range_param)

    # 🔥 Define high-risk condition directly from composite_index
    high_risk_condition = case(
        (FraudAnalysis.composite_index >= 70, 1),
        else_=0
    )

    query = (
        db.query(
            Claim.hospital_id.label("hospital_id"),
            func.count(Claim.claim_id).label("total_claims"),
            func.sum(high_risk_condition).label("high_risk_claims"),
            func.coalesce(func.sum(Claim.claim_amount), 0.0).label("total_claim_amount"),
            func.coalesce(
                func.sum(Claim.claim_amount * FraudAnalysis.final_risk_score),
                0.0
            ).label("risk_weighted_loss"),
        )
        .join(FraudAnalysis, FraudAnalysis.claim_id == Claim.claim_id)
        .filter(FraudAnalysis.final_risk_score.isnot(None))
    )

    if since is not None:
        query = query.filter(Claim.created_at >= since)

    rows = (
        query.group_by(Claim.hospital_id)
        .order_by(
            func.coalesce(
                func.sum(Claim.claim_amount * FraudAnalysis.final_risk_score),
                0.0
            ).desc()
        )
        .all()
    )

    results: list[HospitalLossItem] = []

    for row in rows:
        total_amount = float(row.total_claim_amount)
        risk_loss = float(row.risk_weighted_loss)

        exposure_pct = round((risk_loss / total_amount) * 100, 2) if total_amount > 0 else 0.0

        results.append(
            HospitalLossItem(
                hospital_id=row.hospital_id,
                total_claims=int(row.total_claims),
                high_risk_claims=int(row.high_risk_claims or 0),
                total_claim_amount=round(total_amount, 2),
                risk_weighted_loss=round(risk_loss, 2),
                fraud_exposure_percentage=exposure_pct,
            )
        )

    logger.info(
        "hospital_loss query returned %d hospitals | range=%s",
        len(results),
        range_param or "all",
    )

    return results