"""
FHIR to EvidenceAtom Converter

Transforms FHIR R4 resources from Epic into EvidenceAtoms
that can be processed by the claims intelligence engine.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import json
import uuid

from ..evidence.atoms import EvidenceAtom, Location, store_evidence_atom, EvidenceType


def generate_content_hash(content: str) -> str:
    """Generate SHA256 hash of content for immutability verification."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def fhir_patient_to_atoms(patient: Dict[str, Any]) -> List[EvidenceAtom]:
    """
    Convert a FHIR Patient resource into EvidenceAtoms.
    
    Extracts:
    - Demographics (name, DOB, gender)
    - Contact information
    - Identifiers
    - Address
    """
    atoms = []
    patient_id = patient.get('id', 'unknown')
    
    # Extract name
    names = patient.get('name', [])
    if names:
        official_name = next((n for n in names if n.get('use') == 'official'), names[0])
        name_text = official_name.get('text') or f"{' '.join(official_name.get('given', []))} {official_name.get('family', '')}"
        
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid.uuid4()}",
            evidence_type=EvidenceType.HISTORY,
            source_system="EPIC",
            document_id=f"PAT-{patient_id}",
            document_name=f"Patient/{patient_id}",
            document_hash=hashlib.sha256(f"Patient/{patient_id}".encode()).hexdigest(),
            author="FHIR Import",
            timestamp=datetime.now(),
            content_excerpt=f"Patient Name: {name_text.strip()}",
            location=Location(section="name"),
            extraction_confidence=1.0
        ))
    
    # Extract DOB
    birth_date = patient.get('birthDate')
    if birth_date:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid.uuid4()}",
            evidence_type=EvidenceType.HISTORY,
            source_system="EPIC",
            document_id=f"PAT-{patient_id}",
            document_name=f"Patient/{patient_id}",
            document_hash=hashlib.sha256(f"Patient/{patient_id}".encode()).hexdigest(),
            author="FHIR Import",
            timestamp=datetime.now(),
            content_excerpt=f"Date of Birth: {birth_date}",
            location=Location(section="birthDate"),
            extraction_confidence=1.0
        ))
    
    # Extract gender
    gender = patient.get('gender')
    if gender:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid.uuid4()}",
            evidence_type=EvidenceType.HISTORY,
            source_system="EPIC",
            document_id=f"PAT-{patient_id}",
            document_name=f"Patient/{patient_id}",
            document_hash=hashlib.sha256(f"Patient/{patient_id}".encode()).hexdigest(),
            author="FHIR Import",
            timestamp=datetime.now(),
            content_excerpt=f"Gender: {gender}",
            location=Location(section="gender"),
            extraction_confidence=1.0
        ))
    
    # Extract address
    addresses = patient.get('address', [])
    for addr in addresses:
        addr_text = addr.get('text') or ', '.join(filter(None, [
            ' '.join(addr.get('line', [])),
            addr.get('city'),
            addr.get('state'),
            addr.get('postalCode')
        ]))
        if addr_text:
            atoms.append(EvidenceAtom(
                evidence_id=f"EV-{uuid.uuid4()}",
                evidence_type=EvidenceType.HISTORY,
                source_system="EPIC",
                document_id=f"PAT-{patient_id}",
                document_name=f"Patient/{patient_id}",
                document_hash=hashlib.sha256(f"Patient/{patient_id}".encode()).hexdigest(),
                author="FHIR Import",
                timestamp=datetime.now(),
                content_excerpt=f"Address: {addr_text}",
                location=Location(section="address"),
                extraction_confidence=1.0
            ))
    
    # Extract race/ethnicity from extensions
    extensions = patient.get('extension', [])
    for ext in extensions:
        url = ext.get('url', '')
        if 'us-core-race' in url:
            race_ext = ext.get('extension', [])
            for r in race_ext:
                if r.get('url') == 'text':
                    race_text = r.get('valueString', '')
                    if race_text:
                        atoms.append(EvidenceAtom(
                            evidence_id=f"EV-{uuid.uuid4()}",
                            evidence_type=EvidenceType.HISTORY,
                            source_system="EPIC",
                            document_id=f"PAT-{patient_id}",
                            document_name=f"Patient/{patient_id}",
                            document_hash=hashlib.sha256(f"Patient/{patient_id}".encode()).hexdigest(),
                            author="FHIR Import",
                            timestamp=datetime.now(),
                            content_excerpt=f"Race: {race_text}",
                            location=Location(section="race"),
                            extraction_confidence=1.0
                        ))
    
    return atoms


