"""
Insurabridge Demo Backend
A simplified backend for demonstrating the FHIR-to-Claim pipeline
Works with Python 3.14+ without complex dependencies
Uses Ollama with Gemma 4B for narrative claim generation
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import uuid4
import httpx
import json
import re

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "gemma3:4b"  # Using gemma3:4b for better quality output

async def call_ollama(prompt: str, system_prompt: str = "") -> str:
    """Call Ollama API for text generation"""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload = {
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Low temperature for deterministic output
                    "top_p": 0.9,
                }
            }
            if system_prompt:
                payload["system"] = system_prompt
            
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
    except httpx.RequestError as e:
        print(f"Ollama connection error: {e}")
        return None
    except Exception as e:
        print(f"Ollama error: {e}")
        return None

app = FastAPI(
    title="Insurabridge Demo API",
    description="FHIR-to-Claim Pipeline Demo",
    version="1.0.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ Models ============

class EvidenceAtom(BaseModel):
    evidence_id: str
    evidence_type: str
    source_system: str
    document_name: str
    content_excerpt: str
    extracted_value: Optional[str] = None  # Parsed/extracted value (e.g., CPT code, ICD code)
    confidence: float = 1.0

class Diagnosis(BaseModel):
    sequence: int
    code: str
    description: str
    confidence: float
    supporting_evidence: List[str]

class ClaimLine(BaseModel):
    line_number: int
    code: str
    code_type: str
    description: str
    charge_amount: float
    confidence: float
    supporting_evidence: List[str]
    rationale: str

class ClaimResponse(BaseModel):
    id: str
    status: str
    patient_id: Optional[str]
    patient_name: Optional[str]
    total_charges: float
    diagnoses: List[Diagnosis]
    lines: List[ClaimLine]
    evidence_atoms: List[EvidenceAtom]
    created_at: str
    requires_review: bool
    review_reasons: List[str]

class PipelineRequest(BaseModel):
    bridge_url: str = "http://localhost:3000"
    fhir_data: Optional[Dict[str, Any]] = None  # Optional: send FHIR data directly
    claim_type: str = "professional"

class CitedSection(BaseModel):
    """A section of text with inline citations"""
    section_title: str
    content: str  # Contains [EV-xxx] citation markers
    evidence_ids: List[str]  # List of evidence IDs referenced in this section

class NarrativeClaim(BaseModel):
    """A full narrative claim document with Zotero-style citations"""
    claim_id: str
    title: str
    summary: str
    patient_section: CitedSection
    diagnoses_section: CitedSection
    procedures_section: CitedSection
    medical_necessity_section: CitedSection
    billing_summary_section: CitedSection
    evidence_atoms: List[EvidenceAtom]  # Full evidence atoms for citation lookup
    total_charges: float
    status: str
    requires_review: bool
    review_reasons: List[str]
    generated_at: str
    llm_model: str

class NarrativeRequest(BaseModel):
    claim_id: str
    evidence_atoms: List[EvidenceAtom]
    patient_data: Dict[str, Any]
    diagnoses: List[Diagnosis]
    lines: List[ClaimLine]

# ============ FHIR to EvidenceAtom Converter ============

def convert_patient_to_atoms(patient: Dict[str, Any]) -> List[EvidenceAtom]:
    """Convert FHIR Patient resource to EvidenceAtoms - extracts ALL available data"""
    atoms = []
    patient_id = patient.get('id', 'Unknown')
    
    # Full patient record
    atoms.append(EvidenceAtom(
        evidence_id=f"EV-{uuid4().hex[:8]}",
        evidence_type="fhir_patient",
        source_system="EPIC FHIR",
        document_name=f"Patient {patient_id}",
        content_excerpt=f"Patient ID: {patient_id}, Active: {patient.get('active', 'Unknown')}",
        confidence=1.0,
    ))
    
    # Patient names (can have multiple - official, usual, nickname, etc.)
    names = patient.get("name", [])
    for i, name in enumerate(names):
        name_text = name.get("text", "")
        if not name_text:
            given = " ".join(name.get("given", []))
            family = name.get("family", "")
            name_text = f"{given} {family}".strip()
        if name_text:
            use = name.get("use", "official")
            atoms.append(EvidenceAtom(
                evidence_id=f"EV-{uuid4().hex[:8]}",
                evidence_type=f"patient_name_{use}",
                source_system="EPIC FHIR",
                document_name="Patient Demographics",
                content_excerpt=f"Patient Name ({use}): {name_text}",
                confidence=1.0,
            ))
    
    # Birth date
    birth_date = patient.get("birthDate")
    if birth_date:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid4().hex[:8]}",
            evidence_type="patient_dob",
            source_system="EPIC FHIR",
            document_name="Patient Demographics",
            content_excerpt=f"Date of Birth: {birth_date}",
            confidence=1.0,
        ))
    
    # Gender
    gender = patient.get("gender")
    if gender:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid4().hex[:8]}",
            evidence_type="patient_gender",
            source_system="EPIC FHIR",
            document_name="Patient Demographics",
            content_excerpt=f"Administrative Gender: {gender}",
            confidence=1.0,
        ))
    
    # Deceased status
    if "deceasedBoolean" in patient:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid4().hex[:8]}",
            evidence_type="patient_deceased_status",
            source_system="EPIC FHIR",
            document_name="Patient Demographics",
            content_excerpt=f"Deceased: {'Yes' if patient['deceasedBoolean'] else 'No'}",
            confidence=1.0,
        ))
    
    # Identifiers (MRN, SSN, etc.)
    identifiers = patient.get("identifier", [])
    for ident in identifiers:
        id_type = ident.get("type", {}).get("text", ident.get("system", "Unknown"))
        id_value = ident.get("value", "")
        if id_value:
            atoms.append(EvidenceAtom(
                evidence_id=f"EV-{uuid4().hex[:8]}",
                evidence_type=f"patient_identifier_{id_type.lower().replace(' ', '_')}",
                source_system="EPIC FHIR",
                document_name="Patient Identifiers",
                content_excerpt=f"Identifier ({id_type}): {id_value}",
                confidence=1.0,
            ))
    
    # Telecom (phone, email, fax)
    telecoms = patient.get("telecom", [])
    for telecom in telecoms:
        system = telecom.get("system", "unknown")
        value = telecom.get("value", "")
        use = telecom.get("use", "")
        if value:
            atoms.append(EvidenceAtom(
                evidence_id=f"EV-{uuid4().hex[:8]}",
                evidence_type=f"patient_contact_{system}",
                source_system="EPIC FHIR",
                document_name="Patient Contact Information",
                content_excerpt=f"{system.title()} ({use}): {value}",
                confidence=1.0,
            ))
    
    # Addresses
    addresses = patient.get("address", [])
    for i, addr in enumerate(addresses):
        addr_text = addr.get("text", "")
        if not addr_text:
            lines = addr.get("line", [])
            city = addr.get("city", "")
            state = addr.get("state", "")
            postal = addr.get("postalCode", "")
            country = addr.get("country", "")
            addr_text = ", ".join(filter(None, [", ".join(lines), city, state, postal, country]))
        if addr_text:
            use = addr.get("use", "home")
            atoms.append(EvidenceAtom(
                evidence_id=f"EV-{uuid4().hex[:8]}",
                evidence_type=f"patient_address_{use}",
                source_system="EPIC FHIR",
                document_name="Patient Address",
                content_excerpt=f"Address ({use}): {addr_text}",
                confidence=1.0,
            ))
    
    # Communication/Language preferences
    communications = patient.get("communication", [])
    for comm in communications:
        lang = comm.get("language", {})
        lang_text = lang.get("text", "")
        if not lang_text:
            coding = lang.get("coding", [{}])[0]
            lang_text = coding.get("display", coding.get("code", "Unknown"))
        preferred = comm.get("preferred", False)
        if lang_text:
            atoms.append(EvidenceAtom(
                evidence_id=f"EV-{uuid4().hex[:8]}",
                evidence_type="patient_language",
                source_system="EPIC FHIR",
                document_name="Patient Communication",
                content_excerpt=f"Language: {lang_text}{' (Preferred)' if preferred else ''}",
                confidence=1.0,
            ))
    
    # General Practitioner
    practitioners = patient.get("generalPractitioner", [])
    for pract in practitioners:
        display = pract.get("display", "")
        reference = pract.get("reference", "")
        if display:
            atoms.append(EvidenceAtom(
                evidence_id=f"EV-{uuid4().hex[:8]}",
                evidence_type="patient_practitioner",
                source_system="EPIC FHIR",
                document_name="Patient Care Team",
                content_excerpt=f"General Practitioner: {display}",
                confidence=1.0,
            ))
    
    # Managing Organization
    managing_org = patient.get("managingOrganization", {})
    if managing_org.get("display"):
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid4().hex[:8]}",
            evidence_type="patient_organization",
            source_system="EPIC FHIR",
            document_name="Patient Organization",
            content_excerpt=f"Managing Organization: {managing_org['display']}",
            confidence=1.0,
        ))
    
    # Extensions (race, ethnicity, legal sex, birth sex, etc.)
    extensions = patient.get("extension", [])
    for ext in extensions:
        url = ext.get("url", "")
        
        # Race
        if "race" in url.lower():
            race_exts = ext.get("extension", [])
            for r in race_exts:
                if r.get("url") == "text":
                    atoms.append(EvidenceAtom(
                        evidence_id=f"EV-{uuid4().hex[:8]}",
                        evidence_type="patient_race",
                        source_system="EPIC FHIR",
                        document_name="Patient Demographics",
                        content_excerpt=f"Race: {r.get('valueString', 'Unknown')}",
                        confidence=1.0,
                    ))
                elif r.get("url") == "ombCategory":
                    coding = r.get("valueCoding", {})
                    if coding.get("display"):
                        atoms.append(EvidenceAtom(
                            evidence_id=f"EV-{uuid4().hex[:8]}",
                            evidence_type="patient_race_omb",
                            source_system="EPIC FHIR",
                            document_name="Patient Demographics",
                            content_excerpt=f"Race (OMB): {coding['display']}",
                            confidence=1.0,
                        ))
        
        # Ethnicity
        elif "ethnicity" in url.lower():
            eth_exts = ext.get("extension", [])
            for e in eth_exts:
                if e.get("url") == "text":
                    atoms.append(EvidenceAtom(
                        evidence_id=f"EV-{uuid4().hex[:8]}",
                        evidence_type="patient_ethnicity",
                        source_system="EPIC FHIR",
                        document_name="Patient Demographics",
                        content_excerpt=f"Ethnicity: {e.get('valueString', 'Unknown')}",
                        confidence=1.0,
                    ))
        
        # Legal Sex
        elif "legal-sex" in url.lower():
            value_cc = ext.get("valueCodeableConcept", {})
            text = value_cc.get("text", "")
            if not text:
                coding = value_cc.get("coding", [{}])[0]
                text = coding.get("display", coding.get("code", ""))
            if text:
                atoms.append(EvidenceAtom(
                    evidence_id=f"EV-{uuid4().hex[:8]}",
                    evidence_type="patient_legal_sex",
                    source_system="EPIC FHIR",
                    document_name="Patient Demographics",
                    content_excerpt=f"Legal Sex: {text}",
                    confidence=1.0,
                ))
        
        # Birth Sex (US Core)
        elif "us-core-sex" in url.lower() or "birthsex" in url.lower():
            value = ext.get("valueCode", ext.get("valueString", ""))
            if value:
                atoms.append(EvidenceAtom(
                    evidence_id=f"EV-{uuid4().hex[:8]}",
                    evidence_type="patient_birth_sex",
                    source_system="EPIC FHIR",
                    document_name="Patient Demographics",
                    content_excerpt=f"Birth Sex: {value}",
                    confidence=1.0,
                ))
    
    print(f"Extracted {len(atoms)} evidence atoms from Patient resource")
    return atoms


def convert_condition_to_atoms(condition: Dict[str, Any]) -> List[EvidenceAtom]:
    """Convert FHIR Condition resource to EvidenceAtoms"""
    atoms = []
    condition_id = condition.get('id', str(uuid4())[:8])
    
    # Get the condition code and display
    code_info = condition.get('code', {})
    codings = code_info.get('coding', [])
    
    for coding in codings:
        code = coding.get('code', '')
        display = coding.get('display', '')
        system = coding.get('system', '')
        
        if code or display:
            extracted_value = f"{code} - {display}" if code and display else (code or display)
            atoms.append(EvidenceAtom(
                evidence_id=f"EV-{uuid4().hex[:8]}",
                evidence_type="diagnosis",  # Changed from "condition_diagnosis" to "diagnosis"
                source_system="EPIC FHIR",
                document_name=f"Condition {condition_id}",
                content_excerpt=f"Diagnosis: {display} (Code: {code}, System: {system})",
                extracted_value=extracted_value,
                confidence=1.0,
            ))
    
    # Clinical status
    clinical_status = condition.get('clinicalStatus', {}).get('coding', [{}])[0].get('code', '')
    if clinical_status:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid4().hex[:8]}",
            evidence_type="condition_status",
            source_system="EPIC FHIR",
            document_name=f"Condition {condition_id}",
            content_excerpt=f"Clinical Status: {clinical_status}",
            confidence=1.0,
        ))
    
    # Verification status
    verification = condition.get('verificationStatus', {}).get('coding', [{}])[0].get('code', '')
    if verification:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid4().hex[:8]}",
            evidence_type="condition_verification",
            source_system="EPIC FHIR",
            document_name=f"Condition {condition_id}",
            content_excerpt=f"Verification Status: {verification}",
            confidence=1.0,
        ))
    
    # Onset date
    onset = condition.get('onsetDateTime', condition.get('recordedDate', ''))
    if onset:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid4().hex[:8]}",
            evidence_type="condition_onset",
            source_system="EPIC FHIR",
            document_name=f"Condition {condition_id}",
            content_excerpt=f"Onset Date: {onset}",
            confidence=1.0,
        ))
    
    # Category
    categories = condition.get('category', [])
    for cat in categories:
        cat_display = cat.get('coding', [{}])[0].get('display', cat.get('text', ''))
        if cat_display:
            atoms.append(EvidenceAtom(
                evidence_id=f"EV-{uuid4().hex[:8]}",
                evidence_type="condition_category",
                source_system="EPIC FHIR",
                document_name=f"Condition {condition_id}",
                content_excerpt=f"Category: {cat_display}",
                confidence=1.0,
            ))
    
    return atoms


def convert_procedure_to_atoms(procedure: Dict[str, Any]) -> List[EvidenceAtom]:
    """Convert FHIR Procedure resource to EvidenceAtoms"""
    atoms = []
    procedure_id = procedure.get('id', str(uuid4())[:8])
    
    # Get the procedure code
    code_info = procedure.get('code', {})
    codings = code_info.get('coding', [])
    
    for coding in codings:
        code = coding.get('code', '')
        display = coding.get('display', '')
        system = coding.get('system', '')
        
        if code or display:
            # Format: "CPT_CODE - Description" for easy parsing
            extracted_value = f"{code} - {display}" if code and display else (code or display)
            atoms.append(EvidenceAtom(
                evidence_id=f"EV-{uuid4().hex[:8]}",
                evidence_type="procedure",  # Changed from "procedure_code" to "procedure"
                source_system="EPIC FHIR",
                document_name=f"Procedure {procedure_id}",
                content_excerpt=f"Procedure: {display} (Code: {code}, System: {system})",
                extracted_value=extracted_value,  # Add extracted_value for claim generator
                confidence=1.0,
            ))
    
    # Status
    status = procedure.get('status', '')
    if status:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid4().hex[:8]}",
            evidence_type="procedure_status",
            source_system="EPIC FHIR",
            document_name=f"Procedure {procedure_id}",
            content_excerpt=f"Procedure Status: {status}",
            confidence=1.0,
        ))
    
    # Performed date
    performed = procedure.get('performedDateTime', procedure.get('performedPeriod', {}).get('start', ''))
    if performed:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid4().hex[:8]}",
            evidence_type="procedure_date",
            source_system="EPIC FHIR",
            document_name=f"Procedure {procedure_id}",
            content_excerpt=f"Performed On: {performed}",
            confidence=1.0,
        ))
    
    return atoms


def convert_medication_to_atoms(medication: Dict[str, Any]) -> List[EvidenceAtom]:
    """Convert FHIR MedicationRequest resource to EvidenceAtoms"""
    atoms = []
    med_id = medication.get('id', str(uuid4())[:8])
    
    # Get medication info
    med_info = medication.get('medicationCodeableConcept', {})
    codings = med_info.get('coding', [])
    
    for coding in codings:
        code = coding.get('code', '')
        display = coding.get('display', '')
        
        if code or display:
            atoms.append(EvidenceAtom(
                evidence_id=f"EV-{uuid4().hex[:8]}",
                evidence_type="medication_code",
                source_system="EPIC FHIR",
                document_name=f"Medication {med_id}",
                content_excerpt=f"Medication: {display} (Code: {code})",
                confidence=1.0,
            ))
    
    # Status
    status = medication.get('status', '')
    if status:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid4().hex[:8]}",
            evidence_type="medication_status",
            source_system="EPIC FHIR",
            document_name=f"Medication {med_id}",
            content_excerpt=f"Medication Status: {status}",
            confidence=1.0,
        ))
    
    # Dosage instructions
    dosage = medication.get('dosageInstruction', [{}])[0].get('text', '')
    if dosage:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid4().hex[:8]}",
            evidence_type="medication_dosage",
            source_system="EPIC FHIR",
            document_name=f"Medication {med_id}",
            content_excerpt=f"Dosage: {dosage}",
            confidence=1.0,
        ))
    
    return atoms


def convert_observation_to_atoms(observation: Dict[str, Any]) -> List[EvidenceAtom]:
    """Convert FHIR Observation resource to EvidenceAtoms"""
    atoms = []
    obs_id = observation.get('id', str(uuid4())[:8])
    
    # Get observation code
    code_info = observation.get('code', {})
    display = code_info.get('text', '')
    if not display:
        codings = code_info.get('coding', [])
        if codings:
            display = codings[0].get('display', codings[0].get('code', ''))
    
    # Get value
    value = ''
    if 'valueQuantity' in observation:
        vq = observation['valueQuantity']
        value = f"{vq.get('value', '')} {vq.get('unit', '')}"
    elif 'valueString' in observation:
        value = observation['valueString']
    elif 'valueCodeableConcept' in observation:
        value = observation['valueCodeableConcept'].get('text', '')
    
    if display or value:
        # Determine type (vital, lab, etc.)
        category = observation.get('category', [{}])[0].get('coding', [{}])[0].get('code', 'observation')
        obs_type = f"observation_{category}"
        
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid4().hex[:8]}",
            evidence_type=obs_type,
            source_system="EPIC FHIR",
            document_name=f"Observation {obs_id}",
            content_excerpt=f"{display}: {value}".strip(': '),
            confidence=1.0,
        ))
    
    # Effective date
    effective = observation.get('effectiveDateTime', '')
    if effective and display:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid4().hex[:8]}",
            evidence_type="observation_date",
            source_system="EPIC FHIR",
            document_name=f"Observation {obs_id}",
            content_excerpt=f"{display} recorded on: {effective}",
            confidence=1.0,
        ))
    
    return atoms


def convert_encounter_to_atoms(encounter: Dict[str, Any]) -> List[EvidenceAtom]:
    """Convert FHIR Encounter resource to EvidenceAtoms"""
    atoms = []
    enc_id = encounter.get('id', str(uuid4())[:8])
    
    # Encounter class (inpatient, outpatient, etc.)
    enc_class = encounter.get('class', {})
    class_display = enc_class.get('display', enc_class.get('code', ''))
    if class_display:
        # Main encounter atom for claim generation
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid4().hex[:8]}",
            evidence_type="encounter",  # Changed from "encounter_class" to "encounter"
            source_system="EPIC FHIR",
            document_name=f"Encounter {enc_id}",
            content_excerpt=f"Encounter Type: {class_display}",
            extracted_value=class_display,  # Add extracted_value for claim generator
            confidence=1.0,
        ))
        # Also keep the detailed encounter_class atom for reference
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid4().hex[:8]}",
            evidence_type="encounter_class",
            source_system="EPIC FHIR",
            document_name=f"Encounter {enc_id}",
            content_excerpt=f"Encounter Type: {class_display}",
            confidence=1.0,
        ))
    
    # Status
    status = encounter.get('status', '')
    if status:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid4().hex[:8]}",
            evidence_type="encounter_status",
            source_system="EPIC FHIR",
            document_name=f"Encounter {enc_id}",
            content_excerpt=f"Encounter Status: {status}",
            confidence=1.0,
        ))
    
    # Period
    period = encounter.get('period', {})
    start = period.get('start', '')
    end = period.get('end', '')
    if start:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid4().hex[:8]}",
            evidence_type="encounter_period",
            source_system="EPIC FHIR",
            document_name=f"Encounter {enc_id}",
            content_excerpt=f"Encounter Period: {start} to {end or 'ongoing'}",
            confidence=1.0,
        ))
    
    # Type/reason
    types = encounter.get('type', [])
    for t in types:
        t_display = t.get('text', t.get('coding', [{}])[0].get('display', ''))
        if t_display:
            atoms.append(EvidenceAtom(
                evidence_id=f"EV-{uuid4().hex[:8]}",
                evidence_type="encounter_type",
                source_system="EPIC FHIR",
                document_name=f"Encounter {enc_id}",
                content_excerpt=f"Encounter Reason: {t_display}",
                confidence=1.0,
            ))
    
    return atoms


def convert_allergy_to_atoms(allergy: Dict[str, Any]) -> List[EvidenceAtom]:
    """Convert FHIR AllergyIntolerance resource to EvidenceAtoms"""
    atoms = []
    allergy_id = allergy.get('id', str(uuid4())[:8])
    
    # Get the allergen
    code_info = allergy.get('code', {})
    display = code_info.get('text', '')
    if not display:
        codings = code_info.get('coding', [])
        if codings:
            display = codings[0].get('display', '')
    
    if display:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid4().hex[:8]}",
            evidence_type="allergy",
            source_system="EPIC FHIR",
            document_name=f"Allergy {allergy_id}",
            content_excerpt=f"Allergy: {display}",
            confidence=1.0,
        ))
    
    # Reaction
    reactions = allergy.get('reaction', [])
    for reaction in reactions:
        manifestations = reaction.get('manifestation', [])
        for m in manifestations:
            m_display = m.get('coding', [{}])[0].get('display', m.get('text', ''))
            if m_display:
                atoms.append(EvidenceAtom(
                    evidence_id=f"EV-{uuid4().hex[:8]}",
                    evidence_type="allergy_reaction",
                    source_system="EPIC FHIR",
                    document_name=f"Allergy {allergy_id}",
                    content_excerpt=f"Reaction to {display}: {m_display}",
                    confidence=1.0,
                ))
    
    return atoms


def convert_immunization_to_atoms(immunization: Dict[str, Any]) -> List[EvidenceAtom]:
    """Convert FHIR Immunization resource to EvidenceAtoms"""
    atoms = []
    imm_id = immunization.get('id', str(uuid4())[:8])
    
    # Get vaccine
    vaccine_info = immunization.get('vaccineCode', {})
    display = vaccine_info.get('text', '')
    if not display:
        codings = vaccine_info.get('coding', [])
        if codings:
            display = codings[0].get('display', '')
    
    if display:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid4().hex[:8]}",
            evidence_type="immunization",
            source_system="EPIC FHIR",
            document_name=f"Immunization {imm_id}",
            content_excerpt=f"Vaccine: {display}",
            confidence=1.0,
        ))
    
    # Date
    occurrence = immunization.get('occurrenceDateTime', '')
    if occurrence and display:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid4().hex[:8]}",
            evidence_type="immunization_date",
            source_system="EPIC FHIR",
            document_name=f"Immunization {imm_id}",
            content_excerpt=f"{display} administered on: {occurrence}",
            confidence=1.0,
        ))
    
    return atoms


def convert_all_fhir_to_atoms(fhir_data: Dict[str, Any]) -> List[EvidenceAtom]:
    """Convert all FHIR resources from /fhir/all endpoint to EvidenceAtoms"""
    atoms = []
    
    # Patient
    if fhir_data.get('patient'):
        atoms.extend(convert_patient_to_atoms(fhir_data['patient']))
    
    # Conditions
    conditions = fhir_data.get('conditions', {})
    if conditions and conditions.get('entry'):
        for entry in conditions['entry']:
            resource = entry.get('resource', {})
            if resource.get('resourceType') == 'Condition':
                atoms.extend(convert_condition_to_atoms(resource))
    
    # Procedures
    procedures = fhir_data.get('procedures', {})
    if procedures and procedures.get('entry'):
        for entry in procedures['entry']:
            resource = entry.get('resource', {})
            if resource.get('resourceType') == 'Procedure':
                atoms.extend(convert_procedure_to_atoms(resource))
    
    # Medications
    medications = fhir_data.get('medications', {})
    if medications and medications.get('entry'):
        for entry in medications['entry']:
            resource = entry.get('resource', {})
            if resource.get('resourceType') == 'MedicationRequest':
                atoms.extend(convert_medication_to_atoms(resource))
    
    # Observations
    observations = fhir_data.get('observations', {})
    if observations and observations.get('entry'):
        for entry in observations['entry']:
            resource = entry.get('resource', {})
            if resource.get('resourceType') == 'Observation':
                atoms.extend(convert_observation_to_atoms(resource))
    
    # Encounters
    encounters = fhir_data.get('encounters', {})
    if encounters and encounters.get('entry'):
        for entry in encounters['entry']:
            resource = entry.get('resource', {})
            if resource.get('resourceType') == 'Encounter':
                atoms.extend(convert_encounter_to_atoms(resource))
    
    # Allergies
    allergies = fhir_data.get('allergies', {})
    if allergies and allergies.get('entry'):
        for entry in allergies['entry']:
            resource = entry.get('resource', {})
            if resource.get('resourceType') == 'AllergyIntolerance':
                atoms.extend(convert_allergy_to_atoms(resource))
    
    # Immunizations
    immunizations = fhir_data.get('immunizations', {})
    if immunizations and immunizations.get('entry'):
        for entry in immunizations['entry']:
            resource = entry.get('resource', {})
            if resource.get('resourceType') == 'Immunization':
                atoms.extend(convert_immunization_to_atoms(resource))
    
    print(f"Extracted {len(atoms)} total evidence atoms from all FHIR resources")
    return atoms

# CPT Fee Schedule - Realistic Medicare/Commercial rates
CPT_FEE_SCHEDULE = {
    # E&M Codes (Office Visits)
    "99211": {"description": "Office visit, established, minimal", "charge": 45.00},
    "99212": {"description": "Office visit, established, straightforward", "charge": 95.00},
    "99213": {"description": "Office visit, established, low complexity", "charge": 150.00},
    "99214": {"description": "Office visit, established, moderate complexity", "charge": 220.00},
    "99215": {"description": "Office visit, established, high complexity", "charge": 320.00},
    "99395": {"description": "Preventive medicine, 18-39 years", "charge": 250.00},
    
    # Lab/Diagnostic
    "36415": {"description": "Venipuncture (blood draw)", "charge": 35.00},
    "80053": {"description": "Comprehensive metabolic panel", "charge": 95.00},
    "83036": {"description": "Hemoglobin A1c", "charge": 85.00},
    "85025": {"description": "Complete blood count (CBC)", "charge": 65.00},
    "80061": {"description": "Lipid panel", "charge": 120.00},
    
    # Cardiac Procedures
    "93000": {"description": "Electrocardiogram (ECG/EKG), complete", "charge": 175.00},
    "93306": {"description": "Echocardiography, transthoracic, complete", "charge": 850.00},
    "93350": {"description": "Stress echocardiography", "charge": 1200.00},
    "33533": {"description": "Coronary artery bypass, single arterial graft (CABG)", "charge": 45000.00},
    "92928": {"description": "Percutaneous coronary intervention (stent)", "charge": 18500.00},
    "33249": {"description": "Implantable defibrillator (ICD) insertion", "charge": 32000.00},
    
    # Orthopedic Procedures  
    "27447": {"description": "Total knee arthroplasty (replacement)", "charge": 28500.00},
    "27130": {"description": "Total hip arthroplasty (replacement)", "charge": 32000.00},
    "29881": {"description": "Knee arthroscopy with meniscectomy", "charge": 4500.00},
    "22551": {"description": "Cervical spine fusion, anterior approach", "charge": 35000.00},
    "22612": {"description": "Lumbar spine fusion, posterior approach", "charge": 42000.00},
    "73560": {"description": "X-ray knee, 1-2 views", "charge": 125.00},
    "73630": {"description": "X-ray foot, complete", "charge": 110.00},
    "72148": {"description": "MRI lumbar spine without contrast", "charge": 1850.00},
    
    # Physical Therapy
    "97110": {"description": "Therapeutic exercises, 15 min", "charge": 85.00},
    "97140": {"description": "Manual therapy techniques, 15 min", "charge": 95.00},
    "97530": {"description": "Therapeutic activities, 15 min", "charge": 90.00},
    
    # General Surgery
    "47562": {"description": "Laparoscopic cholecystectomy", "charge": 8500.00},
    "44970": {"description": "Laparoscopic appendectomy", "charge": 7200.00},
    "49505": {"description": "Inguinal hernia repair", "charge": 5800.00},
    
    # Imaging
    "71046": {"description": "Chest X-ray, 2 views", "charge": 145.00},
    "74177": {"description": "CT abdomen and pelvis with contrast", "charge": 1650.00},
    "70553": {"description": "MRI brain with and without contrast", "charge": 2400.00},
    
    # Injections/Infusions
    "20610": {"description": "Arthrocentesis, major joint injection", "charge": 285.00},
    "96365": {"description": "IV infusion therapy, first hour", "charge": 320.00},
    "90834": {"description": "Psychotherapy, 45 minutes", "charge": 180.00},
    
    # Default for unknown codes
    "DEFAULT": {"description": "Medical procedure", "charge": 200.00},
}

def get_cpt_charge(code: str) -> tuple:
    """Get charge and description for a CPT code"""
    if code in CPT_FEE_SCHEDULE:
        entry = CPT_FEE_SCHEDULE[code]
        return entry["charge"], entry["description"]
    return CPT_FEE_SCHEDULE["DEFAULT"]["charge"], CPT_FEE_SCHEDULE["DEFAULT"]["description"]


def generate_claim_from_atoms(
    atoms: List[EvidenceAtom],
    patient: Dict[str, Any]
) -> ClaimResponse:
    """Generate a claim from EvidenceAtoms using rule-based logic"""
    
    # Extract patient info
    patient_id = patient.get("id", "Unknown")
    patient_name = "Unknown"
    names = patient.get("name", [])
    if names:
        patient_name = names[0].get("text", "Unknown")
    
    diagnoses = []
    review_reasons = []
    lines = []
    line_number = 1
    
    # Extract diagnoses from condition atoms
    condition_atoms = [a for a in atoms if a.evidence_type == "diagnosis"]
    for atom in condition_atoms:
        # Parse the code from the atom value (e.g., "E11.9 - Type 2 diabetes...")
        if atom.extracted_value:
            code = atom.extracted_value.split(" - ")[0] if " - " in atom.extracted_value else atom.extracted_value.split()[0]
            description = atom.extracted_value.split(" - ")[1] if " - " in atom.extracted_value else atom.extracted_value
        else:
            # Fallback: parse from content_excerpt
            import re
            match = re.search(r'Code:\s*([A-Z0-9.]+)', atom.content_excerpt)
            code = match.group(1) if match else "Z00.00"
            match_desc = re.search(r'Diagnosis:\s*([^(]+)', atom.content_excerpt)
            description = match_desc.group(1).strip() if match_desc else "Unknown diagnosis"
        
        diagnoses.append(Diagnosis(
            sequence=len(diagnoses) + 1,
            code=code,
            description=description[:100],  # Truncate if too long
            confidence=0.95,
            supporting_evidence=[atom.evidence_id],
        ))
    
    # If no diagnoses from conditions, add default routine checkup
    if not diagnoses:
        dob_atoms = [a for a in atoms if a.evidence_type == "patient_dob"]
        diagnoses.append(Diagnosis(
            sequence=1,
            code="Z00.00",
            description="Encounter for general adult medical examination without abnormal findings",
            confidence=0.95,
            supporting_evidence=[a.evidence_id for a in dob_atoms] if dob_atoms else [],
        ))
        if not dob_atoms:
            review_reasons.append("Missing date of birth - cannot verify patient age")
    
    # Extract procedures from procedure atoms and create claim lines with REAL charges
    procedure_atoms = [a for a in atoms if a.evidence_type == "procedure"]
    for atom in procedure_atoms:
        # Parse CPT code from the atom value
        if atom.extracted_value:
            code = atom.extracted_value.split(" - ")[0] if " - " in atom.extracted_value else atom.extracted_value.split()[0]
        else:
            # Fallback: try to extract from content_excerpt
            content = atom.content_excerpt
            # Look for pattern like "Code: 33533" or "33533 - Description"
            import re
            match = re.search(r'Code:\s*(\d+)', content) or re.search(r'(\d{5})', content)
            code = match.group(1) if match else "99213"
        charge, description = get_cpt_charge(code)
        
        lines.append(ClaimLine(
            line_number=line_number,
            code=code,
            code_type="CPT",
            description=description,
            charge_amount=charge,
            confidence=0.94,
            supporting_evidence=[atom.evidence_id],
            rationale=f"Procedure documented in patient record: {(atom.extracted_value or atom.content_excerpt)[:80]}",
        ))
        line_number += 1
    
    # Add encounter-based E&M code if we have encounter atoms
    encounter_atoms = [a for a in atoms if a.evidence_type == "encounter"]
    if encounter_atoms:
        # Check encounter type to determine complexity
        encounter_value = (encounter_atoms[0].extracted_value or encounter_atoms[0].content_excerpt).lower()
        if "inpatient" in encounter_value or "hospital" in encounter_value:
            code, charge, desc = "99215", 320.00, "Office visit, established, high complexity"
        elif "emergency" in encounter_value:
            code, charge, desc = "99214", 220.00, "Office visit, established, moderate complexity"
        else:
            code, charge, desc = "99213", 150.00, "Office visit, established, low complexity"
        
        lines.append(ClaimLine(
            line_number=line_number,
            code=code,
            code_type="CPT",
            description=desc,
            charge_amount=charge,
            confidence=0.92,
            supporting_evidence=[encounter_atoms[0].evidence_id],
            rationale=f"E&M code based on encounter: {(encounter_atoms[0].extracted_value or encounter_atoms[0].content_excerpt)[:60]}",
        ))
        line_number += 1
    elif not procedure_atoms:
        # Fallback: add basic office visit if no procedures
        lines.append(ClaimLine(
            line_number=line_number,
            code="99213",
            code_type="CPT",
            description="Office or other outpatient visit, established patient, low complexity",
            charge_amount=150.00,
            confidence=0.88,
            supporting_evidence=[atoms[0].evidence_id] if atoms else [],
            rationale="Standard office visit - no specific procedures documented",
        ))
        line_number += 1
    
    # Add lab charges if we have observation/lab atoms
    lab_atoms = [a for a in atoms if a.evidence_type == "lab_result"]
    lab_codes_added = set()
    for atom in lab_atoms:
        # Map common labs to CPT codes
        lab_value = (atom.extracted_value or atom.content_excerpt).lower()
        if "a1c" in lab_value or "hemoglobin a1c" in lab_value:
            code = "83036"
        elif "glucose" in lab_value:
            code = "80053"  # Part of metabolic panel
        elif "cholesterol" in lab_value or "lipid" in lab_value:
            code = "80061"
        elif "cbc" in lab_value or "blood count" in lab_value:
            code = "85025"
        else:
            continue  # Skip unknown labs
        
        if code not in lab_codes_added:
            lab_codes_added.add(code)
            charge, description = get_cpt_charge(code)
            lines.append(ClaimLine(
                line_number=line_number,
                code=code,
                code_type="CPT",
                description=description,
                charge_amount=charge,
                confidence=0.90,
                supporting_evidence=[atom.evidence_id],
                rationale=f"Lab test performed: {(atom.extracted_value or atom.content_excerpt)[:60]}",
            ))
            line_number += 1
    
    total_charges = sum(line.charge_amount for line in lines)
    requires_review = len(review_reasons) > 0 or any(l.confidence < 0.9 for l in lines)
    
    if any(l.confidence < 0.9 for l in lines):
        review_reasons.append("One or more claim lines have confidence below 90%")
    
    return ClaimResponse(
        id=f"CLM-{uuid4().hex[:8].upper()}",
        status="DRAFT" if requires_review else "VALIDATED",
        patient_id=patient_id,
        patient_name=patient_name,
        total_charges=total_charges,
        diagnoses=diagnoses,
        lines=lines,
        evidence_atoms=atoms,
        created_at=datetime.now().isoformat(),
        requires_review=requires_review,
        review_reasons=review_reasons,
    )

# ============ API Endpoints ============

@app.get("/")
async def root():
    return {
        "service": "Insurabridge Demo API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "generate_claim": "POST /generate-claim",
            "pipeline": "POST /pipeline/run",
            "patient": "GET /fhir/patient?bridge_url=...",
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# ============ Demo/Synthetic Patient Data ============

DEMO_PATIENTS = {
    "demo-diabetes": {
        "patient": {
            "resourceType": "Patient",
            "id": "demo-diabetes-001",
            "name": [{"text": "Maria Santos", "family": "Santos", "given": ["Maria"]}],
            "birthDate": "1965-03-15",
            "gender": "female",
            "address": [{"text": "456 Oak Street, Chicago, IL 60601"}],
        },
        "conditions": {
            "entry": [
                {"resource": {"resourceType": "Condition", "id": "cond-1", "code": {"coding": [{"code": "E11.9", "display": "Type 2 diabetes mellitus without complications", "system": "http://hl7.org/fhir/sid/icd-10-cm"}]}, "clinicalStatus": {"coding": [{"code": "active"}]}, "onsetDateTime": "2018-06-01"}},
                {"resource": {"resourceType": "Condition", "id": "cond-2", "code": {"coding": [{"code": "I10", "display": "Essential (primary) hypertension", "system": "http://hl7.org/fhir/sid/icd-10-cm"}]}, "clinicalStatus": {"coding": [{"code": "active"}]}, "onsetDateTime": "2019-02-15"}},
                {"resource": {"resourceType": "Condition", "id": "cond-3", "code": {"coding": [{"code": "E78.5", "display": "Hyperlipidemia, unspecified", "system": "http://hl7.org/fhir/sid/icd-10-cm"}]}, "clinicalStatus": {"coding": [{"code": "active"}]}, "onsetDateTime": "2019-02-15"}},
                {"resource": {"resourceType": "Condition", "id": "cond-4", "code": {"coding": [{"code": "E66.01", "display": "Morbid obesity due to excess calories", "system": "http://hl7.org/fhir/sid/icd-10-cm"}]}, "clinicalStatus": {"coding": [{"code": "active"}]}, "onsetDateTime": "2017-01-01"}},
            ]
        },
        "procedures": {
            "entry": [
                {"resource": {"resourceType": "Procedure", "id": "proc-1", "code": {"coding": [{"code": "36415", "display": "Venipuncture", "system": "http://www.ama-assn.org/go/cpt"}]}, "status": "completed", "performedDateTime": "2024-01-15"}},
                {"resource": {"resourceType": "Procedure", "id": "proc-2", "code": {"coding": [{"code": "99214", "display": "Office visit, established patient, moderate complexity", "system": "http://www.ama-assn.org/go/cpt"}]}, "status": "completed", "performedDateTime": "2024-01-15"}},
            ]
        },
        "medications": {
            "entry": [
                {"resource": {"resourceType": "MedicationRequest", "id": "med-1", "medicationCodeableConcept": {"coding": [{"code": "860975", "display": "Metformin 500 MG Oral Tablet"}]}, "status": "active", "dosageInstruction": [{"text": "Take 500mg twice daily with meals"}]}},
                {"resource": {"resourceType": "MedicationRequest", "id": "med-2", "medicationCodeableConcept": {"coding": [{"code": "197361", "display": "Lisinopril 10 MG Oral Tablet"}]}, "status": "active", "dosageInstruction": [{"text": "Take 10mg once daily"}]}},
                {"resource": {"resourceType": "MedicationRequest", "id": "med-3", "medicationCodeableConcept": {"coding": [{"code": "617312", "display": "Atorvastatin 20 MG Oral Tablet"}]}, "status": "active", "dosageInstruction": [{"text": "Take 20mg once daily at bedtime"}]}},
            ]
        },
        "observations": {
            "entry": [
                {"resource": {"resourceType": "Observation", "id": "obs-1", "code": {"coding": [{"code": "4548-4", "display": "Hemoglobin A1c"}]}, "valueQuantity": {"value": 7.2, "unit": "%"}, "effectiveDateTime": "2024-01-15", "category": [{"coding": [{"code": "laboratory"}]}]}},
                {"resource": {"resourceType": "Observation", "id": "obs-2", "code": {"coding": [{"code": "2339-0", "display": "Glucose"}]}, "valueQuantity": {"value": 142, "unit": "mg/dL"}, "effectiveDateTime": "2024-01-15", "category": [{"coding": [{"code": "laboratory"}]}]}},
                {"resource": {"resourceType": "Observation", "id": "obs-3", "code": {"coding": [{"code": "8480-6", "display": "Systolic blood pressure"}]}, "valueQuantity": {"value": 138, "unit": "mmHg"}, "effectiveDateTime": "2024-01-15", "category": [{"coding": [{"code": "vital-signs"}]}]}},
                {"resource": {"resourceType": "Observation", "id": "obs-4", "code": {"coding": [{"code": "8462-4", "display": "Diastolic blood pressure"}]}, "valueQuantity": {"value": 88, "unit": "mmHg"}, "effectiveDateTime": "2024-01-15", "category": [{"coding": [{"code": "vital-signs"}]}]}},
                {"resource": {"resourceType": "Observation", "id": "obs-5", "code": {"coding": [{"code": "29463-7", "display": "Body weight"}]}, "valueQuantity": {"value": 210, "unit": "lbs"}, "effectiveDateTime": "2024-01-15", "category": [{"coding": [{"code": "vital-signs"}]}]}},
                {"resource": {"resourceType": "Observation", "id": "obs-6", "code": {"coding": [{"code": "2093-3", "display": "Total Cholesterol"}]}, "valueQuantity": {"value": 245, "unit": "mg/dL"}, "effectiveDateTime": "2024-01-15", "category": [{"coding": [{"code": "laboratory"}]}]}},
            ]
        },
        "encounters": {
            "entry": [
                {"resource": {"resourceType": "Encounter", "id": "enc-1", "class": {"code": "AMB", "display": "Ambulatory"}, "status": "finished", "period": {"start": "2024-01-15", "end": "2024-01-15"}, "type": [{"text": "Diabetes follow-up visit"}]}},
            ]
        },
        "allergies": {
            "entry": [
                {"resource": {"resourceType": "AllergyIntolerance", "id": "allergy-1", "code": {"coding": [{"display": "Penicillin"}]}, "reaction": [{"manifestation": [{"coding": [{"display": "Hives"}]}]}]}},
            ]
        },
        "immunizations": {"entry": []},
        "diagnosticReports": {"entry": []},
        "coverages": {"entry": []},
    },
    "demo-cardiac": {
        "patient": {
            "resourceType": "Patient",
            "id": "demo-cardiac-001",
            "name": [{"text": "Robert Johnson", "family": "Johnson", "given": ["Robert"]}],
            "birthDate": "1958-11-22",
            "gender": "male",
            "address": [{"text": "789 Pine Avenue, Boston, MA 02101"}],
        },
        "conditions": {
            "entry": [
                {"resource": {"resourceType": "Condition", "id": "cond-1", "code": {"coding": [{"code": "I25.10", "display": "Atherosclerotic heart disease of native coronary artery without angina pectoris", "system": "http://hl7.org/fhir/sid/icd-10-cm"}]}, "clinicalStatus": {"coding": [{"code": "active"}]}, "onsetDateTime": "2020-03-15"}},
                {"resource": {"resourceType": "Condition", "id": "cond-2", "code": {"coding": [{"code": "I50.9", "display": "Heart failure, unspecified", "system": "http://hl7.org/fhir/sid/icd-10-cm"}]}, "clinicalStatus": {"coding": [{"code": "active"}]}, "onsetDateTime": "2021-06-01"}},
                {"resource": {"resourceType": "Condition", "id": "cond-3", "code": {"coding": [{"code": "I48.91", "display": "Unspecified atrial fibrillation", "system": "http://hl7.org/fhir/sid/icd-10-cm"}]}, "clinicalStatus": {"coding": [{"code": "active"}]}, "onsetDateTime": "2021-08-20"}},
                {"resource": {"resourceType": "Condition", "id": "cond-4", "code": {"coding": [{"code": "I10", "display": "Essential hypertension", "system": "http://hl7.org/fhir/sid/icd-10-cm"}]}, "clinicalStatus": {"coding": [{"code": "active"}]}, "onsetDateTime": "2015-01-01"}},
                {"resource": {"resourceType": "Condition", "id": "cond-5", "code": {"coding": [{"code": "Z95.1", "display": "Presence of aortocoronary bypass graft", "system": "http://hl7.org/fhir/sid/icd-10-cm"}]}, "clinicalStatus": {"coding": [{"code": "active"}]}, "onsetDateTime": "2020-04-10"}},
            ]
        },
        "procedures": {
            "entry": [
                {"resource": {"resourceType": "Procedure", "id": "proc-1", "code": {"coding": [{"code": "33533", "display": "Coronary artery bypass, single arterial graft (CABG)", "system": "http://www.ama-assn.org/go/cpt"}]}, "status": "completed", "performedDateTime": "2020-04-10"}},
                {"resource": {"resourceType": "Procedure", "id": "proc-2", "code": {"coding": [{"code": "93000", "display": "Electrocardiogram (ECG/EKG), complete", "system": "http://www.ama-assn.org/go/cpt"}]}, "status": "completed", "performedDateTime": "2024-01-20"}},
                {"resource": {"resourceType": "Procedure", "id": "proc-3", "code": {"coding": [{"code": "93306", "display": "Echocardiography, transthoracic, complete", "system": "http://www.ama-assn.org/go/cpt"}]}, "status": "completed", "performedDateTime": "2024-01-20"}},
                {"resource": {"resourceType": "Procedure", "id": "proc-4", "code": {"coding": [{"code": "93350", "display": "Stress echocardiography", "system": "http://www.ama-assn.org/go/cpt"}]}, "status": "completed", "performedDateTime": "2024-01-20"}},
            ]
        },
        "medications": {
            "entry": [
                {"resource": {"resourceType": "MedicationRequest", "id": "med-1", "medicationCodeableConcept": {"coding": [{"display": "Warfarin 5 MG Oral Tablet"}]}, "status": "active", "dosageInstruction": [{"text": "Take 5mg once daily"}]}},
                {"resource": {"resourceType": "MedicationRequest", "id": "med-2", "medicationCodeableConcept": {"coding": [{"display": "Metoprolol Succinate 50 MG Extended Release Tablet"}]}, "status": "active", "dosageInstruction": [{"text": "Take 50mg once daily"}]}},
                {"resource": {"resourceType": "MedicationRequest", "id": "med-3", "medicationCodeableConcept": {"coding": [{"display": "Furosemide 40 MG Oral Tablet"}]}, "status": "active", "dosageInstruction": [{"text": "Take 40mg once daily"}]}},
                {"resource": {"resourceType": "MedicationRequest", "id": "med-4", "medicationCodeableConcept": {"coding": [{"display": "Lisinopril 20 MG Oral Tablet"}]}, "status": "active", "dosageInstruction": [{"text": "Take 20mg once daily"}]}},
                {"resource": {"resourceType": "MedicationRequest", "id": "med-5", "medicationCodeableConcept": {"coding": [{"display": "Aspirin 81 MG Oral Tablet"}]}, "status": "active", "dosageInstruction": [{"text": "Take 81mg once daily"}]}},
            ]
        },
        "observations": {
            "entry": [
                {"resource": {"resourceType": "Observation", "id": "obs-1", "code": {"coding": [{"display": "Ejection Fraction"}]}, "valueQuantity": {"value": 35, "unit": "%"}, "effectiveDateTime": "2024-01-20", "category": [{"coding": [{"code": "laboratory"}]}]}},
                {"resource": {"resourceType": "Observation", "id": "obs-2", "code": {"coding": [{"display": "BNP"}]}, "valueQuantity": {"value": 450, "unit": "pg/mL"}, "effectiveDateTime": "2024-01-20", "category": [{"coding": [{"code": "laboratory"}]}]}},
                {"resource": {"resourceType": "Observation", "id": "obs-3", "code": {"coding": [{"display": "INR"}]}, "valueQuantity": {"value": 2.3, "unit": "ratio"}, "effectiveDateTime": "2024-01-20", "category": [{"coding": [{"code": "laboratory"}]}]}},
                {"resource": {"resourceType": "Observation", "id": "obs-4", "code": {"coding": [{"display": "Heart Rate"}]}, "valueQuantity": {"value": 72, "unit": "bpm"}, "effectiveDateTime": "2024-01-20", "category": [{"coding": [{"code": "vital-signs"}]}]}},
            ]
        },
        "encounters": {
            "entry": [
                {"resource": {"resourceType": "Encounter", "id": "enc-1", "class": {"code": "AMB", "display": "Ambulatory"}, "status": "finished", "period": {"start": "2024-01-20"}, "type": [{"text": "Cardiology follow-up"}]}},
            ]
        },
        "allergies": {"entry": []},
        "immunizations": {"entry": []},
        "diagnosticReports": {"entry": []},
        "coverages": {"entry": []},
    },
    "demo-orthopedic": {
        "patient": {
            "resourceType": "Patient",
            "id": "demo-ortho-001",
            "name": [{"text": "Susan Williams", "family": "Williams", "given": ["Susan"]}],
            "birthDate": "1970-07-08",
            "gender": "female",
            "address": [{"text": "321 Maple Drive, Seattle, WA 98101"}],
        },
        "conditions": {
            "entry": [
                {"resource": {"resourceType": "Condition", "id": "cond-1", "code": {"coding": [{"code": "M17.11", "display": "Primary osteoarthritis, right knee", "system": "http://hl7.org/fhir/sid/icd-10-cm"}]}, "clinicalStatus": {"coding": [{"code": "active"}]}, "onsetDateTime": "2022-01-01"}},
                {"resource": {"resourceType": "Condition", "id": "cond-2", "code": {"coding": [{"code": "M54.5", "display": "Low back pain", "system": "http://hl7.org/fhir/sid/icd-10-cm"}]}, "clinicalStatus": {"coding": [{"code": "active"}]}, "onsetDateTime": "2023-06-15"}},
                {"resource": {"resourceType": "Condition", "id": "cond-3", "code": {"coding": [{"code": "M79.3", "display": "Panniculitis, unspecified", "system": "http://hl7.org/fhir/sid/icd-10-cm"}]}, "clinicalStatus": {"coding": [{"code": "active"}]}}},
            ]
        },
        "procedures": {
            "entry": [
                {"resource": {"resourceType": "Procedure", "id": "proc-1", "code": {"coding": [{"code": "27447", "display": "Total knee arthroplasty (replacement)", "system": "http://www.ama-assn.org/go/cpt"}]}, "status": "completed", "performedDateTime": "2024-02-01"}},
                {"resource": {"resourceType": "Procedure", "id": "proc-2", "code": {"coding": [{"code": "72148", "display": "MRI lumbar spine without contrast", "system": "http://www.ama-assn.org/go/cpt"}]}, "status": "completed", "performedDateTime": "2024-01-10"}},
                {"resource": {"resourceType": "Procedure", "id": "proc-3", "code": {"coding": [{"code": "73560", "display": "X-ray knee, 1-2 views", "system": "http://www.ama-assn.org/go/cpt"}]}, "status": "completed", "performedDateTime": "2024-01-15"}},
                {"resource": {"resourceType": "Procedure", "id": "proc-4", "code": {"coding": [{"code": "20610", "display": "Arthrocentesis, major joint injection", "system": "http://www.ama-assn.org/go/cpt"}]}, "status": "completed", "performedDateTime": "2024-01-20"}},
                {"resource": {"resourceType": "Procedure", "id": "proc-5", "code": {"coding": [{"code": "97110", "display": "Therapeutic exercises, 15 min", "system": "http://www.ama-assn.org/go/cpt"}]}, "status": "completed", "performedDateTime": "2024-02-15"}},
                {"resource": {"resourceType": "Procedure", "id": "proc-6", "code": {"coding": [{"code": "97140", "display": "Manual therapy techniques, 15 min", "system": "http://www.ama-assn.org/go/cpt"}]}, "status": "completed", "performedDateTime": "2024-02-15"}},
            ]
        },
        "medications": {
            "entry": [
                {"resource": {"resourceType": "MedicationRequest", "id": "med-1", "medicationCodeableConcept": {"coding": [{"display": "Celecoxib 200 MG Oral Capsule"}]}, "status": "active", "dosageInstruction": [{"text": "Take 200mg once daily"}]}},
                {"resource": {"resourceType": "MedicationRequest", "id": "med-2", "medicationCodeableConcept": {"coding": [{"display": "Oxycodone 5 MG Oral Tablet"}]}, "status": "active", "dosageInstruction": [{"text": "Take 5mg every 6 hours as needed for pain"}]}},
            ]
        },
        "observations": {
            "entry": [
                {"resource": {"resourceType": "Observation", "id": "obs-1", "code": {"coding": [{"display": "Pain Score"}]}, "valueQuantity": {"value": 4, "unit": "/10"}, "effectiveDateTime": "2024-02-15", "category": [{"coding": [{"code": "vital-signs"}]}]}},
                {"resource": {"resourceType": "Observation", "id": "obs-2", "code": {"coding": [{"display": "Range of Motion - Knee Flexion"}]}, "valueQuantity": {"value": 90, "unit": "degrees"}, "effectiveDateTime": "2024-02-15", "category": [{"coding": [{"code": "vital-signs"}]}]}},
            ]
        },
        "encounters": {
            "entry": [
                {"resource": {"resourceType": "Encounter", "id": "enc-1", "class": {"code": "IMP", "display": "Inpatient"}, "status": "finished", "period": {"start": "2024-02-01", "end": "2024-02-03"}, "type": [{"text": "Total Knee Replacement Surgery"}]}},
                {"resource": {"resourceType": "Encounter", "id": "enc-2", "class": {"code": "AMB", "display": "Ambulatory"}, "status": "finished", "period": {"start": "2024-02-15"}, "type": [{"text": "Post-operative follow-up"}]}},
            ]
        },
        "allergies": {
            "entry": [
                {"resource": {"resourceType": "AllergyIntolerance", "id": "allergy-1", "code": {"coding": [{"display": "Sulfa drugs"}]}, "reaction": [{"manifestation": [{"coding": [{"display": "Rash"}]}]}]}},
                {"resource": {"resourceType": "AllergyIntolerance", "id": "allergy-2", "code": {"coding": [{"display": "Latex"}]}, "reaction": [{"manifestation": [{"coding": [{"display": "Anaphylaxis"}]}]}]}},
            ]
        },
        "immunizations": {"entry": []},
        "diagnosticReports": {"entry": []},
        "coverages": {"entry": []},
    },
}

@app.get("/demo/patients")
async def list_demo_patients():
    """List available demo patients with synthetic data"""
    patients = []
    for key, data in DEMO_PATIENTS.items():
        patient_info = data["patient"]
        patients.append({
            "id": key,
            "name": patient_info["name"][0]["text"],
            "birthDate": patient_info.get("birthDate"),
            "gender": patient_info.get("gender"),
            "description": f"{len(data.get('conditions', {}).get('entry', []))} conditions, {len(data.get('procedures', {}).get('entry', []))} procedures, {len(data.get('medications', {}).get('entry', []))} medications",
            "conditions": len(data.get('conditions', {}).get('entry', [])),
            "procedures": len(data.get('procedures', {}).get('entry', [])),
            "medications": len(data.get('medications', {}).get('entry', [])),
            "observations": len(data.get('observations', {}).get('entry', [])),
        })
    return {"patients": patients}

@app.get("/demo/patient/{patient_id}")
async def get_demo_patient(patient_id: str):
    """Get demo patient data"""
    if patient_id not in DEMO_PATIENTS:
        raise HTTPException(status_code=404, detail=f"Demo patient '{patient_id}' not found")
    return DEMO_PATIENTS[patient_id]["patient"]

@app.get("/demo/patient/{patient_id}/all")
async def get_demo_patient_all_data(patient_id: str):
    """Get all demo patient data including conditions, procedures, etc."""
    if patient_id not in DEMO_PATIENTS:
        raise HTTPException(status_code=404, detail=f"Demo patient '{patient_id}' not found")
    return DEMO_PATIENTS[patient_id]

@app.post("/demo/generate-claim/{patient_id}")
async def generate_demo_claim(patient_id: str):
    """Generate a claim from demo patient data"""
    if patient_id not in DEMO_PATIENTS:
        raise HTTPException(status_code=404, detail=f"Demo patient '{patient_id}' not found")
    
    demo_data = DEMO_PATIENTS[patient_id]
    
    # Convert all FHIR data to evidence atoms
    atoms = convert_all_fhir_to_atoms(demo_data)
    
    # Generate claim
    claim = generate_claim_from_atoms(atoms, demo_data["patient"])
    
    return claim

@app.get("/fhir/patient")
async def get_patient(bridge_url: str = "http://localhost:3000"):
    """Fetch patient data from the Epic FHIR Bridge"""
    try:
        async with httpx.AsyncClient() as client:
            # Check auth status
            status_resp = await client.get(f"{bridge_url}/auth/status")
            status_data = status_resp.json()
            
            if not status_data.get("authenticated"):
                raise HTTPException(
                    status_code=401,
                    detail="Not authenticated with Epic. Please login first at the bridge.",
                )
            
            # Fetch patient
            patient_resp = await client.get(f"{bridge_url}/fhir/patient")
            patient_resp.raise_for_status()
            return patient_resp.json()
            
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to Epic FHIR Bridge at {bridge_url}: {str(e)}",
        )

@app.post("/pipeline/run", response_model=ClaimResponse)
async def run_pipeline(request: PipelineRequest):
    """
    Run the full FHIR-to-Claim pipeline:
    1. Use provided FHIR data OR fetch from Epic FHIR Bridge
    2. Convert FHIR resources to EvidenceAtoms
    3. Generate claim using Evidence-Bound Generation
    """
    print(f"DEBUG: Received request: {request}")
    print(f"DEBUG: fhir_data type: {type(request.fhir_data)}, value: {request.fhir_data}")
    
    patient_data = None
    all_fhir_data = None
    
    # If FHIR data provided directly, use it
    if request.fhir_data:
        # Check if this is a single Patient resource or full data
        if request.fhir_data.get('resourceType') == 'Patient':
            patient_data = request.fhir_data
        elif 'patient' in request.fhir_data:
            all_fhir_data = request.fhir_data
            patient_data = request.fhir_data.get('patient')
        else:
            patient_data = request.fhir_data
    else:
        # Try to fetch ALL data from bridge
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Check auth status
                status_resp = await client.get(f"{request.bridge_url}/status")
                status_data = status_resp.json()
                
                if not status_data.get("authenticated"):
                    raise HTTPException(
                        status_code=401,
                        detail="Not authenticated with Epic. Please visit the bridge and login first.",
                    )
                
                # Try to fetch ALL clinical data
                try:
                    all_resp = await client.get(f"{request.bridge_url}/fhir/all")
                    all_resp.raise_for_status()
                    all_fhir_data = all_resp.json()
                    patient_data = all_fhir_data.get('patient')
                    print(f"Fetched all FHIR data: {list(all_fhir_data.keys())}")
                except Exception as e:
                    print(f"Could not fetch all data, falling back to patient only: {e}")
                    # Fallback to just patient
                    patient_resp = await client.get(f"{request.bridge_url}/fhir/patient")
                    patient_resp.raise_for_status()
                    patient_data = patient_resp.json()
                
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"FHIR API error: {e.response.text}",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Cannot connect to Epic FHIR Bridge: {str(e)}",
            )
    
    if not patient_data:
        raise HTTPException(
            status_code=400,
            detail="No FHIR data provided and could not fetch from bridge.",
        )
    
    # Convert to EvidenceAtoms
    if all_fhir_data:
        atoms = convert_all_fhir_to_atoms(all_fhir_data)
    else:
        atoms = convert_patient_to_atoms(patient_data)
    
    # Generate claim
    claim = generate_claim_from_atoms(atoms, patient_data)
    
    return claim

class FhirDataRequest(BaseModel):
    """Request model for FHIR data - allows any JSON structure"""
    class Config:
        extra = "allow"  # Allow any additional fields

@app.post("/generate-claim", response_model=ClaimResponse)
async def generate_claim_direct(request: Request):
    """
    Direct endpoint to generate claim from FHIR data.
    Bypasses the bridge - frontend sends FHIR data directly.
    """
    try:
        fhir_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON in request body")
    
    if not fhir_data:
        raise HTTPException(status_code=400, detail="No FHIR data provided")
    
    # Convert to EvidenceAtoms
    atoms = convert_patient_to_atoms(fhir_data)
    
    # Generate claim
    claim = generate_claim_from_atoms(atoms, fhir_data)
    
    return claim

@app.get("/auth/status")
async def check_bridge_auth(bridge_url: str = "http://localhost:3000"):
    """Check if the Epic FHIR Bridge is authenticated"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{bridge_url}/auth/status")
            return resp.json()
    except httpx.RequestError as e:
        return {
            "authenticated": False,
            "error": f"Cannot connect to bridge: {str(e)}",
        }

