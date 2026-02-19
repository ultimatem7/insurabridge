"""Claim Models"""

from datetime import datetime
from sqlalchemy import String, DateTime, JSON, ForeignKey, Float, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Claim(Base):
    """Generated insurance claim."""
    
    __tablename__ = "claims"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    encounter_id: Mapped[str] = mapped_column(String(36), ForeignKey("encounters.id"), nullable=False, index=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Claim identification
    claim_number: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)
    claim_type: Mapped[str] = mapped_column(String(20), nullable=False, default="professional")  # professional, institutional
    
    # Status
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")  # draft, validated, submitted, paid, denied
    
    # Financial
    total_charges: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    allowed_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    paid_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Provider
    rendering_provider_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rendering_provider_npi: Mapped[str | None] = mapped_column(String(20), nullable=True)
    billing_provider_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    billing_provider_npi: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    # Payer
    payer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payer_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Dates
    service_date_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    service_date_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    submission_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # AI Generation
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    generation_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Evidence and reasoning
    supporting_evidence: Mapped[list | None] = mapped_column(JSON, nullable=True)
    audit_trail: Mapped[list | None] = mapped_column(JSON, nullable=True)
    
    # Review flags
    requires_review: Mapped[bool] = mapped_column(default=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Structured claim data (CMS-1500 format)
    claim_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<Claim {self.claim_number or self.id} - {self.status}>"


class ClaimDiagnosis(Base):
    """Diagnosis code on a claim."""
    
    __tablename__ = "claim_diagnoses"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    claim_id: Mapped[str] = mapped_column(String(36), ForeignKey("claims.id"), nullable=False, index=True)
    
    # ICD-10 code
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    code_system: Mapped[str] = mapped_column(String(50), nullable=False, default="ICD-10-CM")
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Position
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    is_primary: Mapped[bool] = mapped_column(default=False)
    
    # Evidence
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    supporting_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    fhir_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<ClaimDiagnosis {self.code} - {self.description}>"


class ClaimProcedure(Base):
    """Procedure code on a claim."""
    
    __tablename__ = "claim_procedures"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    claim_id: Mapped[str] = mapped_column(String(36), ForeignKey("claims.id"), nullable=False, index=True)
    
    # CPT/HCPCS code
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    code_system: Mapped[str] = mapped_column(String(50), nullable=False, default="CPT")
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Modifiers
    modifiers: Mapped[list | None] = mapped_column(JSON, nullable=True)
    
    # Line details
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    service_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    units: Mapped[float] = mapped_column(Float, default=1.0)
    charge_amount: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Diagnosis pointers
    diagnosis_pointers: Mapped[list | None] = mapped_column(JSON, nullable=True)
    
    # Place of service
    place_of_service: Mapped[str | None] = mapped_column(String(10), nullable=True)
    
    # Evidence
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    supporting_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    fhir_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<ClaimProcedure {self.code} - {self.description}>"
