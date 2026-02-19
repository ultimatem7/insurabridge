"""
Cerner EHR Adapter
SMART on FHIR integration for Cerner
"""

from typing import Dict, List, Any
from urllib.parse import urlencode
import httpx

from app.services.ehr.base import BaseEHRAdapter


class CernerAdapter(BaseEHRAdapter):
    """Cerner EHR adapter using SMART on FHIR."""
    
    @property
    def provider_name(self) -> str:
        return "cerner"
    
    def get_authorization_url(
        self,
        state: str,
        scope: str | None = None,
        **kwargs
    ) -> str:
        """Generate Cerner authorization URL."""
        
        if not scope:
            scope = " ".join([
                "launch/patient",
                "patient/Patient.read",
                "patient/Encounter.read",
                "patient/Condition.read",
                "patient/Procedure.read",
                "patient/Observation.read",
                "patient/DocumentReference.read",
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
        
        return f"{self.auth_url}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str, **kwargs) -> Dict[str, Any]:
        """Exchange code for Cerner access token."""
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        
        auth = (self.client_id, self.client_secret)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data=data,
                auth=auth,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh Cerner access token."""
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        
        auth = (self.client_id, self.client_secret)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data=data,
                auth=auth,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
    
    async def _fhir_request(
        self,
        resource_path: str,
        access_token: str,
        params: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """Make authenticated FHIR request to Cerner."""
        
        url = f"{self.fhir_base_url}/{resource_path}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/fhir+json",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params or {}, timeout=30.0)
            response.raise_for_status()
            return response.json()
    
    async def fetch_patient(self, patient_id: str, access_token: str) -> Dict[str, Any]:
        return await self._fhir_request(f"Patient/{patient_id}", access_token)
    
    async def fetch_encounters(self, patient_id: str, access_token: str, status: str | None = None, **kwargs) -> List[Dict[str, Any]]:
        params = {"patient": patient_id}
        if status:
            params["status"] = status
        result = await self._fhir_request("Encounter", access_token, params)
        return [e["resource"] for e in result.get("entry", []) if "resource" in e]
    
    async def fetch_conditions(self, patient_id: str, access_token: str, **kwargs) -> List[Dict[str, Any]]:
        result = await self._fhir_request("Condition", access_token, {"patient": patient_id})
        return [e["resource"] for e in result.get("entry", []) if "resource" in e]
    
    async def fetch_procedures(self, patient_id: str, access_token: str, **kwargs) -> List[Dict[str, Any]]:
        result = await self._fhir_request("Procedure", access_token, {"patient": patient_id})
        return [e["resource"] for e in result.get("entry", []) if "resource" in e]
    
    async def fetch_observations(self, patient_id: str, access_token: str, category: str | None = None, **kwargs) -> List[Dict[str, Any]]:
        params = {"patient": patient_id}
        if category:
            params["category"] = category
        result = await self._fhir_request("Observation", access_token, params)
        return [e["resource"] for e in result.get("entry", []) if "resource" in e]
    
    async def fetch_document_references(self, patient_id: str, access_token: str, **kwargs) -> List[Dict[str, Any]]:
        result = await self._fhir_request("DocumentReference", access_token, {"patient": patient_id})
        return [e["resource"] for e in result.get("entry", []) if "resource" in e]
    
    async def fetch_medication_requests(self, patient_id: str, access_token: str, **kwargs) -> List[Dict[str, Any]]:
        result = await self._fhir_request("MedicationRequest", access_token, {"patient": patient_id})
        return [e["resource"] for e in result.get("entry", []) if "resource" in e]
    
    async def fetch_allergy_intolerances(self, patient_id: str, access_token: str, **kwargs) -> List[Dict[str, Any]]:
        result = await self._fhir_request("AllergyIntolerance", access_token, {"patient": patient_id})
        return [e["resource"] for e in result.get("entry", []) if "resource" in e]