# Direct proxy endpoints for the frontend
@app.get("/proxy/auth/status")
async def proxy_auth_status():
    """Proxy auth status check to avoid CORS issues"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:3000/auth/status")
            return resp.json()
    except httpx.RequestError as e:
        return {"authenticated": False, "error": str(e)}

@app.get("/proxy/fhir/patient")
async def proxy_fhir_patient():
    """Proxy patient fetch to avoid CORS issues"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:3000/fhir/patient")
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Not authenticated or patient not found")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=str(e))

# ============ Ollama Narrative Generation ============

NARRATIVE_SYSTEM_PROMPT = """You are a medical billing specialist writing a professional insurance claim narrative.
You MUST cite evidence using the exact format [EV-xxxxxxxx] where xxxxxxxx is the evidence ID provided.
Every factual statement MUST include at least one citation.
Write in a clear, professional tone suitable for insurance review.
Do not invent any information - only use what is provided in the evidence."""

async def generate_narrative_section(
    section_type: str,
    evidence_atoms: List[EvidenceAtom],
    context: Dict[str, Any]
) -> CitedSection:
    """Generate a narrative section with inline citations using Ollama"""
    
    # Build evidence context for the LLM
    evidence_text = "\n".join([
        f"[{atom.evidence_id}]: {atom.content_excerpt} (Source: {atom.source_system}, Type: {atom.evidence_type})"
        for atom in evidence_atoms
    ])
    
    prompts = {
        "patient": f"""Write a brief patient identification paragraph for an insurance claim.
Use ONLY the following evidence and cite each fact with [EV-xxx] format:

EVIDENCE:
{evidence_text}

PATIENT INFO:
{json.dumps(context.get('patient', {}), indent=2)}

Write 2-3 sentences identifying the patient, including name, date of birth, and relevant demographics.
Every fact must have a citation like [EV-xxxxxxxx].""",

        "diagnoses": f"""Write a clinical diagnosis section for an insurance claim.
Use ONLY the following evidence and cite each fact with [EV-xxx] format:

EVIDENCE:
{evidence_text}

DIAGNOSES:
{json.dumps(context.get('diagnoses', []), indent=2)}

Write a paragraph explaining each diagnosis code and its clinical basis.
Every diagnosis must reference supporting evidence with [EV-xxxxxxxx] citations.""",

        "procedures": f"""Write a procedures/services section for an insurance claim.
Use ONLY the following evidence and cite each fact with [EV-xxx] format:

EVIDENCE:
{evidence_text}

PROCEDURES:
{json.dumps(context.get('procedures', []), indent=2)}

Write a paragraph describing each procedure code (CPT/HCPCS), why it was performed, and its supporting documentation.
Every procedure must reference supporting evidence with [EV-xxxxxxxx] citations.""",

        "medical_necessity": f"""Write a medical necessity justification for an insurance claim.
Use ONLY the following evidence and cite each fact with [EV-xxx] format:

EVIDENCE:
{evidence_text}

DIAGNOSES:
{json.dumps(context.get('diagnoses', []), indent=2)}

PROCEDURES:
{json.dumps(context.get('procedures', []), indent=2)}

Write 2-3 paragraphs explaining why each procedure was medically necessary given the patient's diagnoses.
Link procedures to diagnoses and cite supporting evidence with [EV-xxxxxxxx] format.""",

        "billing_summary": f"""Write a billing summary section for an insurance claim.
Use ONLY the following evidence and cite each fact with [EV-xxx] format:

EVIDENCE:
{evidence_text}

PROCEDURES:
{json.dumps(context.get('procedures', []), indent=2)}

TOTAL CHARGES: ${context.get('total_charges', 0):.2f}

Write a brief summary of all charges, itemizing each procedure code and its charge.
Reference the supporting documentation for each charge with [EV-xxxxxxxx] citations."""
    }
    
    prompt = prompts.get(section_type, "")
    if not prompt:
        return CitedSection(
            section_title=section_type.replace("_", " ").title(),
            content="Section not available.",
            evidence_ids=[]
        )
    
    # Call Ollama
    response = await call_ollama(prompt, NARRATIVE_SYSTEM_PROMPT)
    
    if not response:
        # Fallback to rule-based generation if Ollama fails
        response = generate_fallback_section(section_type, evidence_atoms, context)
    
    # Extract evidence IDs from the response
    evidence_ids = re.findall(r'\[EV-[a-f0-9]+\]', response)
    evidence_ids = [eid.strip('[]') for eid in evidence_ids]
    
    return CitedSection(
        section_title=section_type.replace("_", " ").title(),
        content=response,
        evidence_ids=list(set(evidence_ids))
    )

