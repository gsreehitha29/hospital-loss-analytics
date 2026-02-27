from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database import Base


class Claim(Base):
    __tablename__ = "claims"

    claim_id = Column(String, primary_key=True, index=True)
    hospital_id = Column(String, nullable=False)
    patient_id = Column(String, nullable=False)
    procedure_code = Column(String, nullable=False)
    package_rate = Column(Float, nullable=False)
    claim_amount = Column(Float, nullable=False)
    admission_date = Column(String, nullable=False)
    discharge_date = Column(String, nullable=False)
    is_inpatient = Column(Integer, nullable=False)
    risk_score = Column(Float, nullable=True)
    is_high_risk = Column(Boolean, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    fraud_analysis = relationship("FraudAnalysis", back_populates="claim", uselist=False)


class FraudAnalysis(Base):
    __tablename__ = "fraud_analysis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    claim_id = Column(String, ForeignKey("claims.claim_id"), nullable=False, unique=True, index=True)

    # --- Legacy fields (preserved) ---
    anomaly_score_norm = Column(Float, nullable=False)
    rule_score_norm = Column(Float, nullable=False)
    final_risk_score = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)
    fraud_pattern_detected = Column(String, nullable=False)
    investigation_priority = Column(String, nullable=False)
    rule_triggers = Column(JSON, nullable=False)
    risk_breakdown = Column(JSON, nullable=False)
    explanation = Column(Text, nullable=False)

    # --- New Composite Intelligence fields ---
    composite_index = Column(Integer, nullable=True)
    threat_level = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)
    enforcement_state = Column(String, nullable=True)
    signal_vector = Column(JSON, nullable=True)
    knowledge_signals = Column(JSON, nullable=True)
    hard_stop = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    claim = relationship("Claim", back_populates="fraud_analysis")
