from pydantic import BaseModel, field_validator, model_validator
from datetime import date
from typing import Literal, List
import re

ALLOWED_HOSPITALS = {f"H{i}" for i in range(1, 11)}
ALLOWED_PROCEDURES = {"P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"}


class ClaimInput(BaseModel):
    claim_id: str
    hospital_id: str
    patient_id: str
    procedure_code: str
    package_rate: float
    claim_amount: float
    admission_date: date
    discharge_date: date
    is_inpatient: bool

    @field_validator("claim_amount")
    @classmethod
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError("claim_amount must be greater than 0")
        return v

    @field_validator("package_rate")
    @classmethod
    def rate_positive(cls, v):
        if v <= 0:
            raise ValueError("package_rate must be greater than 0")
        return v

    @field_validator("hospital_id")
    @classmethod
    def valid_hospital(cls, v):
        pattern = r"^H-[A-Z]{2}-\d{3}$"
        if not re.match(pattern, v):
            raise ValueError("hospital_id must follow format H-XX-000")
        return v

    @field_validator("procedure_code")
    @classmethod
    def valid_procedure(cls, v):
        if v not in ALLOWED_PROCEDURES:
            raise ValueError(f"procedure_code '{v}' not in allowed set {sorted(ALLOWED_PROCEDURES)}")
        return v

    @model_validator(mode="after")
    def discharge_after_admission(self):
        if self.discharge_date < self.admission_date:
            raise ValueError("discharge_date must be >= admission_date")
        return self


# --- Legacy sub-schemas (preserved) ---
class RuleTriggersSchema(BaseModel):
    zero_day_inpatient: bool
    high_amount_zscore: bool
    repeat_procedure_flag: bool
    near_package_ceiling: bool
    high_patient_frequency: bool


class RiskBreakdownSchema(BaseModel):
    rule_contribution_percent: float
    anomaly_contribution_percent: float


# --- New Composite Intelligence sub-schemas ---
class SignalVectorSchema(BaseModel):
    rule_weight: float
    anomaly_weight: float
    rule_trigger_count: int
    anomaly_intensity_band: Literal["Mild Deviation", "Elevated Anomaly", "Extreme Outlier"]


class KnowledgeSignalSchema(BaseModel):
    signal_code: str
    signal_type: Literal["DETERMINISTIC", "STATISTICAL"]
    severity_weight: float
    description: str
    fraud_category: Literal["PHANTOM", "UPCODING", "REPEAT_ABUSE", "ANOMALY"]


class IntelligenceResponse(BaseModel):
    claim_id: str

    # Legacy fields
    anomaly_score_norm: float
    rule_score_norm: float
    final_risk_score: float
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    risk_breakdown: RiskBreakdownSchema
    rule_triggers: RuleTriggersSchema
    fraud_pattern_detected: Literal["PHANTOM", "UPCODING", "REPEAT_ABUSE", "MIXED", "NONE"]
    investigation_priority: Literal["AUTO_APPROVE", "REVIEW", "ESCALATE"]
    explanation: str

    # New composite intelligence fields
    composite_index: int
    threat_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    confidence_score: int
    enforcement_state: Literal["CLEAR", "MONITOR", "ESCALATED", "HARD_STOP"]
    signal_vector: SignalVectorSchema
    knowledge_signals: List[KnowledgeSignalSchema]


class IntelligenceMetricsResponse(BaseModel):
    total_scored: int
    threat_level_distribution: dict
    hard_stop_count: int
    average_composite_index: float
    anomaly_band_distribution: dict


class HospitalLossItem(BaseModel):
    hospital_id: str
    total_claims: int
    high_risk_claims: int
    total_claim_amount: float
    risk_weighted_loss: float
    fraud_exposure_percentage: float

HospitalLossResponse = List[HospitalLossItem]
