"""
FHIR R4 Ingestion

Parses FHIR resources from EPIC and other EHR systems.
Normalizes to internal canonical format.
"""

from datetime import datetime
from typing import Any
from enum import Enum

import structlog
from pydantic import BaseModel, Field
from fhir.resources.R4B.patient import Patient as FHIRPatient
from fhir.resources.R4B.encounter import Encounter as FHIREncounter
from fhir.resources.R4B.condition import Condition as FHIRCondition
from fhir.resources.R4B.procedure import Procedure as FHIRProcedure
from fhir.resources.R4B.observation import Observation as FHIRObservation
from fhir.resources.R4B.claim import Claim as FHIRClaim
from fhir.resources.R4B.coverage import Coverage as FHIRCoverage
from fhir.resources.R4B.diagnosticreport import DiagnosticReport as FHIRDiagnosticReport

from app.core.security import generate_secure_id

logger = structlog.get_logger(__name__)


class ResourceType(str, Enum):
    """Supported FHIR resource types."""
    PATIENT = "Patient"
    ENCOUNTER = "Encounter"
    CONDITION = "Condition"
    PROCEDURE = "Procedure"
    OBSERVATION = "Observation"
    DIAGNOSTIC_REPORT = "DiagnosticReport"
    CLAIM = "Claim"
    COVERAGE = "Coverage"


# Canonical models (internal representation)

class CanonicalPatient(BaseModel):
    """Internal patient representation."""
    id: str = Field(default_factory=generate_secure_id)
    fhir_id: str | None = None
    mrn: str | None = None
    
    first_name: str
    last_name: str
    date_of_birth: str  # YYYY-MM-DD
    gender: str | None = None
    
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    phone: str | None = None
    
    # Insurance
    primary_insurance: dict | None = None


class CanonicalEncounter(BaseModel):
    """Internal encounter representation."""
    id: str = Field(default_factory=generate_secure_id)
    fhir_id: str | None = None
    patient_id: str
    
    encounter_type: str  # inpatient, outpatient, emergency, etc.
    status: str
    
    start_date: datetime
    end_date: datetime | None = None
    
    attending_provider: str | None = None
    facility_name: str | None = None
    place_of_service: str | None = None
    
    # Clinical data
    diagnoses: list[dict] = []
    procedures: list[dict] = []
    observations: list[dict] = []
    notes: list[str] = []


class CanonicalCondition(BaseModel):
    """Internal condition/diagnosis representation."""
    id: str = Field(default_factory=generate_secure_id)
    fhir_id: str | None = None
    encounter_id: str | None = None
    patient_id: str
    
    code: str  # ICD-10 or SNOMED
    code_system: str
    display: str
    
    clinical_status: str | None = None  # active, resolved, etc.
    verification_status: str | None = None
    
    onset_date: datetime | None = None
    abatement_date: datetime | None = None
    
    recorded_date: datetime | None = None
    recorder: str | None = None
    
    # Additional context
    body_site: str | None = None
    severity: str | None = None
    note: str | None = None


class CanonicalProcedure(BaseModel):
    """Internal procedure representation."""
    id: str = Field(default_factory=generate_secure_id)
    fhir_id: str | None = None
    encounter_id: str | None = None
    patient_id: str
    
    code: str  # CPT, HCPCS, ICD-10-PCS
    code_system: str
    display: str
    
    status: str
    performed_date: datetime | None = None
    
    performer: str | None = None
    location: str | None = None
    
    body_site: str | None = None
    outcome: str | None = None
    note: str | None = None