def fhir_condition_to_atoms(condition: Dict[str, Any]) -> List[EvidenceAtom]:
    """
    Convert a FHIR Condition resource into EvidenceAtoms.
    
    Extracts:
    - Diagnosis code (ICD-10)
    - Clinical status
    - Onset date
    - Verification status
    """
    atoms = []
    condition_id = condition.get('id', 'unknown')
    
    # Extract diagnosis code
    code = condition.get('code', {})
    codings = code.get('coding', [])
    
    for coding in codings:
        system = coding.get('system', '')
        code_value = coding.get('code', '')
        display = coding.get('display', '')
        
        # Identify ICD-10 codes
        is_icd10 = 'icd-10' in system.lower() or 'icd10' in system.lower()
        code_type = "ICD-10" if is_icd10 else "diagnosis_code"
        
        content = f"Diagnosis: {display} (Code: {code_value})"
        
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid.uuid4()}",
            evidence_type=EvidenceType.HISTORY,
            source_system="EPIC",
            document_id=f"CON-{condition_id}",
            document_name=f"Condition/{condition_id}",
            document_hash=hashlib.sha256(f"Condition/{condition_id}".encode()).hexdigest(),
            author="FHIR Import",
            timestamp=datetime.now(),
            content_excerpt=content,
            location=Location(section="code"),
            extraction_confidence=1.0
        ))
    
    # Extract clinical status
    clinical_status = condition.get('clinicalStatus', {})
    status_codings = clinical_status.get('coding', [])
    if status_codings:
        status = status_codings[0].get('code', 'unknown')
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid.uuid4()}",
            evidence_type=EvidenceType.HISTORY,
            source_system="EPIC",
            document_id=f"CON-{condition_id}",
            document_name=f"Condition/{condition_id}",
            document_hash=hashlib.sha256(f"Condition/{condition_id}".encode()).hexdigest(),
            author="FHIR Import",
            timestamp=datetime.now(),
            content_excerpt=f"Clinical Status: {status}",
            location=Location(section="clinicalStatus"),
            extraction_confidence=1.0
        ))
    
    # Extract onset date
    onset = condition.get('onsetDateTime') or condition.get('recordedDate')
    if onset:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid.uuid4()}",
            evidence_type=EvidenceType.HISTORY,
            source_system="EPIC",
            document_id=f"CON-{condition_id}",
            document_name=f"Condition/{condition_id}",
            document_hash=hashlib.sha256(f"Condition/{condition_id}".encode()).hexdigest(),
            author="FHIR Import",
            timestamp=datetime.now(),
            content_excerpt=f"Onset/Recorded Date: {onset}",
            location=Location(section="onset"),
            extraction_confidence=1.0
        ))
    
    return atoms


def fhir_coverage_to_atoms(coverage: Dict[str, Any]) -> List[EvidenceAtom]:
    """
    Convert a FHIR Coverage resource into EvidenceAtoms.
    
    Extracts:
    - Insurance plan details
    - Policy holder
    - Coverage period
    - Payer information
    """
    atoms = []
    coverage_id = coverage.get('id', 'unknown')
    
    # Extract coverage status
    status = coverage.get('status', 'unknown')
    atoms.append(EvidenceAtom(
        evidence_id=f"EV-{uuid.uuid4()}",
        evidence_type=EvidenceType.INSURANCE,
        source_system="EPIC",
        document_id=f"COV-{coverage_id}",
        document_name=f"Coverage/{coverage_id}",
        document_hash=hashlib.sha256(f"Coverage/{coverage_id}".encode()).hexdigest(),
        author="FHIR Import",
        timestamp=datetime.now(),
        content_excerpt=f"Coverage Status: {status}",
        location=Location(section="status"),
        confidence=1.0
    ))
    
    # Extract payer
    payors = coverage.get('payor', [])
    for payor in payors:
        payor_name = payor.get('display', payor.get('reference', 'Unknown Payer'))
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid.uuid4()}",
            evidence_type=EvidenceType.INSURANCE,
            source_system="EPIC",
            document_id=f"COV-{coverage_id}",
            document_name=f"Coverage/{coverage_id}",
            document_hash=hashlib.sha256(f"Coverage/{coverage_id}".encode()).hexdigest(),
            author="FHIR Import",
            timestamp=datetime.now(),
            content_excerpt=f"Insurance Payer: {payor_name}",
            location=Location(section="payor"),
            extraction_confidence=1.0
        ))
    
    # Extract coverage period
    period = coverage.get('period', {})
    start = period.get('start')
    end = period.get('end')
    if start or end:
        period_text = f"Coverage Period: {start or 'N/A'} to {end or 'ongoing'}"
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid.uuid4()}",
            evidence_type=EvidenceType.INSURANCE,
            source_system="EPIC",
            document_id=f"COV-{coverage_id}",
            document_name=f"Coverage/{coverage_id}",
            document_hash=hashlib.sha256(f"Coverage/{coverage_id}".encode()).hexdigest(),
            author="FHIR Import",
            timestamp=datetime.now(),
            content_excerpt=period_text,
            location=Location(section="period"),
            extraction_confidence=1.0
        ))
    
    # Extract class info (plan details)
    classes = coverage.get('class', [])
    for cls in classes:
        class_type = cls.get('type', {}).get('coding', [{}])[0].get('code', 'unknown')
        class_value = cls.get('value', '')
        class_name = cls.get('name', '')
        
        if class_value or class_name:
            class_text = f"Coverage Class ({class_type}): {class_name or class_value}"
            atoms.append(EvidenceAtom(
                evidence_id=f"EV-{uuid.uuid4()}",
                evidence_type=EvidenceType.INSURANCE,
                source_system="EPIC",
                document_id=f"COV-{coverage_id}",
                document_name=f"Coverage/{coverage_id}",
                document_hash=hashlib.sha256(f"Coverage/{coverage_id}".encode()).hexdigest(),
                author="FHIR Import",
                timestamp=datetime.now(),
                content_excerpt=class_text,
                location=Location(section="class"),
                extraction_confidence=1.0
            ))
    
    return atoms


