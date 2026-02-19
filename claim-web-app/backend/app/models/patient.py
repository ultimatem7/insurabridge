"""Patient Model"""

from datetime import datetime
from sqlalchemy import String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Patient(Base):
    """Patient demographic and insurance information."""
    
    __tablename__ = "patients"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # FHIR identifier
    fhir_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    fhir_system: Mapped[str] = mapped_column(String(255), nullable=False)  # EHR system
    
    # Demographics
    mrn: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    # Contact
    address: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Insurance
    insurance_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Raw FHIR data
    fhir_resource: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<Patient {self.first_name} {self.last_name} ({self.mrn})>"