def generate_fallback_section(
    section_type: str,
    evidence_atoms: List[EvidenceAtom],
    context: Dict[str, Any]
) -> str:
    """Fallback rule-based section generation when Ollama is unavailable"""
    
    if section_type == "patient":
        patient = context.get('patient', {})
        name = patient.get('name', [{}])[0].get('text', 'Unknown Patient')
        dob = patient.get('birthDate', 'Unknown')
        gender = patient.get('gender', 'Unknown')
        name_atom = next((a for a in evidence_atoms if a.evidence_type == "patient_name"), None)
        dob_atom = next((a for a in evidence_atoms if a.evidence_type == "patient_dob"), None)
        gender_atom = next((a for a in evidence_atoms if a.evidence_type == "patient_gender"), None)
        
        parts = []
        if name_atom:
            parts.append(f"Patient {name} [{name_atom.evidence_id}]")
        else:
            parts.append(f"Patient {name}")
        if dob_atom:
            parts.append(f"with date of birth {dob} [{dob_atom.evidence_id}]")
        if gender_atom:
            parts.append(f"({gender}) [{gender_atom.evidence_id}]")
        
        return " ".join(parts) + " presented for evaluation and treatment."
    
    elif section_type == "diagnoses":
        diagnoses = context.get('diagnoses', [])
        lines = []
        for dx in diagnoses:
            ev_refs = " ".join([f"[{eid}]" for eid in dx.get('supporting_evidence', [])])
            lines.append(f"• {dx.get('code', 'N/A')} - {dx.get('description', 'N/A')} {ev_refs}")
        return "The following diagnoses were established based on clinical evidence:\n" + "\n".join(lines)
    
    elif section_type == "procedures":
        procedures = context.get('procedures', [])
        lines = []
        for proc in procedures:
            ev_refs = " ".join([f"[{eid}]" for eid in proc.get('supporting_evidence', [])])
            lines.append(f"• {proc.get('code', 'N/A')} ({proc.get('code_type', 'CPT')}) - {proc.get('description', 'N/A')} - ${proc.get('charge_amount', 0):.2f} {ev_refs}")
            if proc.get('rationale'):
                lines.append(f"  Rationale: {proc.get('rationale')}")
        return "The following procedures were performed:\n" + "\n".join(lines)
    
    elif section_type == "medical_necessity":
        return "Medical necessity is established through the documented clinical findings and the patient's presenting condition. Each procedure performed was directly related to the diagnosis and represents the standard of care for the patient's condition."
    
    elif section_type == "billing_summary":
        total = context.get('total_charges', 0)
        procedures = context.get('procedures', [])
        lines = [f"• {p.get('code')}: ${p.get('charge_amount', 0):.2f}" for p in procedures]
        return f"Total charges for this encounter: ${total:.2f}\n" + "\n".join(lines)
    
    return "Section content not available."

