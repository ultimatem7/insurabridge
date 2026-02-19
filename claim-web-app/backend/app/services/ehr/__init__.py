"""
EHR Adapter Factory
Centralized provider adapter management
"""

from typing import Dict, Type
from app.core.config import settings
from app.services.ehr.base import BaseEHRAdapter
from app.services.ehr.epic_adapter import EpicAdapter
from app.services.ehr.cerner_adapter import CernerAdapter


class MockAdapter(BaseEHRAdapter):
    """Mock adapter for testing and development."""
    
    @property
    def provider_name(self) -> str:
        return "mock"
    
    def get_authorization_url(self, state: str, scope: str | None = None, **kwargs) -> str:
        return f"http://mock-ehr.com/authorize?state={state}"
    
    async def exchange_code_for_token(self, code: str, **kwargs) -> Dict:
        return {
            "access_token": "mock_access_token",
            "refresh_token": "mock_refresh_token",
            "expires_in": 3600,
            "patient": "mock_patient_123",
        }
    
    async def refresh_access_token(self, refresh_token: str) -> Dict:
        return {"access_token": "mock_refreshed_token", "expires_in": 3600}
    
    async def fetch_patient(self, patient_id: str, access_token: str) -> Dict:
        return {
            "resourceType": "Patient",
            "id": patient_id,
            "name": [{"given": ["John"], "family": "Doe"}],
            "gender": "male",
            "birthDate": "1980-01-01",
        }
    
    async def fetch_encounters(self, patient_id: str, access_token: str, status: str | None = None, **kwargs) -> list:
        return [{
            "resourceType": "Encounter",
            "id": "encounter_1",
            "status": "finished",
            "class": {"code": "AMB"},
            "period": {"start": "2024-01-15T10:00:00Z", "end": "2024-01-15T11:00:00Z"},
        }]
    
    async def fetch_conditions(self, patient_id: str, access_token: str, **kwargs) -> list:
        return [{
            "resourceType": "Condition",
            "id": "condition_1",
            "code": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": "I10", "display": "Essential hypertension"}]},
        }]
    
    async def fetch_procedures(self, patient_id: str, access_token: str, **kwargs) -> list:
        return []
    
    async def fetch_observations(self, patient_id: str, access_token: str, category: str | None = None, **kwargs) -> list:
        return []
    
    async def fetch_document_references(self, patient_id: str, access_token: str, **kwargs) -> list:
        return []
    
    async def fetch_medication_requests(self, patient_id: str, access_token: str, **kwargs) -> list:
        return []
    
    async def fetch_allergy_intolerances(self, patient_id: str, access_token: str, **kwargs) -> list:
        return []


# Provider adapter registry
ADAPTER_REGISTRY: Dict[str, Type[BaseEHRAdapter]] = {
    "epic": EpicAdapter,
    "cerner": CernerAdapter,
    "mock": MockAdapter,
}


def get_adapter(provider: str) -> BaseEHRAdapter:
    """
    Get EHR adapter instance for provider.
    
    Args:
        provider: Provider name (epic, cerner, eclinicalworks, athenahealth, meditech)
    
    Returns:
        Initialized adapter instance
    
    Raises:
        ValueError: If provider is not supported
    """
    
    adapter_class = ADAPTER_REGISTRY.get(provider.lower())
    
    if not adapter_class:
        raise ValueError(f"Unsupported EHR provider: {provider}")
    
    # Get configuration based on provider
    if provider == "epic":
        return EpicAdapter(
            client_id=settings.EPIC_CLIENT_ID,
            client_secret=settings.EPIC_CLIENT_SECRET.get_secret_value(),
            redirect_uri=settings.EPIC_REDIRECT_URI,
            fhir_base_url=settings.EPIC_FHIR_BASE,
            auth_url=settings.EPIC_AUTH_URL,
            token_url=settings.EPIC_TOKEN_URL,
        )
    elif provider == "cerner":
        return CernerAdapter(
            client_id=settings.CERNER_CLIENT_ID,
            client_secret=settings.CERNER_CLIENT_SECRET.get_secret_value(),
            redirect_uri=settings.CERNER_REDIRECT_URI,
            fhir_base_url=settings.CERNER_FHIR_BASE,
            auth_url=settings.CERNER_AUTH_URL,
            token_url=settings.CERNER_TOKEN_URL,
        )
    elif provider == "mock":
        return MockAdapter(
            client_id="mock_client",
            client_secret="mock_secret",
            redirect_uri="http://localhost:8000/auth/mock/callback",
            fhir_base_url="http://mock-fhir.com",
            auth_url="http://mock-fhir.com/auth",
            token_url="http://mock-fhir.com/token",
        )
    else:
        raise ValueError(f"Provider {provider} not yet configured")


__all__ = [
    "BaseEHRAdapter",
    "EpicAdapter",
    "CernerAdapter",
    "MockAdapter",
    "get_adapter",
    "ADAPTER_REGISTRY",
]