def fhir_procedure_to_atoms(procedure: Dict[str, Any]) -> List[EvidenceAtom]:
    """
    Convert a FHIR Procedure resource into EvidenceAtoms.
    
    Extracts:
    - Procedure code (CPT/HCPCS/SNOMED)
    - Status
    - Performed date
    - Reason
    """
    atoms = []
    procedure_id = procedure.get('id', 'unknown')
    
    # Extract procedure code
    code = procedure.get('code', {})
    codings = code.get('coding', [])
    
    for coding in codings:
        system = coding.get('system', '')
        code_value = coding.get('code', '')
        display = coding.get('display', '')
        
        # Identify code type
        if 'cpt' in system.lower():
            code_type = "CPT"
        elif 'hcpcs' in system.lower():
            code_type = "HCPCS"
        elif 'snomed' in system.lower():
            code_type = "SNOMED"
        else:
            code_type = "procedure_code"
        
        content = f"Procedure: {display} ({code_type} Code: {code_value})"
        
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid.uuid4()}",
            evidence_type=EvidenceType.PROCEDURE,
            source_system="EPIC",
            document_id=f"PROC-{procedure_id}",
            document_name=f"Procedure/{procedure_id}",
            document_hash=hashlib.sha256(f"Procedure/{procedure_id}".encode()).hexdigest(),
            author="FHIR Import",
            timestamp=datetime.now(),
            content_excerpt=content,
            location=Location(section="code"),
            extraction_confidence=1.0
        ))
    
    # Extract status
    status = procedure.get('status', '')
    if status:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid.uuid4()}",
            evidence_type=EvidenceType.PROCEDURE,
            source_system="EPIC",
            document_id=f"PROC-{procedure_id}",
            document_name=f"Procedure/{procedure_id}",
            document_hash=hashlib.sha256(f"Procedure/{procedure_id}".encode()).hexdigest(),
            author="FHIR Import",
            timestamp=datetime.now(),
            content_excerpt=f"Procedure Status: {status}",
            location=Location(section="status"),
            extraction_confidence=1.0
        ))
    
    # Extract performed date
    performed = procedure.get('performedDateTime') or procedure.get('performedPeriod', {}).get('start')
    if performed:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid.uuid4()}",
            evidence_type=EvidenceType.PROCEDURE,
            source_system="EPIC",
            document_id=f"PROC-{procedure_id}",
            document_name=f"Procedure/{procedure_id}",
            document_hash=hashlib.sha256(f"Procedure/{procedure_id}".encode()).hexdigest(),
            author="FHIR Import",
            timestamp=datetime.now(),
            content_excerpt=f"Procedure Date: {performed}",
            location=Location(section="performed"),
            extraction_confidence=1.0
        ))
    
    return atoms


def fhir_medication_to_atoms(medication: Dict[str, Any]) -> List[EvidenceAtom]:
    """
    Convert a FHIR MedicationRequest resource into EvidenceAtoms.
    
    Extracts:
    - Medication name/code
    - Dosage instructions
    - Status
    - Prescriber
    """
    atoms = []
    med_id = medication.get('id', 'unknown')
    
    # Extract medication code
    med_code = medication.get('medicationCodeableConcept', {})
    codings = med_code.get('coding', [])
    med_text = med_code.get('text', '')
    
    for coding in codings:
        code_value = coding.get('code', '')
        display = coding.get('display', med_text)
        system = coding.get('system', '')
        
        content = f"Medication: {display} (Code: {code_value})"
        
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid.uuid4()}",
            evidence_type=EvidenceType.MEDICATION,
            source_system="EPIC",
            document_id=f"MED-{med_id}",
            document_name=f"MedicationRequest/{med_id}",
            document_hash=hashlib.sha256(f"MedicationRequest/{med_id}".encode()).hexdigest(),
            author="FHIR Import",
            timestamp=datetime.now(),
            content_excerpt=content,
            location=Location(section="medication"),
            extraction_confidence=1.0
        ))
    
    # If no codings but has text, use that
    if not codings and med_text:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid.uuid4()}",
            evidence_type=EvidenceType.MEDICATION,
            source_system="EPIC",
            document_id=f"MED-{med_id}",
            document_name=f"MedicationRequest/{med_id}",
            document_hash=hashlib.sha256(f"MedicationRequest/{med_id}".encode()).hexdigest(),
            author="FHIR Import",
            timestamp=datetime.now(),
            content_excerpt=f"Medication: {med_text}",
            location=Location(section="medication"),
            extraction_confidence=1.0
        ))
    
    # Extract status
    status = medication.get('status', '')
    if status:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid.uuid4()}",
            evidence_type=EvidenceType.MEDICATION,
            source_system="EPIC",
            document_id=f"MED-{med_id}",
            document_name=f"MedicationRequest/{med_id}",
            document_hash=hashlib.sha256(f"MedicationRequest/{med_id}".encode()).hexdigest(),
            author="FHIR Import",
            timestamp=datetime.now(),
            content_excerpt=f"Medication Status: {status}",
            location=Location(section="status"),
            extraction_confidence=1.0
        ))
    
    # Extract dosage instructions
    dosage = medication.get('dosageInstruction', [])
    for d in dosage:
        text = d.get('text', '')
        if text:
            atoms.append(EvidenceAtom(
                evidence_id=f"EV-{uuid.uuid4()}",
                evidence_type=EvidenceType.MEDICATION,
                source_system="EPIC",
                document_id=f"MED-{med_id}",
                document_name=f"MedicationRequest/{med_id}",
                document_hash=hashlib.sha256(f"MedicationRequest/{med_id}".encode()).hexdigest(),
                author="FHIR Import",
                timestamp=datetime.now(),
                content_excerpt=f"Dosage: {text}",
                location=Location(section="dosage"),
                extraction_confidence=1.0
            ))
    
    return atoms