@app.post("/narrative/generate", response_model=NarrativeClaim)
async def generate_narrative_claim(claim: ClaimResponse):
    """
    Generate a full narrative claim document with Zotero-style citations.
    Uses Ollama with Gemma to write professional claim narratives.
    """
    print(f"Generating narrative for claim {claim.id}")
    
    # Get patient data from atoms
    patient_data = {}
    for atom in claim.evidence_atoms:
        if "patient" in atom.evidence_type.lower():
            # Parse patient info from atoms
            if "name" in atom.evidence_type:
                patient_data["name"] = [{"text": atom.content_excerpt.replace("Patient Name: ", "")}]
            elif "dob" in atom.evidence_type:
                patient_data["birthDate"] = atom.content_excerpt.replace("Date of Birth: ", "")
            elif "gender" in atom.evidence_type:
                patient_data["gender"] = atom.content_excerpt.replace("Gender: ", "")
    
    context = {
        "patient": patient_data,
        "diagnoses": [d.model_dump() for d in claim.diagnoses],
        "procedures": [l.model_dump() for l in claim.lines],
        "total_charges": claim.total_charges,
    }
    
    # Generate each section
    patient_section = await generate_narrative_section("patient", claim.evidence_atoms, context)
    diagnoses_section = await generate_narrative_section("diagnoses", claim.evidence_atoms, context)
    procedures_section = await generate_narrative_section("procedures", claim.evidence_atoms, context)
    medical_necessity_section = await generate_narrative_section("medical_necessity", claim.evidence_atoms, context)
    billing_summary_section = await generate_narrative_section("billing_summary", claim.evidence_atoms, context)
    
    # Build summary
    summary = f"Insurance claim for {claim.patient_name or 'Patient'} with {len(claim.diagnoses)} diagnosis(es) and {len(claim.lines)} procedure(s). Total charges: ${claim.total_charges:.2f}."
    
    return NarrativeClaim(
        claim_id=claim.id,
        title=f"Insurance Claim - {claim.patient_name or 'Patient'} - {claim.id}",
        summary=summary,
        patient_section=patient_section,
        diagnoses_section=diagnoses_section,
        procedures_section=procedures_section,
        medical_necessity_section=medical_necessity_section,
        billing_summary_section=billing_summary_section,
        evidence_atoms=claim.evidence_atoms,
        total_charges=claim.total_charges,
        status=claim.status,
        requires_review=claim.requires_review,
        review_reasons=claim.review_reasons,
        generated_at=datetime.now().isoformat(),
        llm_model=OLLAMA_MODEL
    )

@app.get("/ollama/status")
async def check_ollama_status():
    """Check if Ollama is running and the model is available"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check if Ollama is running
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()
            data = response.json()
            
            models = [m.get("name", "") for m in data.get("models", [])]
            model_available = any(OLLAMA_MODEL in m for m in models)
            
            return {
                "ollama_running": True,
                "models_available": models,
                "target_model": OLLAMA_MODEL,
                "model_ready": model_available,
                "message": f"Model {OLLAMA_MODEL} is {'available' if model_available else 'not found - run: ollama pull ' + OLLAMA_MODEL}"
            }
    except httpx.RequestError as e:
        return {
            "ollama_running": False,
            "error": str(e),
            "message": "Ollama is not running. Start it with: ollama serve"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

