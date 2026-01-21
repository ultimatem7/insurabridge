"""
Demo Data Module

Provides synthetic patient data for testing and demonstration purposes.
"""

from .synthetic_patients import (
    get_all_demo_patients,
    get_demo_patient_data,
    DEMO_PATIENTS,
    create_cardiac_surgery_patient,
    create_orthopedic_surgery_patient,
    create_oncology_patient,
)

__all__ = [
    "get_all_demo_patients",
    "get_demo_patient_data",
    "DEMO_PATIENTS",
    "create_cardiac_surgery_patient",
    "create_orthopedic_surgery_patient",
    "create_oncology_patient",
]