def fhir_observation_to_atoms(observation: Dict[str, Any]) -> List[EvidenceAtom]:
    """
    Convert a FHIR Observation resource into EvidenceAtoms.
    
    Extracts:
    - Observation type (vital sign, lab, etc.)
    - Value
    - Date
    - Interpretation
    """
    atoms = []
    obs_id = observation.get('id', 'unknown')
    
    # Determine observation type
    categories = observation.get('category', [])
    obs_type = EvidenceType.LAB
    for cat in categories:
        codings = cat.get('coding', [])
        for c in codings:
            code = c.get('code', '')
            if code == 'vital-signs':
                obs_type = EvidenceType.VITAL_SIGN
            elif code == 'laboratory':
                obs_type = EvidenceType.LAB
    
    # Extract observation code
    code = observation.get('code', {})
    codings = code.get('coding', [])
    code_text = code.get('text', '')
    
    for coding in codings:
        display = coding.get('display', code_text)
        code_value = coding.get('code', '')
        
        # Extract value
        value_quantity = observation.get('valueQuantity', {})
        value_string = observation.get('valueString', '')
        value_codeable = observation.get('valueCodeableConcept', {})
        
        if value_quantity:
            value = f"{value_quantity.get('value', '')} {value_quantity.get('unit', '')}"
        elif value_string:
            value = value_string
        elif value_codeable:
            value = value_codeable.get('text', value_codeable.get('coding', [{}])[0].get('display', ''))
        else:
            value = "N/A"
        
        content = f"Observation: {display} = {value}"
        
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid.uuid4()}",
            evidence_type=obs_type,
            source_system="EPIC",
            document_id=f"OBS-{obs_id}",
            document_name=f"Observation/{obs_id}",
            document_hash=hashlib.sha256(f"Observation/{obs_id}".encode()).hexdigest(),
            author="FHIR Import",
            timestamp=datetime.now(),
            content_excerpt=content,
            location=Location(section="value"),
            extraction_confidence=1.0
        ))
    
    # Extract effective date
    effective = observation.get('effectiveDateTime') or observation.get('effectivePeriod', {}).get('start')
    if effective and codings:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid.uuid4()}",
            evidence_type=obs_type,
            source_system="EPIC",
            document_id=f"OBS-{obs_id}",
            document_name=f"Observation/{obs_id}",
            document_hash=hashlib.sha256(f"Observation/{obs_id}".encode()).hexdigest(),
            author="FHIR Import",
            timestamp=datetime.now(),
            content_excerpt=f"Observation Date: {effective}",
            location=Location(section="effective"),
            extraction_confidence=1.0
        ))
    
    return atoms