class FHIRParser:
    """
    Parses FHIR R4 resources into canonical internal format.
    
    Compatible with EPIC App Orchard FHIR endpoints.
    """
    
    def parse_patient(self, resource: dict | FHIRPatient) -> CanonicalPatient:
        """Parse a FHIR Patient resource."""
        if isinstance(resource, dict):
            patient = FHIRPatient.model_validate(resource)
        else:
            patient = resource
        
        # Extract name
        first_name = ""
        last_name = ""
        if patient.name:
            name = patient.name[0]
            if name.given:
                first_name = name.given[0]
            if name.family:
                last_name = name.family
        
        # Extract address
        address = None
        if patient.address:
            address = patient.address[0]
        
        # Extract phone
        phone = None
        if patient.telecom:
            for telecom in patient.telecom:
                if telecom.system == "phone":
                    phone = telecom.value
                    break
        
        # Extract MRN
        mrn = None
        if patient.identifier:
            for identifier in patient.identifier:
                if identifier.type and identifier.type.coding:
                    for coding in identifier.type.coding:
                        if coding.code == "MR":
                            mrn = identifier.value
                            break
        
        return CanonicalPatient(
            fhir_id=patient.id,
            mrn=mrn,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=patient.birthDate.isoformat() if patient.birthDate else "",
            gender=patient.gender,
            address_line1=address.line[0] if address and address.line else None,
            address_line2=address.line[1] if address and address.line and len(address.line) > 1 else None,
            city=address.city if address else None,
            state=address.state if address else None,
            zip_code=address.postalCode if address else None,
            phone=phone,
        )
    
    def parse_encounter(self, resource: dict | FHIREncounter, patient_id: str) -> CanonicalEncounter:
        """Parse a FHIR Encounter resource."""
        if isinstance(resource, dict):
            encounter = FHIREncounter.model_validate(resource)
        else:
            encounter = resource
        
        # Map encounter class to type
        encounter_type = "outpatient"
        if encounter.class_fhir:
            class_code = encounter.class_fhir.code
            if class_code == "IMP":
                encounter_type = "inpatient"
            elif class_code == "EMER":
                encounter_type = "emergency"
            elif class_code == "AMB":
                encounter_type = "outpatient"
        
        # Extract dates
        start_date = None
        end_date = None
        if encounter.period:
            start_date = encounter.period.start
            end_date = encounter.period.end
        
        # Extract provider
        attending = None
        if encounter.participant:
            for participant in encounter.participant:
                if participant.individual and participant.individual.display:
                    attending = participant.individual.display
                    break
        
        # Extract facility
        facility = None
        if encounter.serviceProvider and encounter.serviceProvider.display:
            facility = encounter.serviceProvider.display
        
        return CanonicalEncounter(
            fhir_id=encounter.id,
            patient_id=patient_id,
            encounter_type=encounter_type,
            status=encounter.status,
            start_date=start_date or datetime.now(),
            end_date=end_date,
            attending_provider=attending,
            facility_name=facility,
        )
    
    def parse_condition(self, resource: dict | FHIRCondition, patient_id: str) -> CanonicalCondition:
        """Parse a FHIR Condition resource."""
        if isinstance(resource, dict):
            condition = FHIRCondition.model_validate(resource)
        else:
            condition = resource
        
        # Extract code
        code = ""
        code_system = ""
        display = ""
        if condition.code and condition.code.coding:
            coding = condition.code.coding[0]
            code = coding.code or ""
            code_system = coding.system or ""
            display = coding.display or ""
        
        # Extract encounter reference
        encounter_id = None
        if condition.encounter and condition.encounter.reference:
            encounter_id = condition.encounter.reference.split("/")[-1]
        
        # Extract dates
        onset = None
        if condition.onsetDateTime:
            onset = condition.onsetDateTime
        
        return CanonicalCondition(
            fhir_id=condition.id,
            encounter_id=encounter_id,
            patient_id=patient_id,
            code=code,
            code_system=code_system,
            display=display,
            clinical_status=condition.clinicalStatus.coding[0].code if condition.clinicalStatus and condition.clinicalStatus.coding else None,
            verification_status=condition.verificationStatus.coding[0].code if condition.verificationStatus and condition.verificationStatus.coding else None,
            onset_date=onset,
            recorded_date=condition.recordedDate,
        )
    
    def parse_procedure(self, resource: dict | FHIRProcedure, patient_id: str) -> CanonicalProcedure:
        """Parse a FHIR Procedure resource."""
        if isinstance(resource, dict):
            procedure = FHIRProcedure.model_validate(resource)
        else:
            procedure = resource
        
        # Extract code
        code = ""
        code_system = ""
        display = ""
        if procedure.code and procedure.code.coding:
            coding = procedure.code.coding[0]
            code = coding.code or ""
            code_system = coding.system or ""
            display = coding.display or ""
        
        # Extract encounter reference
        encounter_id = None
        if procedure.encounter and procedure.encounter.reference:
            encounter_id = procedure.encounter.reference.split("/")[-1]
        
        # Extract date
        performed_date = None
        if procedure.performedDateTime:
            performed_date = procedure.performedDateTime
        elif procedure.performedPeriod and procedure.performedPeriod.start:
            performed_date = procedure.performedPeriod.start
        
        # Extract performer
        performer = None
        if procedure.performer:
            for perf in procedure.performer:
                if perf.actor and perf.actor.display:
                    performer = perf.actor.display
                    break
        
        return CanonicalProcedure(
            fhir_id=procedure.id,
            encounter_id=encounter_id,
            patient_id=patient_id,
            code=code,
            code_system=code_system,
            display=display,
            status=procedure.status,
            performed_date=performed_date,
            performer=performer,
        )
    
    def parse_bundle(self, bundle: dict) -> dict[str, list]:
        """
        Parse a FHIR Bundle containing multiple resources.
        
        Returns a dictionary of resource type -> list of canonical objects.
        """
        results = {
            "patients": [],
            "encounters": [],
            "conditions": [],
            "procedures": [],
            "observations": [],
        }
        
        if bundle.get("resourceType") != "Bundle":
            logger.warning("Expected Bundle resource")
            return results
        
        entries = bundle.get("entry", [])
        patient_id = None
        
        # First pass: find patient
        for entry in entries:
            resource = entry.get("resource", {})
            if resource.get("resourceType") == "Patient":
                patient = self.parse_patient(resource)
                results["patients"].append(patient)
                patient_id = patient.id
                break
        
        if not patient_id:
            logger.warning("No patient found in bundle")
            return results
        
        # Second pass: parse other resources
        for entry in entries:
            resource = entry.get("resource", {})
            resource_type = resource.get("resourceType")
            
            try:
                if resource_type == "Encounter":
                    results["encounters"].append(
                        self.parse_encounter(resource, patient_id)
                    )
                elif resource_type == "Condition":
                    results["conditions"].append(
                        self.parse_condition(resource, patient_id)
                    )
                elif resource_type == "Procedure":
                    results["procedures"].append(
                        self.parse_procedure(resource, patient_id)
                    )
            except Exception as e:
                logger.error(
                    "Failed to parse resource",
                    resource_type=resource_type,
                    error=str(e),
                )
        
        return results


# Singleton parser instance
_fhir_parser: FHIRParser | None = None


def get_fhir_parser() -> FHIRParser:
    """Get the FHIR parser instance."""
    global _fhir_parser
    if _fhir_parser is None:
        _fhir_parser = FHIRParser()
    return _fhir_parser

