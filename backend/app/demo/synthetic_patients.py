"""
Synthetic Patient Data Generator

Creates comprehensive demo patients with realistic clinical data for testing.
These patients have 60+ evidence atoms each for testing complex claim scenarios.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
import uuid
import random

def generate_patient_id() -> str:
    return f"demo-{uuid.uuid4().hex[:8]}"

def generate_encounter_id() -> str:
    return f"enc-{uuid.uuid4().hex[:8]}"

def generate_condition_id() -> str:
    return f"cond-{uuid.uuid4().hex[:8]}"

def generate_procedure_id() -> str:
    return f"proc-{uuid.uuid4().hex[:8]}"

def generate_observation_id() -> str:
    return f"obs-{uuid.uuid4().hex[:8]}"

def generate_medication_id() -> str:
    return f"med-{uuid.uuid4().hex[:8]}"


# =============================================================================
# CARDIAC SURGERY PATIENT - Coronary Artery Bypass Grafting (CABG)
# =============================================================================

def create_cardiac_surgery_patient() -> Dict[str, Any]:
    """
    Creates a patient who underwent CABG surgery.
    Includes extensive cardiac conditions, procedures, labs, and medications.
    Target: 80+ evidence atoms
    """
    patient_id = "demo-cardiac-001"
    base_date = datetime.now() - timedelta(days=30)
    
    patient = {
        "resourceType": "Patient",
        "id": patient_id,
        "name": [{"use": "official", "family": "Harrison", "given": ["Robert", "James"], "text": "Robert James Harrison"}],
        "gender": "male",
        "birthDate": "1958-03-15",
        "address": [{"use": "home", "text": "456 Oak Street, Chicago, IL 60601", "city": "Chicago", "state": "IL", "postalCode": "60601"}],
        "telecom": [{"system": "phone", "value": "(312) 555-0198"}],
        "maritalStatus": {"coding": [{"code": "M", "display": "Married"}]},
    }
    
    # Extensive cardiac conditions
    conditions = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            # Primary cardiac conditions
            create_condition(patient_id, "I25.10", "Atherosclerotic heart disease of native coronary artery without angina pectoris", "active", base_date - timedelta(days=180)),
            create_condition(patient_id, "I25.110", "Atherosclerotic heart disease of native coronary artery with unstable angina pectoris", "active", base_date - timedelta(days=45)),
            create_condition(patient_id, "I25.111", "Atherosclerotic heart disease of native coronary artery with angina pectoris with documented spasm", "active", base_date - timedelta(days=45)),
            create_condition(patient_id, "I25.5", "Ischemic cardiomyopathy", "active", base_date - timedelta(days=90)),
            create_condition(patient_id, "I50.9", "Heart failure, unspecified", "active", base_date - timedelta(days=60)),
            create_condition(patient_id, "I50.32", "Chronic diastolic (congestive) heart failure", "active", base_date - timedelta(days=60)),
            # Comorbidities
            create_condition(patient_id, "I10", "Essential (primary) hypertension", "active", base_date - timedelta(days=3650)),
            create_condition(patient_id, "E11.9", "Type 2 diabetes mellitus without complications", "active", base_date - timedelta(days=2190)),
            create_condition(patient_id, "E11.65", "Type 2 diabetes mellitus with hyperglycemia", "active", base_date - timedelta(days=90)),
            create_condition(patient_id, "E78.5", "Hyperlipidemia, unspecified", "active", base_date - timedelta(days=1825)),
            create_condition(patient_id, "E78.00", "Pure hypercholesterolemia, unspecified", "active", base_date - timedelta(days=1825)),
            create_condition(patient_id, "J44.9", "Chronic obstructive pulmonary disease, unspecified", "active", base_date - timedelta(days=730)),
            create_condition(patient_id, "N18.3", "Chronic kidney disease, stage 3 (moderate)", "active", base_date - timedelta(days=365)),
            create_condition(patient_id, "I48.91", "Unspecified atrial fibrillation", "active", base_date - timedelta(days=30)),
            create_condition(patient_id, "G47.33", "Obstructive sleep apnea", "active", base_date - timedelta(days=1095)),
            create_condition(patient_id, "E66.01", "Morbid (severe) obesity due to excess calories", "active", base_date - timedelta(days=1825)),
        ]
    }
    
    # CABG and related procedures
    procedures = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            # Main CABG procedure
            create_procedure(patient_id, "33533", "Coronary artery bypass, using arterial graft(s); single arterial graft", "completed", base_date, "CPT"),
            create_procedure(patient_id, "33518", "Coronary artery bypass, using venous graft(s) and arterial graft(s); 2 venous grafts", "completed", base_date, "CPT"),
            create_procedure(patient_id, "33519", "Coronary artery bypass, using venous graft(s) and arterial graft(s); 3 venous grafts", "completed", base_date, "CPT"),
            # Pre-operative procedures
            create_procedure(patient_id, "93458", "Catheter placement in coronary artery(s) for coronary angiography", "completed", base_date - timedelta(days=14), "CPT"),
            create_procedure(patient_id, "93459", "Catheter placement for coronary angiography and left heart catheterization", "completed", base_date - timedelta(days=14), "CPT"),
            create_procedure(patient_id, "93454", "Catheter placement in coronary artery(s) for coronary angiography, imaging", "completed", base_date - timedelta(days=14), "CPT"),
            # Intra-operative
            create_procedure(patient_id, "33020", "Pericardiotomy for removal of clot or foreign body", "completed", base_date, "CPT"),
            create_procedure(patient_id, "35500", "Harvest of upper extremity artery for coronary artery bypass", "completed", base_date, "CPT"),
            create_procedure(patient_id, "35600", "Harvest of upper extremity vein, one segment, for lower extremity bypass", "completed", base_date, "CPT"),
            # Anesthesia
            create_procedure(patient_id, "00562", "Anesthesia for procedures on heart, pericardial sac, and great vessels", "completed", base_date, "CPT"),
            # Post-operative
            create_procedure(patient_id, "93000", "Electrocardiogram, routine ECG with at least 12 leads", "completed", base_date + timedelta(days=1), "CPT"),
            create_procedure(patient_id, "93306", "Echocardiography, transthoracic, real-time with image documentation", "completed", base_date + timedelta(days=2), "CPT"),
            create_procedure(patient_id, "71046", "Radiologic examination, chest; 2 views", "completed", base_date + timedelta(days=1), "CPT"),
            create_procedure(patient_id, "94760", "Noninvasive ear or pulse oximetry for oxygen saturation", "completed", base_date, "CPT"),
            create_procedure(patient_id, "36556", "Insertion of non-tunneled centrally inserted central venous catheter", "completed", base_date, "CPT"),
            create_procedure(patient_id, "36620", "Arterial catheterization for blood sampling or for use of a monitoring device", "completed", base_date, "CPT"),
        ]
    }
    
    # Extensive lab results and vital signs
    observations = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            # Pre-operative labs
            create_observation(patient_id, "2093-3", "Total cholesterol", "256", "mg/dL", base_date - timedelta(days=14), "laboratory"),
            create_observation(patient_id, "2085-9", "HDL cholesterol", "32", "mg/dL", base_date - timedelta(days=14), "laboratory"),
            create_observation(patient_id, "2089-1", "LDL cholesterol", "178", "mg/dL", base_date - timedelta(days=14), "laboratory"),
            create_observation(patient_id, "2571-8", "Triglycerides", "230", "mg/dL", base_date - timedelta(days=14), "laboratory"),
            create_observation(patient_id, "4548-4", "Hemoglobin A1c", "8.2", "%", base_date - timedelta(days=14), "laboratory"),
            create_observation(patient_id, "2339-0", "Glucose", "186", "mg/dL", base_date - timedelta(days=14), "laboratory"),
            create_observation(patient_id, "2160-0", "Creatinine", "1.8", "mg/dL", base_date - timedelta(days=14), "laboratory"),
            create_observation(patient_id, "3094-0", "BUN", "32", "mg/dL", base_date - timedelta(days=14), "laboratory"),
            create_observation(patient_id, "33914-3", "eGFR", "42", "mL/min/1.73m2", base_date - timedelta(days=14), "laboratory"),
            create_observation(patient_id, "718-7", "Hemoglobin", "11.8", "g/dL", base_date - timedelta(days=14), "laboratory"),
            create_observation(patient_id, "4544-3", "Hematocrit", "35.4", "%", base_date - timedelta(days=14), "laboratory"),
            create_observation(patient_id, "777-3", "Platelets", "198", "10*3/uL", base_date - timedelta(days=14), "laboratory"),
            create_observation(patient_id, "6690-2", "WBC", "8.2", "10*3/uL", base_date - timedelta(days=14), "laboratory"),
            create_observation(patient_id, "5902-2", "PT", "12.8", "sec", base_date - timedelta(days=14), "laboratory"),
            create_observation(patient_id, "6301-6", "INR", "1.1", "ratio", base_date - timedelta(days=14), "laboratory"),
            create_observation(patient_id, "3173-2", "PTT", "32", "sec", base_date - timedelta(days=14), "laboratory"),
            # Cardiac biomarkers
            create_observation(patient_id, "10839-9", "Troponin I", "0.04", "ng/mL", base_date - timedelta(days=14), "laboratory"),
            create_observation(patient_id, "33762-6", "NT-proBNP", "2450", "pg/mL", base_date - timedelta(days=14), "laboratory"),
            create_observation(patient_id, "30522-7", "CRP", "4.2", "mg/L", base_date - timedelta(days=14), "laboratory"),
            # Post-operative labs
            create_observation(patient_id, "10839-9", "Troponin I", "12.8", "ng/mL", base_date + timedelta(days=1), "laboratory"),
            create_observation(patient_id, "718-7", "Hemoglobin", "9.2", "g/dL", base_date + timedelta(days=1), "laboratory"),
            create_observation(patient_id, "2160-0", "Creatinine", "2.1", "mg/dL", base_date + timedelta(days=1), "laboratory"),
            # Vital signs
            create_observation(patient_id, "8480-6", "Systolic blood pressure", "162", "mmHg", base_date - timedelta(days=14), "vital-signs"),
            create_observation(patient_id, "8462-4", "Diastolic blood pressure", "94", "mmHg", base_date - timedelta(days=14), "vital-signs"),
            create_observation(patient_id, "8867-4", "Heart rate", "88", "beats/min", base_date - timedelta(days=14), "vital-signs"),
            create_observation(patient_id, "9279-1", "Respiratory rate", "18", "breaths/min", base_date - timedelta(days=14), "vital-signs"),
            create_observation(patient_id, "8310-5", "Body temperature", "98.6", "°F", base_date - timedelta(days=14), "vital-signs"),
            create_observation(patient_id, "2710-2", "Oxygen saturation", "94", "%", base_date - timedelta(days=14), "vital-signs"),
            create_observation(patient_id, "29463-7", "Body weight", "242", "lbs", base_date - timedelta(days=14), "vital-signs"),
            create_observation(patient_id, "8302-2", "Body height", "70", "in", base_date - timedelta(days=14), "vital-signs"),
            create_observation(patient_id, "39156-5", "BMI", "34.7", "kg/m2", base_date - timedelta(days=14), "vital-signs"),
            # Post-op vitals
            create_observation(patient_id, "8480-6", "Systolic blood pressure", "118", "mmHg", base_date + timedelta(days=1), "vital-signs"),
            create_observation(patient_id, "8462-4", "Diastolic blood pressure", "72", "mmHg", base_date + timedelta(days=1), "vital-signs"),
            create_observation(patient_id, "8867-4", "Heart rate", "76", "beats/min", base_date + timedelta(days=1), "vital-signs"),
        ]
    }
    
    # Cardiac medications
    medications = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            create_medication(patient_id, "316049", "Metoprolol Succinate 50mg", "active", "Take 1 tablet by mouth once daily"),
            create_medication(patient_id, "197884", "Lisinopril 20mg", "active", "Take 1 tablet by mouth once daily"),
            create_medication(patient_id, "310798", "Atorvastatin 80mg", "active", "Take 1 tablet by mouth at bedtime"),
            create_medication(patient_id, "855288", "Aspirin 81mg", "active", "Take 1 tablet by mouth once daily"),
            create_medication(patient_id, "855318", "Clopidogrel 75mg", "active", "Take 1 tablet by mouth once daily"),
            create_medication(patient_id, "311671", "Metformin 1000mg", "active", "Take 1 tablet by mouth twice daily with meals"),
            create_medication(patient_id, "860975", "Furosemide 40mg", "active", "Take 1 tablet by mouth twice daily"),
            create_medication(patient_id, "197770", "Spironolactone 25mg", "active", "Take 1 tablet by mouth once daily"),
            create_medication(patient_id, "313002", "Warfarin 5mg", "active", "Take as directed based on INR"),
            create_medication(patient_id, "892477", "Carvedilol 12.5mg", "active", "Take 1 tablet by mouth twice daily"),
            create_medication(patient_id, "647235", "Amlodipine 10mg", "active", "Take 1 tablet by mouth once daily"),
            create_medication(patient_id, "854228", "Nitroglycerin 0.4mg SL", "active", "Place 1 tablet under tongue as needed for chest pain"),
            create_medication(patient_id, "197381", "Potassium Chloride 20mEq", "active", "Take 1 tablet by mouth daily"),
            create_medication(patient_id, "310429", "Insulin Glargine 100 units/mL", "active", "Inject 30 units subcutaneously at bedtime"),
            create_medication(patient_id, "860601", "Pantoprazole 40mg", "active", "Take 1 tablet by mouth once daily"),
        ]
    }
    
    # Hospital encounters
    encounters = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            create_encounter(patient_id, "IMP", "Inpatient encounter", base_date - timedelta(days=1), base_date + timedelta(days=7), "Cardiac surgery admission for CABG"),
            create_encounter(patient_id, "AMB", "Ambulatory", base_date - timedelta(days=14), base_date - timedelta(days=14), "Pre-operative cardiac catheterization"),
            create_encounter(patient_id, "AMB", "Ambulatory", base_date - timedelta(days=45), base_date - timedelta(days=45), "Cardiology consultation for unstable angina"),
        ]
    }
    
    # Allergies
    allergies = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            create_allergy(patient_id, "7980", "Penicillin", "active", "Anaphylaxis"),
            create_allergy(patient_id, "2670", "Codeine", "active", "Nausea and vomiting"),
            create_allergy(patient_id, "70618", "Shellfish", "active", "Hives"),
        ]
    }
    
    # Immunizations
    immunizations = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            create_immunization(patient_id, "141", "Influenza vaccine", base_date - timedelta(days=120)),
            create_immunization(patient_id, "33", "Pneumococcal vaccine", base_date - timedelta(days=365)),
            create_immunization(patient_id, "207", "COVID-19 vaccine", base_date - timedelta(days=180)),
        ]
    }
    
    return {
        "patient": patient,
        "conditions": conditions,
        "procedures": procedures,
        "medications": medications,
        "observations": observations,
        "encounters": encounters,
        "allergies": allergies,
        "immunizations": immunizations,
    }


# =============================================================================
# ORTHOPEDIC SURGERY PATIENT - Total Hip Replacement
# =============================================================================

def create_orthopedic_surgery_patient() -> Dict[str, Any]:
    """
    Creates a patient who underwent total hip replacement.
    Includes orthopedic conditions, procedures, and post-op care.
    Target: 70+ evidence atoms
    """
    patient_id = "demo-ortho-001"
    base_date = datetime.now() - timedelta(days=21)
    
    patient = {
        "resourceType": "Patient",
        "id": patient_id,
        "name": [{"use": "official", "family": "Martinez", "given": ["Elena", "Sofia"], "text": "Elena Sofia Martinez"}],
        "gender": "female",
        "birthDate": "1952-08-22",
        "address": [{"use": "home", "text": "789 Pine Avenue, Phoenix, AZ 85001", "city": "Phoenix", "state": "AZ", "postalCode": "85001"}],
    }
    
    conditions = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            # Primary orthopedic conditions
            create_condition(patient_id, "M16.11", "Primary osteoarthritis, right hip", "active", base_date - timedelta(days=730)),
            create_condition(patient_id, "M16.12", "Primary osteoarthritis, left hip", "active", base_date - timedelta(days=730)),
            create_condition(patient_id, "M25.551", "Pain in right hip", "active", base_date - timedelta(days=365)),
            create_condition(patient_id, "M25.552", "Pain in left hip", "active", base_date - timedelta(days=365)),
            create_condition(patient_id, "M79.3", "Panniculitis, unspecified", "active", base_date - timedelta(days=180)),
            create_condition(patient_id, "M62.81", "Muscle weakness (generalized)", "active", base_date - timedelta(days=365)),
            create_condition(patient_id, "R26.2", "Difficulty in walking, not elsewhere classified", "active", base_date - timedelta(days=365)),
            # Comorbidities
            create_condition(patient_id, "I10", "Essential (primary) hypertension", "active", base_date - timedelta(days=2555)),
            create_condition(patient_id, "E78.5", "Hyperlipidemia, unspecified", "active", base_date - timedelta(days=1825)),
            create_condition(patient_id, "M81.0", "Age-related osteoporosis without current pathological fracture", "active", base_date - timedelta(days=1095)),
            create_condition(patient_id, "E55.9", "Vitamin D deficiency, unspecified", "active", base_date - timedelta(days=730)),
            create_condition(patient_id, "F32.9", "Major depressive disorder, single episode, unspecified", "active", base_date - timedelta(days=365)),
            create_condition(patient_id, "G89.29", "Other chronic pain", "active", base_date - timedelta(days=365)),
        ]
    }
    
    procedures = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            # Hip replacement procedures
            create_procedure(patient_id, "27130", "Arthroplasty, acetabular and proximal femoral prosthetic replacement (total hip arthroplasty)", "completed", base_date, "CPT"),
            create_procedure(patient_id, "27132", "Conversion of previous hip surgery to total hip arthroplasty", "completed", base_date, "CPT"),
            # Pre-operative
            create_procedure(patient_id, "73521", "Radiologic examination, hips, bilateral, minimum of 2 views", "completed", base_date - timedelta(days=30), "CPT"),
            create_procedure(patient_id, "73502", "Radiologic examination, hip, unilateral, minimum of 2 views", "completed", base_date - timedelta(days=30), "CPT"),
            create_procedure(patient_id, "73721", "MRI, any joint of lower extremity", "completed", base_date - timedelta(days=45), "CPT"),
            # Anesthesia and intra-operative
            create_procedure(patient_id, "01214", "Anesthesia for open procedures involving hip joint", "completed", base_date, "CPT"),
            create_procedure(patient_id, "62322", "Injection, including indwelling catheter placement, continuous infusion or intermittent bolus", "completed", base_date, "CPT"),
            # Post-operative
            create_procedure(patient_id, "97110", "Therapeutic exercises", "completed", base_date + timedelta(days=1), "CPT"),
            create_procedure(patient_id, "97140", "Manual therapy techniques", "completed", base_date + timedelta(days=1), "CPT"),
            create_procedure(patient_id, "97116", "Gait training", "completed", base_date + timedelta(days=2), "CPT"),
            create_procedure(patient_id, "97530", "Therapeutic activities", "completed", base_date + timedelta(days=3), "CPT"),
            create_procedure(patient_id, "71046", "Radiologic examination, chest; 2 views", "completed", base_date, "CPT"),
            create_procedure(patient_id, "93000", "Electrocardiogram, routine ECG", "completed", base_date - timedelta(days=7), "CPT"),
        ]
    }
    
    observations = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            # Pre-operative labs
            create_observation(patient_id, "718-7", "Hemoglobin", "12.8", "g/dL", base_date - timedelta(days=7), "laboratory"),
            create_observation(patient_id, "4544-3", "Hematocrit", "38.4", "%", base_date - timedelta(days=7), "laboratory"),
            create_observation(patient_id, "777-3", "Platelets", "245", "10*3/uL", base_date - timedelta(days=7), "laboratory"),
            create_observation(patient_id, "2160-0", "Creatinine", "0.9", "mg/dL", base_date - timedelta(days=7), "laboratory"),
            create_observation(patient_id, "5902-2", "PT", "11.5", "sec", base_date - timedelta(days=7), "laboratory"),
            create_observation(patient_id, "6301-6", "INR", "1.0", "ratio", base_date - timedelta(days=7), "laboratory"),
            create_observation(patient_id, "2093-3", "Total cholesterol", "218", "mg/dL", base_date - timedelta(days=30), "laboratory"),
            create_observation(patient_id, "1742-6", "ALT", "24", "U/L", base_date - timedelta(days=7), "laboratory"),
            create_observation(patient_id, "1920-8", "AST", "22", "U/L", base_date - timedelta(days=7), "laboratory"),
            # Post-op labs
            create_observation(patient_id, "718-7", "Hemoglobin", "10.2", "g/dL", base_date + timedelta(days=1), "laboratory"),
            create_observation(patient_id, "2160-0", "Creatinine", "1.1", "mg/dL", base_date + timedelta(days=1), "laboratory"),
            # Vitamin D panel
            create_observation(patient_id, "1989-3", "Vitamin D", "18", "ng/mL", base_date - timedelta(days=30), "laboratory"),
            # Bone markers
            create_observation(patient_id, "17861-6", "Calcium", "9.2", "mg/dL", base_date - timedelta(days=30), "laboratory"),
            create_observation(patient_id, "2777-1", "Phosphorus", "3.8", "mg/dL", base_date - timedelta(days=30), "laboratory"),
            # Vital signs
            create_observation(patient_id, "8480-6", "Systolic blood pressure", "138", "mmHg", base_date - timedelta(days=7), "vital-signs"),
            create_observation(patient_id, "8462-4", "Diastolic blood pressure", "82", "mmHg", base_date - timedelta(days=7), "vital-signs"),
            create_observation(patient_id, "8867-4", "Heart rate", "72", "beats/min", base_date - timedelta(days=7), "vital-signs"),
            create_observation(patient_id, "29463-7", "Body weight", "168", "lbs", base_date - timedelta(days=7), "vital-signs"),
            create_observation(patient_id, "8302-2", "Body height", "64", "in", base_date - timedelta(days=7), "vital-signs"),
            create_observation(patient_id, "39156-5", "BMI", "28.8", "kg/m2", base_date - timedelta(days=7), "vital-signs"),
            # Pain assessment
            create_observation(patient_id, "72514-3", "Pain severity - 0-10 verbal numeric rating", "8", "score", base_date - timedelta(days=30), "vital-signs"),
            create_observation(patient_id, "72514-3", "Pain severity - 0-10 verbal numeric rating", "3", "score", base_date + timedelta(days=3), "vital-signs"),
        ]
    }
    
    medications = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            create_medication(patient_id, "1049635", "Enoxaparin 40mg", "active", "Inject subcutaneously once daily for DVT prophylaxis"),
            create_medication(patient_id, "857005", "Oxycodone 5mg", "active", "Take 1-2 tablets by mouth every 4-6 hours as needed for pain"),
            create_medication(patient_id, "198240", "Acetaminophen 650mg", "active", "Take 2 tablets by mouth every 6 hours"),
            create_medication(patient_id, "197884", "Lisinopril 10mg", "active", "Take 1 tablet by mouth once daily"),
            create_medication(patient_id, "310798", "Atorvastatin 40mg", "active", "Take 1 tablet by mouth at bedtime"),
            create_medication(patient_id, "854228", "Calcium 600mg + Vitamin D 400IU", "active", "Take 1 tablet by mouth twice daily"),
            create_medication(patient_id, "310429", "Alendronate 70mg", "active", "Take 1 tablet by mouth once weekly on empty stomach"),
            create_medication(patient_id, "860601", "Pantoprazole 40mg", "active", "Take 1 tablet by mouth once daily"),
            create_medication(patient_id, "311671", "Sertraline 50mg", "active", "Take 1 tablet by mouth once daily"),
            create_medication(patient_id, "197381", "Docusate Sodium 100mg", "active", "Take 1 capsule by mouth twice daily"),
        ]
    }
    
    encounters = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            create_encounter(patient_id, "IMP", "Inpatient encounter", base_date, base_date + timedelta(days=4), "Total hip arthroplasty admission"),
            create_encounter(patient_id, "AMB", "Ambulatory", base_date - timedelta(days=30), base_date - timedelta(days=30), "Pre-operative orthopedic consultation"),
            create_encounter(patient_id, "AMB", "Ambulatory", base_date - timedelta(days=7), base_date - timedelta(days=7), "Pre-operative clearance"),
        ]
    }
    
    allergies = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            create_allergy(patient_id, "1191", "Aspirin", "active", "GI bleeding"),
            create_allergy(patient_id, "723", "NSAIDs", "active", "Gastric ulcer"),
        ]
    }
    
    immunizations = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            create_immunization(patient_id, "140", "Influenza vaccine", base_date - timedelta(days=90)),
            create_immunization(patient_id, "33", "Pneumococcal vaccine", base_date - timedelta(days=730)),
            create_immunization(patient_id, "113", "Tdap vaccine", base_date - timedelta(days=1825)),
        ]
    }
    
    return {
        "patient": patient,
        "conditions": conditions,
        "procedures": procedures,
        "medications": medications,
        "observations": observations,
        "encounters": encounters,
        "allergies": allergies,
        "immunizations": immunizations,
    }


# =============================================================================
# ONCOLOGY PATIENT - Cancer Treatment
# =============================================================================

def create_oncology_patient() -> Dict[str, Any]:
    """
    Creates a patient undergoing cancer treatment.
    Includes multiple cancer-related conditions, chemotherapy, and supportive care.
    Target: 75+ evidence atoms
    """
    patient_id = "demo-onc-001"
    base_date = datetime.now() - timedelta(days=14)
    
    patient = {
        "resourceType": "Patient",
        "id": patient_id,
        "name": [{"use": "official", "family": "Chen", "given": ["William", "Ming"], "text": "William Ming Chen"}],
        "gender": "male",
        "birthDate": "1965-11-08",
        "address": [{"use": "home", "text": "123 Maple Drive, Seattle, WA 98101", "city": "Seattle", "state": "WA", "postalCode": "98101"}],
    }
    
    conditions = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            # Primary cancer diagnosis
            create_condition(patient_id, "C34.11", "Malignant neoplasm of upper lobe, right bronchus or lung", "active", base_date - timedelta(days=180)),
            create_condition(patient_id, "C34.12", "Malignant neoplasm of upper lobe, left bronchus or lung", "active", base_date - timedelta(days=180)),
            create_condition(patient_id, "C78.00", "Secondary malignant neoplasm of unspecified lung", "active", base_date - timedelta(days=90)),
            create_condition(patient_id, "C77.1", "Secondary and unspecified malignant neoplasm of intrathoracic lymph nodes", "active", base_date - timedelta(days=120)),
            # Cancer-related conditions
            create_condition(patient_id, "R91.8", "Other nonspecific abnormal finding of lung field", "active", base_date - timedelta(days=210)),
            create_condition(patient_id, "J98.11", "Atelectasis", "active", base_date - timedelta(days=60)),
            create_condition(patient_id, "R05.9", "Cough, unspecified", "active", base_date - timedelta(days=180)),
            create_condition(patient_id, "R06.00", "Dyspnea, unspecified", "active", base_date - timedelta(days=120)),
            create_condition(patient_id, "R63.4", "Abnormal weight loss", "active", base_date - timedelta(days=90)),
            # Treatment side effects
            create_condition(patient_id, "D64.81", "Anemia due to antineoplastic chemotherapy", "active", base_date - timedelta(days=30)),
            create_condition(patient_id, "D70.1", "Drug-induced agranulocytosis and neutropenia", "active", base_date - timedelta(days=21)),
            create_condition(patient_id, "R11.0", "Nausea", "active", base_date - timedelta(days=21)),
            create_condition(patient_id, "R11.10", "Vomiting, unspecified", "active", base_date - timedelta(days=21)),
            create_condition(patient_id, "K52.1", "Toxic gastroenteritis and colitis", "active", base_date - timedelta(days=14)),
            create_condition(patient_id, "L65.9", "Nonscarring hair loss, unspecified", "active", base_date - timedelta(days=45)),
            # Comorbidities
            create_condition(patient_id, "I10", "Essential (primary) hypertension", "active", base_date - timedelta(days=1825)),
            create_condition(patient_id, "F32.A", "Depression, unspecified", "active", base_date - timedelta(days=90)),
            create_condition(patient_id, "G47.00", "Insomnia, unspecified", "active", base_date - timedelta(days=90)),
        ]
    }
    
    procedures = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            # Diagnostic procedures
            create_procedure(patient_id, "31628", "Bronchoscopy with transbronchial lung biopsy", "completed", base_date - timedelta(days=175), "CPT"),
            create_procedure(patient_id, "88305", "Surgical pathology, gross and microscopic examination", "completed", base_date - timedelta(days=170), "CPT"),
            create_procedure(patient_id, "78815", "PET imaging, skull base to mid-thigh", "completed", base_date - timedelta(days=165), "CPT"),
            create_procedure(patient_id, "71260", "CT thorax with contrast", "completed", base_date - timedelta(days=180), "CPT"),
            create_procedure(patient_id, "70553", "MRI brain with and without contrast", "completed", base_date - timedelta(days=160), "CPT"),
            # Chemotherapy administration
            create_procedure(patient_id, "96413", "Chemotherapy administration, IV infusion, first hour", "completed", base_date - timedelta(days=90), "CPT"),
            create_procedure(patient_id, "96415", "Chemotherapy administration, IV infusion, each additional hour", "completed", base_date - timedelta(days=90), "CPT"),
            create_procedure(patient_id, "96417", "Chemotherapy administration, IV push", "completed", base_date - timedelta(days=60), "CPT"),
            create_procedure(patient_id, "96413", "Chemotherapy administration, IV infusion, first hour", "completed", base_date - timedelta(days=30), "CPT"),
            create_procedure(patient_id, "96413", "Chemotherapy administration, IV infusion, first hour", "completed", base_date, "CPT"),
            # Supportive procedures
            create_procedure(patient_id, "36561", "Insertion of central venous access device with subcutaneous port", "completed", base_date - timedelta(days=100), "CPT"),
            create_procedure(patient_id, "96372", "Therapeutic injection", "completed", base_date - timedelta(days=21), "CPT"),
            create_procedure(patient_id, "90715", "Hydration therapy", "completed", base_date - timedelta(days=14), "CPT"),
            # Follow-up imaging
            create_procedure(patient_id, "71260", "CT thorax with contrast", "completed", base_date - timedelta(days=45), "CPT"),
            create_procedure(patient_id, "71260", "CT thorax with contrast", "completed", base_date, "CPT"),
        ]
    }
    
    observations = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            # Tumor markers
            create_observation(patient_id, "19994-3", "CEA", "12.8", "ng/mL", base_date - timedelta(days=90), "laboratory"),
            create_observation(patient_id, "19994-3", "CEA", "8.4", "ng/mL", base_date - timedelta(days=45), "laboratory"),
            create_observation(patient_id, "19994-3", "CEA", "5.2", "ng/mL", base_date, "laboratory"),
            # CBC with differential
            create_observation(patient_id, "718-7", "Hemoglobin", "10.2", "g/dL", base_date - timedelta(days=7), "laboratory"),
            create_observation(patient_id, "4544-3", "Hematocrit", "30.6", "%", base_date - timedelta(days=7), "laboratory"),
            create_observation(patient_id, "777-3", "Platelets", "145", "10*3/uL", base_date - timedelta(days=7), "laboratory"),
            create_observation(patient_id, "6690-2", "WBC", "2.8", "10*3/uL", base_date - timedelta(days=7), "laboratory"),
            create_observation(patient_id, "751-8", "Neutrophils", "1.2", "10*3/uL", base_date - timedelta(days=7), "laboratory"),
            create_observation(patient_id, "731-0", "Lymphocytes", "0.8", "10*3/uL", base_date - timedelta(days=7), "laboratory"),
            # Chemistry panel
            create_observation(patient_id, "2160-0", "Creatinine", "1.0", "mg/dL", base_date - timedelta(days=7), "laboratory"),
            create_observation(patient_id, "3094-0", "BUN", "18", "mg/dL", base_date - timedelta(days=7), "laboratory"),
            create_observation(patient_id, "1742-6", "ALT", "42", "U/L", base_date - timedelta(days=7), "laboratory"),
            create_observation(patient_id, "1920-8", "AST", "38", "U/L", base_date - timedelta(days=7), "laboratory"),
            create_observation(patient_id, "1975-2", "Total bilirubin", "0.8", "mg/dL", base_date - timedelta(days=7), "laboratory"),
            create_observation(patient_id, "6768-6", "Alkaline phosphatase", "98", "U/L", base_date - timedelta(days=7), "laboratory"),
            create_observation(patient_id, "2951-2", "Sodium", "138", "mEq/L", base_date - timedelta(days=7), "laboratory"),
            create_observation(patient_id, "2823-3", "Potassium", "4.2", "mEq/L", base_date - timedelta(days=7), "laboratory"),
            create_observation(patient_id, "17861-6", "Calcium", "8.8", "mg/dL", base_date - timedelta(days=7), "laboratory"),
            create_observation(patient_id, "2885-2", "Protein", "6.4", "g/dL", base_date - timedelta(days=7), "laboratory"),
            create_observation(patient_id, "1751-7", "Albumin", "3.2", "g/dL", base_date - timedelta(days=7), "laboratory"),
            # Vital signs
            create_observation(patient_id, "8480-6", "Systolic blood pressure", "128", "mmHg", base_date, "vital-signs"),
            create_observation(patient_id, "8462-4", "Diastolic blood pressure", "78", "mmHg", base_date, "vital-signs"),
            create_observation(patient_id, "8867-4", "Heart rate", "84", "beats/min", base_date, "vital-signs"),
            create_observation(patient_id, "9279-1", "Respiratory rate", "20", "breaths/min", base_date, "vital-signs"),
            create_observation(patient_id, "2710-2", "Oxygen saturation", "95", "%", base_date, "vital-signs"),
            create_observation(patient_id, "29463-7", "Body weight", "158", "lbs", base_date, "vital-signs"),
            create_observation(patient_id, "8302-2", "Body height", "68", "in", base_date, "vital-signs"),
            create_observation(patient_id, "39156-5", "BMI", "24.0", "kg/m2", base_date, "vital-signs"),
            # ECOG Performance status
            create_observation(patient_id, "89247-1", "ECOG Performance Status", "1", "score", base_date, "vital-signs"),
        ]
    }
    
    medications = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            # Chemotherapy drugs
            create_medication(patient_id, "1721543", "Carboplatin 450mg", "active", "IV infusion over 30-60 minutes every 3 weeks"),
            create_medication(patient_id, "1726319", "Pemetrexed 500mg/m2", "active", "IV infusion over 10 minutes every 3 weeks"),
            create_medication(patient_id, "1946840", "Pembrolizumab 200mg", "active", "IV infusion over 30 minutes every 3 weeks"),
            # Supportive medications
            create_medication(patient_id, "860175", "Ondansetron 8mg", "active", "Take 1 tablet by mouth every 8 hours as needed for nausea"),
            create_medication(patient_id, "197884", "Dexamethasone 4mg", "active", "Take as directed for chemotherapy premedication"),
            create_medication(patient_id, "1721543", "Filgrastim 480mcg", "active", "Inject subcutaneously daily for 5 days after chemotherapy"),
            create_medication(patient_id, "197884", "Prochlorperazine 10mg", "active", "Take 1 tablet by mouth every 6 hours as needed for nausea"),
            create_medication(patient_id, "197770", "Omeprazole 20mg", "active", "Take 1 capsule by mouth twice daily"),
            create_medication(patient_id, "197884", "Lorazepam 0.5mg", "active", "Take 1 tablet by mouth every 8 hours as needed for anxiety"),
            # Comorbidity medications
            create_medication(patient_id, "197884", "Lisinopril 10mg", "active", "Take 1 tablet by mouth once daily"),
            create_medication(patient_id, "311671", "Sertraline 50mg", "active", "Take 1 tablet by mouth once daily"),
            create_medication(patient_id, "860601", "Trazodone 50mg", "active", "Take 1 tablet by mouth at bedtime as needed for sleep"),
            # Supplements
            create_medication(patient_id, "854228", "Folic acid 1mg", "active", "Take 1 tablet by mouth daily"),
            create_medication(patient_id, "854228", "Vitamin B12 1000mcg", "active", "Take 1 tablet by mouth daily"),
        ]
    }
    
    encounters = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            create_encounter(patient_id, "AMB", "Ambulatory", base_date, base_date, "Chemotherapy cycle 4"),
            create_encounter(patient_id, "AMB", "Ambulatory", base_date - timedelta(days=21), base_date - timedelta(days=21), "Chemotherapy cycle 3"),
            create_encounter(patient_id, "AMB", "Ambulatory", base_date - timedelta(days=42), base_date - timedelta(days=42), "Chemotherapy cycle 2"),
            create_encounter(patient_id, "AMB", "Ambulatory", base_date - timedelta(days=63), base_date - timedelta(days=63), "Chemotherapy cycle 1"),
            create_encounter(patient_id, "AMB", "Ambulatory", base_date - timedelta(days=175), base_date - timedelta(days=175), "Bronchoscopy with biopsy"),
            create_encounter(patient_id, "AMB", "Ambulatory", base_date - timedelta(days=180), base_date - timedelta(days=180), "Initial oncology consultation"),
        ]
    }
    
    allergies = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            create_allergy(patient_id, "7980", "Sulfa drugs", "active", "Rash"),
        ]
    }
    
    immunizations = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            create_immunization(patient_id, "141", "Influenza vaccine", base_date - timedelta(days=60)),
            create_immunization(patient_id, "33", "Pneumococcal vaccine", base_date - timedelta(days=180)),
        ]
    }
    
    return {
        "patient": patient,
        "conditions": conditions,
        "procedures": procedures,
        "medications": medications,
        "observations": observations,
        "encounters": encounters,
        "allergies": allergies,
        "immunizations": immunizations,
    }


# =============================================================================
# HELPER FUNCTIONS TO CREATE FHIR RESOURCES
# =============================================================================

def create_condition(patient_id: str, code: str, display: str, status: str, onset_date: datetime) -> Dict:
    return {
        "resource": {
            "resourceType": "Condition",
            "id": generate_condition_id(),
            "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": status}]},
            "verificationStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status", "code": "confirmed"}]},
            "code": {
                "coding": [{"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": code, "display": display}],
                "text": display
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "onsetDateTime": onset_date.isoformat(),
            "recordedDate": onset_date.isoformat()
        }
    }

def create_procedure(patient_id: str, code: str, display: str, status: str, performed_date: datetime, code_type: str = "CPT") -> Dict:
    system = "http://www.ama-assn.org/go/cpt" if code_type == "CPT" else "http://www.cms.gov/Medicare/Coding/HCPCSReleaseCodeSets"
    return {
        "resource": {
            "resourceType": "Procedure",
            "id": generate_procedure_id(),
            "status": status,
            "code": {
                "coding": [{"system": system, "code": code, "display": display}],
                "text": display
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "performedDateTime": performed_date.isoformat()
        }
    }

def create_observation(patient_id: str, code: str, display: str, value: str, unit: str, effective_date: datetime, category: str) -> Dict:
    return {
        "resource": {
            "resourceType": "Observation",
            "id": generate_observation_id(),
            "status": "final",
            "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": category}]}],
            "code": {
                "coding": [{"system": "http://loinc.org", "code": code, "display": display}],
                "text": display
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "effectiveDateTime": effective_date.isoformat(),
            "valueQuantity": {"value": float(value) if value.replace('.', '').isdigit() else 0, "unit": unit}
        }
    }

def create_medication(patient_id: str, code: str, display: str, status: str, dosage: str) -> Dict:
    return {
        "resource": {
            "resourceType": "MedicationRequest",
            "id": generate_medication_id(),
            "status": status,
            "intent": "order",
            "medicationCodeableConcept": {
                "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": code, "display": display}],
                "text": display
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "dosageInstruction": [{"text": dosage}]
        }
    }

def create_encounter(patient_id: str, enc_class: str, class_display: str, start_date: datetime, end_date: datetime, reason: str) -> Dict:
    return {
        "resource": {
            "resourceType": "Encounter",
            "id": generate_encounter_id(),
            "status": "finished",
            "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": enc_class, "display": class_display},
            "type": [{"coding": [{"display": reason}], "text": reason}],
            "subject": {"reference": f"Patient/{patient_id}"},
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()}
        }
    }

def create_allergy(patient_id: str, code: str, display: str, status: str, reaction: str) -> Dict:
    return {
        "resource": {
            "resourceType": "AllergyIntolerance",
            "id": f"allergy-{uuid.uuid4().hex[:8]}",
            "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical", "code": status}]},
            "code": {
                "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": code, "display": display}],
                "text": display
            },
            "patient": {"reference": f"Patient/{patient_id}"},
            "reaction": [{"manifestation": [{"coding": [{"display": reaction}]}]}]
        }
    }

def create_immunization(patient_id: str, code: str, display: str, occurrence_date: datetime) -> Dict:
    return {
        "resource": {
            "resourceType": "Immunization",
            "id": f"imm-{uuid.uuid4().hex[:8]}",
            "status": "completed",
            "vaccineCode": {
                "coding": [{"system": "http://hl7.org/fhir/sid/cvx", "code": code, "display": display}],
                "text": display
            },
            "patient": {"reference": f"Patient/{patient_id}"},
            "occurrenceDateTime": occurrence_date.isoformat()
        }
    }


# =============================================================================
# REGISTRY OF ALL DEMO PATIENTS
# =============================================================================

DEMO_PATIENTS = {
    "demo-cardiac-001": {
        "name": "Robert James Harrison",
        "description": "Cardiac Surgery - CABG (Coronary Artery Bypass Grafting)",
        "generator": create_cardiac_surgery_patient,
        "expected_atoms": 85,
        "tags": ["cardiac", "surgery", "complex"],
    },
    "demo-ortho-001": {
        "name": "Elena Sofia Martinez",
        "description": "Orthopedic Surgery - Total Hip Replacement",
        "generator": create_orthopedic_surgery_patient,
        "expected_atoms": 70,
        "tags": ["orthopedic", "surgery"],
    },
    "demo-onc-001": {
        "name": "William Ming Chen",
        "description": "Oncology - Lung Cancer with Chemotherapy",
        "generator": create_oncology_patient,
        "expected_atoms": 75,
        "tags": ["oncology", "chemotherapy", "complex"],
    },
}

def get_all_demo_patients() -> List[Dict]:
    """Returns summary info for all available demo patients."""
    return [
        {
            "id": pid,
            "name": info["name"],
            "description": info["description"],
            "expected_atoms": info["expected_atoms"],
            "tags": info["tags"],
        }
        for pid, info in DEMO_PATIENTS.items()
    ]

def get_demo_patient_data(patient_id: str) -> Dict[str, Any]:
    """Returns the full FHIR data for a demo patient."""
    if patient_id not in DEMO_PATIENTS:
        raise ValueError(f"Unknown demo patient: {patient_id}")
    
    generator = DEMO_PATIENTS[patient_id]["generator"]
    return generator()