def fhir_encounter_to_atoms(encounter: Dict[str, Any]) -> List[EvidenceAtom]:
    """
    Convert a FHIR Encounter resource into EvidenceAtoms.
    """
    atoms = []
    enc_id = encounter.get('id', 'unknown')
    
    # Extract encounter type
    types = encounter.get('type', [])
    for t in types:
        codings = t.get('coding', [])
        for coding in codings:
            display = coding.get('display', t.get('text', ''))
            if display:
                atoms.append(EvidenceAtom(
                    evidence_id=f"EV-{uuid.uuid4()}",
                    evidence_type=EvidenceType.CLINICAL_NOTE,
                    source_system="EPIC",
                    document_id=f"ENC-{enc_id}",
                    document_name=f"Encounter/{enc_id}",
                    document_hash=hashlib.sha256(f"Encounter/{enc_id}".encode()).hexdigest(),
                    author="FHIR Import",
                    timestamp=datetime.now(),
                    content_excerpt=f"Encounter Type: {display}",
                    location=Location(section="type"),
                    extraction_confidence=1.0
                ))
    
    # Extract period
    period = encounter.get('period', {})
    start = period.get('start', '')
    end = period.get('end', '')
    if start:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid.uuid4()}",
            evidence_type=EvidenceType.CLINICAL_NOTE,
            source_system="EPIC",
            document_id=f"ENC-{enc_id}",
            document_name=f"Encounter/{enc_id}",
            document_hash=hashlib.sha256(f"Encounter/{enc_id}".encode()).hexdigest(),
            author="FHIR Import",
            timestamp=datetime.now(),
            content_excerpt=f"Encounter Date: {start}" + (f" to {end}" if end else ""),
            location=Location(section="period"),
            extraction_confidence=1.0
        ))
    
    # Extract class (inpatient, outpatient, etc.)
    enc_class = encounter.get('class', {})
    class_display = enc_class.get('display', enc_class.get('code', ''))
    if class_display:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid.uuid4()}",
            evidence_type=EvidenceType.CLINICAL_NOTE,
            source_system="EPIC",
            document_id=f"ENC-{enc_id}",
            document_name=f"Encounter/{enc_id}",
            document_hash=hashlib.sha256(f"Encounter/{enc_id}".encode()).hexdigest(),
            author="FHIR Import",
            timestamp=datetime.now(),
            content_excerpt=f"Encounter Class: {class_display}",
            location=Location(section="class"),
            extraction_confidence=1.0
        ))
    
    return atoms


def fhir_allergy_to_atoms(allergy: Dict[str, Any]) -> List[EvidenceAtom]:
    """
    Convert a FHIR AllergyIntolerance resource into EvidenceAtoms.
    """
    atoms = []
    allergy_id = allergy.get('id', 'unknown')
    
    # Extract allergen
    code = allergy.get('code', {})
    codings = code.get('coding', [])
    text = code.get('text', '')
    
    for coding in codings:
        display = coding.get('display', text)
        if display:
            atoms.append(EvidenceAtom(
                evidence_id=f"EV-{uuid.uuid4()}",
                evidence_type=EvidenceType.HISTORY,
                source_system="EPIC",
                document_id=f"ALG-{allergy_id}",
                document_name=f"AllergyIntolerance/{allergy_id}",
                document_hash=hashlib.sha256(f"AllergyIntolerance/{allergy_id}".encode()).hexdigest(),
                author="FHIR Import",
                timestamp=datetime.now(),
                content_excerpt=f"Allergy: {display}",
                location=Location(section="code"),
                extraction_confidence=1.0
            ))
    
    # Extract clinical status
    clinical_status = allergy.get('clinicalStatus', {})
    status_codings = clinical_status.get('coding', [])
    if status_codings:
        status = status_codings[0].get('code', '')
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid.uuid4()}",
            evidence_type=EvidenceType.HISTORY,
            source_system="EPIC",
            document_id=f"ALG-{allergy_id}",
            document_name=f"AllergyIntolerance/{allergy_id}",
            document_hash=hashlib.sha256(f"AllergyIntolerance/{allergy_id}".encode()).hexdigest(),
            author="FHIR Import",
            timestamp=datetime.now(),
            content_excerpt=f"Allergy Status: {status}",
            location=Location(section="clinicalStatus"),
            extraction_confidence=1.0
        ))
    
    return atoms


def fhir_immunization_to_atoms(immunization: Dict[str, Any]) -> List[EvidenceAtom]:
    """
    Convert a FHIR Immunization resource into EvidenceAtoms.
    """
    atoms = []
    imm_id = immunization.get('id', 'unknown')
    
    # Extract vaccine
    vaccine = immunization.get('vaccineCode', {})
    codings = vaccine.get('coding', [])
    text = vaccine.get('text', '')
    
    for coding in codings:
        display = coding.get('display', text)
        if display:
            atoms.append(EvidenceAtom(
                evidence_id=f"EV-{uuid.uuid4()}",
                evidence_type=EvidenceType.HISTORY,
                source_system="EPIC",
                document_id=f"IMM-{imm_id}",
                document_name=f"Immunization/{imm_id}",
                document_hash=hashlib.sha256(f"Immunization/{imm_id}".encode()).hexdigest(),
                author="FHIR Import",
                timestamp=datetime.now(),
                content_excerpt=f"Immunization: {display}",
                location=Location(section="vaccineCode"),
                extraction_confidence=1.0
            ))
    
    # Extract occurrence date
    occurrence = immunization.get('occurrenceDateTime', '')
    if occurrence:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid.uuid4()}",
            evidence_type=EvidenceType.HISTORY,
            source_system="EPIC",
            document_id=f"IMM-{imm_id}",
            document_name=f"Immunization/{imm_id}",
            document_hash=hashlib.sha256(f"Immunization/{imm_id}".encode()).hexdigest(),
            author="FHIR Import",
            timestamp=datetime.now(),
            content_excerpt=f"Immunization Date: {occurrence}",
            location=Location(section="occurrence"),
            extraction_confidence=1.0
        ))
    
    return atoms


