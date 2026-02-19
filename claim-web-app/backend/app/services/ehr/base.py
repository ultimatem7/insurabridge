"""
Base EHR Adapter
Abstract base class for EHR provider integrations
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
import structlog

logger = structlog.get_logger(__name__)


class BaseEHRAdapter(ABC):
    """
    Base class for EHR provider adapters.
    
    All EHR integrations must implement this interface to ensure
    consistent behavior across different providers.
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        fhir_base_url: str,
        auth_url: str,
        token_url: str,
    ):
        """
        Initialize EHR adapter.
        
        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: OAuth redirect URI
            fhir_base_url: FHIR API base URL
            auth_url: OAuth authorization endpoint
            token_url: OAuth token endpoint
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.fhir_base_url = fhir_base_url
        self.auth_url = auth_url
        self.token_url = token_url
        
        self.logger = logger.bind(provider=self.provider_name)
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name (e.g., 'epic', 'cerner')."""
        pass
    
    @abstractmethod
    def get_authorization_url(
        self,
        state: str,
        scope: str | None = None,
        **kwargs
    ) -> str:
        """
        Generate OAuth authorization URL.
        
        Args:
            state: OAuth state parameter
            scope: Requested FHIR scopes
            **kwargs: Additional provider-specific parameters
        
        Returns:
            Authorization URL
        """
        pass
    
    @abstractmethod
    async def exchange_code_for_token(
        self,
        code: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: OAuth authorization code
            **kwargs: Additional provider-specific parameters
        
        Returns:
            Token response with access_token, refresh_token, expires_in, patient, etc.
        """
        pass
    
    @abstractmethod
    async def refresh_access_token(
        self,
        refresh_token: str
    ) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: OAuth refresh token
        
        Returns:
            New token response
        """
        pass
    
    @abstractmethod
    async def fetch_patient(
        self,
        patient_id: str,
        access_token: str
    ) -> Dict[str, Any]:
        """
        Fetch patient resource.
        
        Args:
            patient_id: FHIR Patient ID
            access_token: OAuth access token
        
        Returns:
            FHIR Patient resource
        """
        pass
    
    @abstractmethod
    async def fetch_encounters(
        self,
        patient_id: str,
        access_token: str,
        status: str | None = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch patient encounters.
        
        Args:
            patient_id: FHIR Patient ID
            access_token: OAuth access token
            status: Filter by encounter status
            **kwargs: Additional query parameters
        
        Returns:
            List of FHIR Encounter resources
        """
        pass
    
    @abstractmethod
    async def fetch_conditions(
        self,
        patient_id: str,
        access_token: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch patient conditions (diagnoses).
        
        Args:
            patient_id: FHIR Patient ID
            access_token: OAuth access token
            **kwargs: Additional query parameters
        
        Returns:
            List of FHIR Condition resources
        """
        pass
    
    @abstractmethod
    async def fetch_procedures(
        self,
        patient_id: str,
        access_token: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch patient procedures.
        
        Args:
            patient_id: FHIR Patient ID
            access_token: OAuth access token
            **kwargs: Additional query parameters
        
        Returns:
            List of FHIR Procedure resources
        """
        pass
    
    @abstractmethod
    async def fetch_observations(
        self,
        patient_id: str,
        access_token: str,
        category: str | None = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch patient observations (labs, vitals).
        
        Args:
            patient_id: FHIR Patient ID
            access_token: OAuth access token
            category: Observation category filter
            **kwargs: Additional query parameters
        
        Returns:
            List of FHIR Observation resources
        """
        pass
    
    @abstractmethod
    async def fetch_document_references(
        self,
        patient_id: str,
        access_token: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch clinical documents.
        
        Args:
            patient_id: FHIR Patient ID
            access_token: OAuth access token
            **kwargs: Additional query parameters
        
        Returns:
            List of FHIR DocumentReference resources
        """
        pass
    
    @abstractmethod
    async def fetch_medication_requests(
        self,
        patient_id: str,
        access_token: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch medication requests.
        
        Args:
            patient_id: FHIR Patient ID
            access_token: OAuth access token
            **kwargs: Additional query parameters
        
        Returns:
            List of FHIR MedicationRequest resources
        """
        pass
    
    @abstractmethod
    async def fetch_allergy_intolerances(
        self,
        patient_id: str,
        access_token: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch allergy and intolerance information.
        
        Args:
            patient_id: FHIR Patient ID
            access_token: OAuth access token
            **kwargs: Additional query parameters
        
        Returns:
            List of FHIR AllergyIntolerance resources
        """
        pass
    
    async def fetch_clinical_notes(
        self,
        patient_id: str,
        access_token: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch clinical notes (default implementation using DocumentReference).
        
        Can be overridden by specific adapters if they have better methods.
        """
        return await self.fetch_document_references(patient_id, access_token, **kwargs)
    
    async def fetch_all_encounter_data(
        self,
        patient_id: str,
        encounter_id: str,
        access_token: str
    ) -> Dict[str, Any]:
        """
        Fetch all relevant data for an encounter.
        
        This is a convenience method that fetches all necessary resources
        for claim generation.
        """
        self.logger.info("Fetching complete encounter data", 
                        patient_id=patient_id, 
                        encounter_id=encounter_id)
        
        # Fetch resources in parallel for performance
        import asyncio
        
        results = await asyncio.gather(
            self.fetch_patient(patient_id, access_token),
            self.fetch_encounters(patient_id, access_token),
            self.fetch_conditions(patient_id, access_token),
            self.fetch_procedures(patient_id, access_token),
            self.fetch_observations(patient_id, access_token),
            self.fetch_clinical_notes(patient_id, access_token),
            self.fetch_medication_requests(patient_id, access_token),
            return_exceptions=True
        )
        
        patient, encounters, conditions, procedures, observations, notes, medications = results
        
        # Filter encounter
        encounter = None
        if not isinstance(encounters, Exception):
            encounter = next(
                (e for e in encounters if e.get("id") == encounter_id),
                None
            )
        
        return {
            "patient": patient if not isinstance(patient, Exception) else None,
            "encounter": encounter,
            "conditions": conditions if not isinstance(conditions, Exception) else [],
            "procedures": procedures if not isinstance(procedures, Exception) else [],
            "observations": observations if not isinstance(observations, Exception) else [],
            "clinical_notes": notes if not isinstance(notes, Exception) else [],
            "medications": medications if not isinstance(medications, Exception) else [],
        }
