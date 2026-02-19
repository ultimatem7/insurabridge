"""Encounter Model"""

from datetime import datetime
from sqlalchemy import String, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Encounter(Base):
    """Clinical encounter."""
    
    __tablename__ = "encounters"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    
    # FHIR identifier
    fhir_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    fhir_system: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Encounter details
    encounter_type: Mapped[str] = mapped_column(String(50), nullable=False)  # inpatient, outpatient, emergency
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # planned, arrived, in-progress, finished
    encounter_class: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Timing
    start_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_datetime: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Provider info
    provider_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_npi: Mapped[str | None] = mapped_column(String(20), nullable=True)
    facility_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Place of service
    location_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    place_of_service: Mapped[str | None] = mapped_column(String(10), nullable=True)  # CMS POS code
    
    # Clinical data
    reason_codes: Mapped[list | None] = mapped_column(JSON, nullable=True)
    diagnoses: Mapped[list | None] = mapped_column(JSON, nullable=True)
    procedures: Mapped[list | None] = mapped_column(JSON, nullable=True)
    clinical_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Raw FHIR data
    fhir_resource: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Claim status
    has_claim: Mapped[bool] = mapped_column(default=False)
    claim_generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<Encounter {self.fhir_id} - {self.encounter_type}>"