def fhir_diagnostic_report_to_atoms(report: Dict[str, Any]) -> List[EvidenceAtom]:
    """
    Convert a FHIR DiagnosticReport resource into EvidenceAtoms.
    """
    atoms = []
    report_id = report.get('id', 'unknown')
    
    # Extract report type
    code = report.get('code', {})
    codings = code.get('coding', [])
    text = code.get('text', '')
    
    for coding in codings:
        display = coding.get('display', text)
        if display:
            atoms.append(EvidenceAtom(
                evidence_id=f"EV-{uuid.uuid4()}",
                evidence_type=EvidenceType.LAB,
                source_system="EPIC",
                document_id=f"DR-{report_id}",
                document_name=f"DiagnosticReport/{report_id}",
                document_hash=hashlib.sha256(f"DiagnosticReport/{report_id}".encode()).hexdigest(),
                author="FHIR Import",
                timestamp=datetime.now(),
                content_excerpt=f"Diagnostic Report: {display}",
                location=Location(section="code"),
                extraction_confidence=1.0
            ))
    
    # Extract conclusion
    conclusion = report.get('conclusion', '')
    if conclusion:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid.uuid4()}",
            evidence_type=EvidenceType.LAB,
            source_system="EPIC",
            document_id=f"DR-{report_id}",
            document_name=f"DiagnosticReport/{report_id}",
            document_hash=hashlib.sha256(f"DiagnosticReport/{report_id}".encode()).hexdigest(),
            author="FHIR Import",
            timestamp=datetime.now(),
            content_excerpt=f"Conclusion: {conclusion[:500]}",  # Limit length
            location=Location(section="conclusion"),
            extraction_confidence=1.0
        ))
    
    return atoms


def fhir_eob_to_atoms(eob: Dict[str, Any]) -> List[EvidenceAtom]:
    """
    Convert a FHIR ExplanationOfBenefit resource into EvidenceAtoms.
    
    Extracts:
    - Claim details
    - Service items
    - Adjudication amounts
    - Payment information
    """
    atoms = []
    eob_id = eob.get('id', 'unknown')
    
    # Extract claim status
    status = eob.get('status', 'unknown')
    outcome = eob.get('outcome', 'unknown')
    atoms.append(EvidenceAtom(
        evidence_id=f"EV-{uuid.uuid4()}",
        evidence_type=EvidenceType.CLAIM,
        source_system="EPIC",
        document_id=f"EOB-{eob_id}",
        document_name=f"ExplanationOfBenefit/{eob_id}",
        document_hash=hashlib.sha256(f"ExplanationOfBenefit/{eob_id}".encode()).hexdigest(),
        author="FHIR Import",
        timestamp=datetime.now(),
        content_excerpt=f"Claim Status: {status}, Outcome: {outcome}",
        location=Location(section="status"),
        confidence=1.0
    ))
    
    # Extract billable period
    period = eob.get('billablePeriod', {})
    if period:
        period_text = f"Service Period: {period.get('start', 'N/A')} to {period.get('end', 'N/A')}"
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid.uuid4()}",
            evidence_type=EvidenceType.CLAIM,
            source_system="EPIC",
            document_id=f"EOB-{eob_id}",
            document_name=f"ExplanationOfBenefit/{eob_id}",
            document_hash=hashlib.sha256(f"ExplanationOfBenefit/{eob_id}".encode()).hexdigest(),
            author="FHIR Import",
            timestamp=datetime.now(),
            content_excerpt=period_text,
            location=Location(section="billablePeriod"),
            extraction_confidence=1.0
        ))
    
    # Extract service items
    items = eob.get('item', [])
    for idx, item in enumerate(items):
        service = item.get('productOrService', {})
        service_codes = service.get('coding', [])
        
        for coding in service_codes:
            code = coding.get('code', '')
            display = coding.get('display', '')
            system = coding.get('system', '')
            
            # Identify CPT codes
            is_cpt = 'cpt' in system.lower()
            code_type = "CPT" if is_cpt else "service_code"
            
            service_text = f"Service: {display} (Code: {code})"
            atoms.append(EvidenceAtom(
                evidence_id=f"EV-{uuid.uuid4()}",
                evidence_type=EvidenceType.PROCEDURE,
                source_system="EPIC",
                document_id=f"EOB-{eob_id}",
                document_name=f"ExplanationOfBenefit/{eob_id}",
                document_hash=hashlib.sha256(f"ExplanationOfBenefit/{eob_id}".encode()).hexdigest(),
                author="FHIR Import",
                timestamp=datetime.now(),
                content_excerpt=service_text,
                location=Location(section=f"item[{idx}]"),
                extraction_confidence=1.0
            ))
        
        # Extract adjudication amounts
        adjudications = item.get('adjudication', [])
        for adj in adjudications:
            category = adj.get('category', {}).get('coding', [{}])[0].get('code', 'unknown')
            amount = adj.get('amount', {})
            value = amount.get('value', 0)
            currency = amount.get('currency', 'USD')
            
            if value:
                adj_text = f"Adjudication ({category}): {currency} {value}"
                atoms.append(EvidenceAtom(
                    evidence_id=f"EV-{uuid.uuid4()}",
                    evidence_type=EvidenceType.CLAIM,
                    source_system="EPIC",
                    document_id=f"EOB-{eob_id}",
                    document_name=f"ExplanationOfBenefit/{eob_id}",
                    document_hash=hashlib.sha256(f"ExplanationOfBenefit/{eob_id}".encode()).hexdigest(),
                    author="FHIR Import",
                    timestamp=datetime.now(),
                    content_excerpt=adj_text,
                    location=Location(section=f"item[{idx}].adjudication"),
                    extraction_confidence=1.0
                ))
    
    # Extract total amounts
    totals = eob.get('total', [])
    for total in totals:
        category = total.get('category', {}).get('coding', [{}])[0].get('code', 'total')
        amount = total.get('amount', {})
        value = amount.get('value', 0)
        currency = amount.get('currency', 'USD')
        
        total_text = f"Total ({category}): {currency} {value}"
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid.uuid4()}",
            evidence_type=EvidenceType.CLAIM,
            source_system="EPIC",
            document_id=f"EOB-{eob_id}",
            document_name=f"ExplanationOfBenefit/{eob_id}",
            document_hash=hashlib.sha256(f"ExplanationOfBenefit/{eob_id}".encode()).hexdigest(),
            author="FHIR Import",
            timestamp=datetime.now(),
            content_excerpt=total_text,
            location=Location(section="total"),
            extraction_confidence=1.0
        ))
    
    return atoms


