"""
FHIR Resource Normalizer
Converts FHIR R4 resources to internal schema
"""

from typing import Dict, Any, List
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


class FHIRNormalizer:
    """
    Normalizes FHIR R4 resources to consistent internal format.
    
    Handles variations across different EHR implementations.
    """
    
    def normalize_encounter_data(self, encounter_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize complete encounter dataset.
        
        Args:
            encounter_data: Raw FHIR resources from EHR
        
        Returns:
            Normalized data structure
        """
        return {
            "patient": self.normalize_patient(encounter_data.get("patient")),
            "encounter": self.normalize_encounter(encounter_data.get("encounter")),
            "conditions": self.normalize_conditions(encounter_data.get("conditions", [])),
            "procedures": self.normalize_procedures(encounter_data.get("procedures", [])),
            "observations": self.normalize_observations(encounter_data.get("observations", [])),
            "clinical_notes_text": self._extract_clinical_notes(encounter_data.get("clinical_notes", [])),
            "medications": self.normalize_medications(encounter_data.get("medications", [])),
        }
    
    def normalize_patient(self, patient: Dict[str, Any] | None) -> Dict[str, Any]:
        """Normalize FHIR Patient resource."""
        if not patient:
            return {}
        
        # Extract name
        name = ""
        names = patient.get("name", [])
        if names:
            name_obj = names[0]
            given = " ".join(name_obj.get("given", []))
            family = name_obj.get("family", "")
            name = f"{given} {family}".strip()
        
        # Calculate age
        age = None
        dob_str = patient.get("birthDate")
        if dob_str:
            try:
                dob = datetime.fromisoformat(dob_str.replace("Z", "+00:00"))
                age = (datetime.now() - dob).days // 365
            except Exception:
                pass
        
        # Extract address
        address = None
        addresses = patient.get("address", [])
        if addresses:
            addr = addresses[0]
            address = {
                "line": " ".join(addr.get("line", [])),
                "city": addr.get("city"),
                "state": addr.get("state"),
                "postal_code": addr.get("postalCode"),
            }
        
        return {
            "id": patient.get("id"),
            "mrn": self._extract_identifier(patient, "MR"),
            "name": name,
            "date_of_birth": dob_str,
            "age": age,
            "gender": patient.get("gender"),
            "address": address,
            "phone": self._extract_telecom(patient, "phone"),
            "email": self._extract_telecom(patient, "email"),
        }
    
    def normalize_encounter(self, encounter: Dict[str, Any] | None) -> Dict[str, Any]:
        """Normalize FHIR Encounter resource."""
        if not encounter:
            return {}
        
        # Extract period
        period = encounter.get("period", {})
        start = period.get("start")
        end = period.get("end")
        
        # Extract class
        encounter_class = encounter.get("class", {})
        class_code = encounter_class.get("code", "AMB")
        
        # Extract type
        encounter_type = "outpatient"
        types = encounter.get("type", [])
        if types and types[0].get("coding"):
            type_display = types[0]["coding"][0].get("display", "").lower()
            if "inpatient" in type_display:
                encounter_type = "inpatient"
            elif "emergency" in type_display:
                encounter_type = "emergency"
        
        # Extract provider
        provider_name = None
        provider_npi = None
        participants = encounter.get("participant", [])
        for participant in participants:
            individual = participant.get("individual", {})
            if individual.get("reference"):
                provider_name = individual.get("display")
                # NPI would typically come from Practitioner resource
                break
        
        # Place of service mapping
        pos_map = {
            "AMB": "11",  # Office
            "EMER": "23",  # Emergency Room
            "IMP": "21",  # Inpatient Hospital
            "HH": "12",  # Home
        }
        place_of_service = pos_map.get(class_code, "11")
        
        return {
            "id": encounter.get("id"),
            "status": encounter.get("status"),
            "type": encounter_type,
            "class": class_code,
            "start_datetime": start,
            "end_datetime": end,
            "provider_name": provider_name,
            "provider_npi": provider_npi,
            "facility_name": self._extract_location(encounter),
            "place_of_service": place_of_service,
        }
    
    def normalize_conditions(self, conditions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize FHIR Condition resources (diagnoses)."""
        normalized = []
        
        for condition in conditions:
            code_data = self._extract_coding(condition.get("code", {}), "ICD-10")
            if not code_data:
                continue
            
            normalized.append({
                "id": condition.get("id"),
                "code": code_data["code"],
                "display": code_data["display"],
                "system": code_data["system"],
                "clinical_status": condition.get("clinicalStatus", {}).get("coding", [{}])[0].get("code"),
                "verification_status": condition.get("verificationStatus", {}).get("coding", [{}])[0].get("code"),
                "onset_datetime": condition.get("onsetDateTime"),
                "recorded_date": condition.get("recordedDate"),
            })
        
        return normalized
    
    def normalize_procedures(self, procedures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize FHIR Procedure resources."""
        normalized = []
        
        for procedure in procedures:
            code_data = self._extract_coding(procedure.get("code", {}), "CPT")
            if not code_data:
                continue
            
            normalized.append({
                "id": procedure.get("id"),
                "code": code_data["code"],
                "display": code_data["display"],
                "system": code_data["system"],
                "status": procedure.get("status"),
                "performed_datetime": self._extract_performed_datetime(procedure),
            })
        
        return normalized
    
    def normalize_observations(self, observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize FHIR Observation resources."""
        normalized = []
        
        for obs in observations:
            code_data = self._extract_coding(obs.get("code", {}), "LOINC")
            if not code_data:
                continue
            
            value, unit = self._extract_value(obs)
            
            normalized.append({
                "id": obs.get("id"),
                "code": code_data["code"],
                "display": code_data["display"],
                "system": code_data["system"],
                "value": value,
                "unit": unit,
                "status": obs.get("status"),
                "effective_datetime": obs.get("effectiveDateTime"),
            })
        
        return normalized
    
    def normalize_medications(self, medications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize FHIR MedicationRequest resources."""
        normalized = []
        
        for med in medications:
            medication_code = med.get("medicationCodeableConcept", {})
            code_data = self._extract_coding(medication_code, "RxNorm")
            
            if not code_data:
                continue
            
            normalized.append({
                "id": med.get("id"),
                "code": code_data["code"],
                "display": code_data["display"],
                "status": med.get("status"),
                "intent": med.get("intent"),
                "authored_on": med.get("authoredOn"),
            })
        
        return normalized
    
    def _extract_coding(self, codeable_concept: Dict[str, Any], preferred_system: str | None = None) -> Dict[str, str] | None:
        """Extract code from CodeableConcept."""
        if not codeable_concept:
            return None
        
        codings = codeable_concept.get("coding", [])
        if not codings:
            return None
        
        # Try to find preferred system
        if preferred_system:
            for coding in codings:
                system = coding.get("system", "")
                if preferred_system.lower() in system.lower():
                    return {
                        "code": coding.get("code"),
                        "display": coding.get("display", ""),
                        "system": system,
                    }
        
        # Fallback to first coding
        coding = codings[0]
        return {
            "code": coding.get("code"),
            "display": coding.get("display", ""),
            "system": coding.get("system", ""),
        }
    
    def _extract_identifier(self, resource: Dict[str, Any], type_code: str) -> str | None:
        """Extract identifier of specific type."""
        identifiers = resource.get("identifier", [])
        for identifier in identifiers:
            type_obj = identifier.get("type", {})
            codings = type_obj.get("coding", [])
            for coding in codings:
                if coding.get("code") == type_code:
                    return identifier.get("value")
        return None
    
    def _extract_telecom(self, resource: Dict[str, Any], system: str) -> str | None:
        """Extract telecom value (phone/email)."""
        telecoms = resource.get("telecom", [])
        for telecom in telecoms:
            if telecom.get("system") == system:
                return telecom.get("value")
        return None
    
    def _extract_location(self, encounter: Dict[str, Any]) -> str | None:
        """Extract facility name from encounter."""
        locations = encounter.get("location", [])
        if locations:
            location = locations[0].get("location", {})
            return location.get("display")
        return None
    
    def _extract_performed_datetime(self, procedure: Dict[str, Any]) -> str | None:
        """Extract procedure performed datetime."""
        if "performedDateTime" in procedure:
            return procedure["performedDateTime"]
        elif "performedPeriod" in procedure:
            return procedure["performedPeriod"].get("start")
        return None
    
    def _extract_value(self, observation: Dict[str, Any]) -> tuple[Any, str | None]:
        """Extract observation value and unit."""
        if "valueQuantity" in observation:
            qty = observation["valueQuantity"]
            return qty.get("value"), qty.get("unit")
        elif "valueString" in observation:
            return observation["valueString"], None
        elif "valueBoolean" in observation:
            return observation["valueBoolean"], None
        return None, None
    
    def _extract_clinical_notes(self, documents: List[Dict[str, Any]]) -> str:
        """Extract text from DocumentReference resources."""
        notes = []
        
        for doc in documents[:5]:  # Limit to 5 documents
            content_list = doc.get("content", [])
            for content in content_list:
                attachment = content.get("attachment", {})
                # In real implementation, would fetch document data
                # For now, just use description
                if attachment.get("data"):
                    # Base64 decode if needed
                    pass
                elif attachment.get("url"):
                    # Fetch from URL
                    pass
                
                # Use description as fallback
                description = doc.get("description") or attachment.get("title", "")
                if description:
                    notes.append(description)
        
        return "\n\n".join(notes)
