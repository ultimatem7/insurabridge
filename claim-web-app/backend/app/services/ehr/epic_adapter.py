"""
Epic EHR Adapter
Production-ready Epic SMART on FHIR integration
"""

from typing import Dict, List, Any
from urllib.parse import urlencode
import httpx

from app.services.ehr.base import BaseEHRAdapter


class EpicAdapter(BaseEHRAdapter):
    """
    Epic EHR adapter using SMART on FHIR.
    
    Implements full OAuth2 with PKCE and FHIR R4 resource access.
    """
    
    @property
    def provider_name(self) -> str:
        return "epic"
    
    def get_authorization_url(
        self,
        state: str,
        scope: str | None = None,
        code_challenge: str | None = None,
        **kwargs
    ) -> str:
        """Generate Epic authorization URL with PKCE."""
        
        # Default Epic SMART scopes
        if not scope:
            scope = " ".join([
                "launch/patient",
                "patient/Patient.read",
                "patient/Encounter.read",
                "patient/Condition.read",
                "patient/Procedure.read",
                "patient/Observation.read",
                "patient/DocumentReference.read",
                "patient/MedicationRequest.read",
                "patient/AllergyIntolerance.read",
                "online_access",
            ])
        
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": scope,
            "state": state,
            "aud": self.fhir_base_url,
        }
        
        # Epic requires PKCE
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"
        
        url = f"{self.auth_url}?{urlencode(params)}"
        self.logger.info("Generated authorization URL", state=state)
        return url
    
    async def exchange_code_for_token(
        self,
        code: str,
        code_verifier: str | None = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Exchange authorization code for tokens."""
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
        }
        
        # Epic requires PKCE
        if code_verifier:
            data["code_verifier"] = code_verifier
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30.0,
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.logger.info("Token exchange successful", 
                           patient_id=token_data.get("patient"))
            return token_data
    
    async def refresh_access_token(
        self,
        refresh_token: str
    ) -> Dict[str, Any]:
        """Refresh Epic access token."""
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30.0,
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.logger.info("Token refreshed successfully")
            return token_data
    
    async def _fhir_request(
        self,
        resource_path: str,
        access_token: str,
        params: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """Make authenticated FHIR API request."""
        
        url = f"{self.fhir_base_url}/{resource_path}"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/fhir+json",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=headers,
                params=params or {},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
    
    async def fetch_patient(
        self,
        patient_id: str,
        access_token: str
    ) -> Dict[str, Any]:
        """Fetch Epic patient resource."""
        
        self.logger.info("Fetching patient", patient_id=patient_id)
        return await self._fhir_request(
            f"Patient/{patient_id}",
            access_token
        )
    
    async def fetch_encounters(
        self,
        patient_id: str,
        access_token: str,
        status: str | None = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Fetch Epic encounters."""
        
        self.logger.info("Fetching encounters", patient_id=patient_id)
        
        params = {
            "patient": patient_id,
            "_count": kwargs.get("count", 100),
        }
        
        if status:
            params["status"] = status
        
        result = await self._fhir_request("Encounter", access_token, params)
        
        # Extract Bundle entries
        entries = result.get("entry", [])
        return [entry["resource"] for entry in entries if "resource" in entry]
    
    async def fetch_conditions(
        self,
        patient_id: str,
        access_token: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Fetch Epic conditions (diagnoses)."""
        
        self.logger.info("Fetching conditions", patient_id=patient_id)
        
        params = {
            "patient": patient_id,
            "_count": kwargs.get("count", 100),
        }
        
        result = await self._fhir_request("Condition", access_token, params)
        entries = result.get("entry", [])
        return [entry["resource"] for entry in entries if "resource" in entry]
    
    async def fetch_procedures(
        self,
        patient_id: str,
        access_token: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Fetch Epic procedures."""
        
        self.logger.info("Fetching procedures", patient_id=patient_id)
        
        params = {
            "patient": patient_id,
            "_count": kwargs.get("count", 100),
        }
        
        result = await self._fhir_request("Procedure", access_token, params)
        entries = result.get("entry", [])
        return [entry["resource"] for entry in entries if "resource" in entry]
    
    async def fetch_observations(
        self,
        patient_id: str,
        access_token: str,
        category: str | None = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Fetch Epic observations."""
        
        self.logger.info("Fetching observations", patient_id=patient_id)
        
        params = {
            "patient": patient_id,
            "_count": kwargs.get("count", 100),
        }
        
        if category:
            params["category"] = category
        
        result = await self._fhir_request("Observation", access_token, params)
        entries = result.get("entry", [])
        return [entry["resource"] for entry in entries if "resource" in entry]
    
    async def fetch_document_references(
        self,
        patient_id: str,
        access_token: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Fetch Epic clinical documents."""
        
        self.logger.info("Fetching documents", patient_id=patient_id)
        
        params = {
            "patient": patient_id,
            "_count": kwargs.get("count", 100),
        }
        
        result = await self._fhir_request("DocumentReference", access_token, params)
        entries = result.get("entry", [])
        return [entry["resource"] for entry in entries if "resource" in entry]
    
    async def fetch_medication_requests(
        self,
        patient_id: str,
        access_token: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Fetch Epic medication requests."""
        
        self.logger.info("Fetching medications", patient_id=patient_id)
        
        params = {
            "patient": patient_id,
            "_count": kwargs.get("count", 100),
        }
        
        result = await self._fhir_request("MedicationRequest", access_token, params)
        entries = result.get("entry", [])
        return [entry["resource"] for entry in entries if "resource" in entry]
    
    async def fetch_allergy_intolerances(
        self,
        patient_id: str,
        access_token: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Fetch Epic allergies."""
        
        self.logger.info("Fetching allergies", patient_id=patient_id)
        
        params = {
            "patient": patient_id,
            "_count": kwargs.get("count", 100),
        }
        
        result = await self._fhir_request("AllergyIntolerance", access_token, params)
        entries = result.get("entry", [])
        return [entry["resource"] for entry in entries if "resource" in entry]