def convert_fhir_bundle(bundle: Dict[str, Any]) -> List[EvidenceAtom]:
    """
    Convert a FHIR Bundle into EvidenceAtoms.
    Handles bundles containing multiple resource types.
    """
    all_atoms = []
    
    entries = bundle.get('entry', [])
    for entry in entries:
        resource = entry.get('resource', {})
        resource_type = resource.get('resourceType', '')
        
        if resource_type == 'Patient':
            all_atoms.extend(fhir_patient_to_atoms(resource))
        elif resource_type == 'Condition':
            all_atoms.extend(fhir_condition_to_atoms(resource))
        elif resource_type == 'Coverage':
            all_atoms.extend(fhir_coverage_to_atoms(resource))
        elif resource_type == 'ExplanationOfBenefit':
            all_atoms.extend(fhir_eob_to_atoms(resource))
        elif resource_type == 'Procedure':
            all_atoms.extend(fhir_procedure_to_atoms(resource))
        elif resource_type == 'MedicationRequest':
            all_atoms.extend(fhir_medication_to_atoms(resource))
        elif resource_type == 'Observation':
            all_atoms.extend(fhir_observation_to_atoms(resource))
        elif resource_type == 'Encounter':
            all_atoms.extend(fhir_encounter_to_atoms(resource))
        elif resource_type == 'AllergyIntolerance':
            all_atoms.extend(fhir_allergy_to_atoms(resource))
        elif resource_type == 'Immunization':
            all_atoms.extend(fhir_immunization_to_atoms(resource))
        elif resource_type == 'DiagnosticReport':
            all_atoms.extend(fhir_diagnostic_report_to_atoms(resource))
    
    return all_atoms


def convert_fhir_bundle_with_type(bundle: Dict[str, Any], resource_type: str) -> List[EvidenceAtom]:
    """
    Convert a FHIR Bundle into EvidenceAtoms, specifying the expected resource type.
    This handles bundles where entries might not have explicit resourceType.
    """
    all_atoms = []
    
    if not bundle:
        return all_atoms
    
    entries = bundle.get('entry', [])
    for entry in entries:
        resource = entry.get('resource', entry)  # Some bundles have resource nested, some don't
        actual_type = resource.get('resourceType', resource_type)
        
        if actual_type == 'Patient':
            all_atoms.extend(fhir_patient_to_atoms(resource))
        elif actual_type == 'Condition':
            all_atoms.extend(fhir_condition_to_atoms(resource))
        elif actual_type == 'Coverage':
            all_atoms.extend(fhir_coverage_to_atoms(resource))
        elif actual_type == 'ExplanationOfBenefit':
            all_atoms.extend(fhir_eob_to_atoms(resource))
        elif actual_type == 'Procedure':
            all_atoms.extend(fhir_procedure_to_atoms(resource))
        elif actual_type == 'MedicationRequest':
            all_atoms.extend(fhir_medication_to_atoms(resource))
        elif actual_type == 'Observation':
            all_atoms.extend(fhir_observation_to_atoms(resource))
        elif actual_type == 'Encounter':
            all_atoms.extend(fhir_encounter_to_atoms(resource))
        elif actual_type == 'AllergyIntolerance':
            all_atoms.extend(fhir_allergy_to_atoms(resource))
        elif actual_type == 'Immunization':
            all_atoms.extend(fhir_immunization_to_atoms(resource))
        elif actual_type == 'DiagnosticReport':
            all_atoms.extend(fhir_diagnostic_report_to_atoms(resource))
    
    return all_atoms


def ingest_fhir_data(fhir_data: Dict[str, Any]) -> List[str]:
    """
    Main entry point for FHIR data ingestion.
    
    Accepts either:
    - A single FHIR resource
    - A FHIR Bundle
    - A dictionary with patient, coverage, conditions, etc. (from Epic FHIR Bridge)
    
    Returns list of created EvidenceAtom IDs.
    """
    all_atoms = []
    
    resource_type = fhir_data.get('resourceType', '')
    
    if resource_type == 'Bundle':
        all_atoms = convert_fhir_bundle(fhir_data)
    elif resource_type == 'Patient':
        all_atoms = fhir_patient_to_atoms(fhir_data)
    elif resource_type == 'Condition':
        all_atoms = fhir_condition_to_atoms(fhir_data)
    elif resource_type == 'Coverage':
        all_atoms = fhir_coverage_to_atoms(fhir_data)
    elif resource_type == 'ExplanationOfBenefit':
        all_atoms = fhir_eob_to_atoms(fhir_data)
    elif resource_type == 'Procedure':
        all_atoms = fhir_procedure_to_atoms(fhir_data)
    elif resource_type == 'MedicationRequest':
        all_atoms = fhir_medication_to_atoms(fhir_data)
    elif resource_type == 'Observation':
        all_atoms = fhir_observation_to_atoms(fhir_data)
    elif resource_type == 'Encounter':
        all_atoms = fhir_encounter_to_atoms(fhir_data)
    elif resource_type == 'AllergyIntolerance':
        all_atoms = fhir_allergy_to_atoms(fhir_data)
    elif resource_type == 'Immunization':
        all_atoms = fhir_immunization_to_atoms(fhir_data)
    elif resource_type == 'DiagnosticReport':
        all_atoms = fhir_diagnostic_report_to_atoms(fhir_data)
    else:
        # Handle composite response from our Epic FHIR Bridge (/fhir/all endpoint)
        # Keys match what the Epic Bridge returns: patient, conditions, procedures, etc.
        
        if 'patient' in fhir_data and fhir_data['patient']:
            patient = fhir_data['patient']
            if isinstance(patient, dict):
                all_atoms.extend(fhir_patient_to_atoms(patient))
        
        if 'conditions' in fhir_data and fhir_data['conditions']:
            bundle = fhir_data['conditions']
            if isinstance(bundle, dict):
                all_atoms.extend(convert_fhir_bundle_with_type(bundle, 'Condition'))
        
        if 'procedures' in fhir_data and fhir_data['procedures']:
            bundle = fhir_data['procedures']
            if isinstance(bundle, dict):
                all_atoms.extend(convert_fhir_bundle_with_type(bundle, 'Procedure'))
        
        if 'medications' in fhir_data and fhir_data['medications']:
            bundle = fhir_data['medications']
            if isinstance(bundle, dict):
                all_atoms.extend(convert_fhir_bundle_with_type(bundle, 'MedicationRequest'))
        
        if 'observations' in fhir_data and fhir_data['observations']:
            bundle = fhir_data['observations']
            if isinstance(bundle, dict):
                all_atoms.extend(convert_fhir_bundle_with_type(bundle, 'Observation'))
        
        if 'encounters' in fhir_data and fhir_data['encounters']:
            bundle = fhir_data['encounters']
            if isinstance(bundle, dict):
                all_atoms.extend(convert_fhir_bundle_with_type(bundle, 'Encounter'))
        
        if 'allergies' in fhir_data and fhir_data['allergies']:
            bundle = fhir_data['allergies']
            if isinstance(bundle, dict):
                all_atoms.extend(convert_fhir_bundle_with_type(bundle, 'AllergyIntolerance'))
        
        if 'immunizations' in fhir_data and fhir_data['immunizations']:
            bundle = fhir_data['immunizations']
            if isinstance(bundle, dict):
                all_atoms.extend(convert_fhir_bundle_with_type(bundle, 'Immunization'))
        
        if 'diagnosticReports' in fhir_data and fhir_data['diagnosticReports']:
            bundle = fhir_data['diagnosticReports']
            if isinstance(bundle, dict):
                all_atoms.extend(convert_fhir_bundle_with_type(bundle, 'DiagnosticReport'))
        
        if 'coverages' in fhir_data and fhir_data['coverages']:
            bundle = fhir_data['coverages']
            if isinstance(bundle, dict):
                all_atoms.extend(convert_fhir_bundle_with_type(bundle, 'Coverage'))
        
        # Also handle 'explanationOfBenefits' if present
        if 'explanationOfBenefits' in fhir_data and fhir_data['explanationOfBenefits']:
            bundle = fhir_data['explanationOfBenefits']
            if isinstance(bundle, dict):
                all_atoms.extend(convert_fhir_bundle_with_type(bundle, 'ExplanationOfBenefit'))
    
    # Store all atoms and collect IDs
    atom_ids = []
    for atom in all_atoms:
        try:
            store_evidence_atom(atom)
            atom_ids.append(atom.evidence_id)
        except Exception as e:
            print(f"Warning: Failed to store atom: {e}")
    
    print(f"DEBUG: Created {len(atom_ids)} evidence atoms from FHIR data")
    return atom_ids

