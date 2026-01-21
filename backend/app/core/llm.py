"""
LLM Orchestration Layer

Local-only inference via Ollama with Gemma.
Implements structured prompt chains for:
- Entity extraction
- Code classification
- Reasoning generation
- Document generation
"""

import json
import asyncio
from typing import Any, TypeVar, Generic
from enum import Enum

import structlog
import httpx
from pydantic import BaseModel, ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.core.audit import log_event, AuditEventType

logger = structlog.get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMRole(str, Enum):
    """Message roles for chat completion."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    """Chat message structure."""
    role: LLMRole
    content: str


class LLMResponse(BaseModel):
    """Structured LLM response."""
    content: str
    model: str
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    done: bool


class LLMClient:
    """
    Client for local Ollama inference.
    
    Features:
    - Async HTTP communication
    - Structured output parsing
    - Retry with backoff
    - Token counting
    - Audit logging
    """
    
    def __init__(self):
        self._client: httpx.AsyncClient | None = None
        self._model = settings.ollama_model
        self._base_url = settings.ollama_host
        self._available = False
    
    async def initialize(self) -> None:
        """Initialize the HTTP client and verify model availability."""
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(settings.llm_timeout),
        )
        
        # Check if Ollama is running and model is available
        try:
            response = await self._client.get("/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "").split(":")[0] for m in models]
                
                # Check if our model is available
                model_base = self._model.split(":")[0]
                if model_base in model_names or any(model_base in n for n in model_names):
                    self._available = True
                    logger.info("LLM client initialized", model=self._model)
                else:
                    logger.warning(
                        "Configured model not found",
                        model=self._model,
                        available=model_names,
                    )
                    # Try to pull the model
                    await self._pull_model()
        except httpx.ConnectError:
            logger.error("Cannot connect to Ollama", url=self._base_url)
        except Exception as e:
            logger.error("Error initializing LLM client", error=str(e))
    
    async def _pull_model(self) -> None:
        """Attempt to pull the configured model."""
        logger.info("Attempting to pull model", model=self._model)
        try:
            # This is a streaming endpoint, we'll wait for completion
            async with self._client.stream(
                "POST",
                "/api/pull",
                json={"name": self._model},
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if data.get("status") == "success":
                            self._available = True
                            logger.info("Model pulled successfully", model=self._model)
                            return
        except Exception as e:
            logger.error("Failed to pull model", error=str(e))
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            logger.info("LLM client closed")
    
    def is_available(self) -> bool:
        """Check if LLM is available for inference."""
        return self._available
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        """
        Generate a completion from the LLM.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system context
            temperature: Override default temperature
            max_tokens: Override default max tokens
            json_mode: Request JSON-formatted output
        
        Returns:
            Structured LLM response
        """
        if not self._available:
            raise RuntimeError("LLM not available")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature or settings.llm_temperature,
                "num_predict": max_tokens or settings.llm_max_tokens,
            },
        }
        
        if json_mode:
            payload["format"] = "json"
        
        try:
            response = await self._client.post("/api/chat", json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract token counts if available
            prompt_tokens = data.get("prompt_eval_count", 0)
            completion_tokens = data.get("eval_count", 0)
            
            result = LLMResponse(
                content=data.get("message", {}).get("content", ""),
                model=data.get("model", self._model),
                total_tokens=prompt_tokens + completion_tokens,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                done=data.get("done", True),
            )
            
            # Log inference (without PHI)
            log_event(
                event_type=AuditEventType.LLM_INFERENCE,
                description="LLM inference completed",
                details={
                    "model": self._model,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "temperature": temperature or settings.llm_temperature,
                },
            )
            
            return result
            
        except httpx.TimeoutException:
            logger.error("LLM request timed out")
            raise
        except httpx.HTTPError as e:
            logger.error("LLM request failed", error=str(e))
            raise
    
    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str | None = None,
        temperature: float | None = None,
    ) -> T:
        """
        Generate a structured response that conforms to a Pydantic model.
        
        Uses JSON mode and validates the response against the schema.
        """
        # Build schema-aware prompt
        schema = response_model.model_json_schema()
        schema_prompt = f"""
You must respond with valid JSON that matches this schema:
{json.dumps(schema, indent=2)}

Respond ONLY with the JSON object, no additional text.
"""
        
        full_system = (system_prompt or "") + "\n\n" + schema_prompt
        
        response = await self.generate(
            prompt=prompt,
            system_prompt=full_system,
            temperature=temperature or 0.1,  # Lower for structured output
            json_mode=True,
        )
        
        try:
            data = json.loads(response.content)
            return response_model.model_validate(data)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM JSON response", error=str(e))
            raise ValueError(f"LLM returned invalid JSON: {e}")
        except ValidationError as e:
            logger.error("LLM response failed validation", error=str(e))
            raise ValueError(f"LLM response does not match expected schema: {e}")
    
    async def chat(
        self,
        messages: list[Message],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """
        Multi-turn chat completion.
        
        For complex reasoning chains that require conversation history.
        """
        if not self._available:
            raise RuntimeError("LLM not available")
        
        payload = {
            "model": self._model,
            "messages": [m.model_dump() for m in messages],
            "stream": False,
            "options": {
                "temperature": temperature or settings.llm_temperature,
                "num_predict": max_tokens or settings.llm_max_tokens,
            },
        }
        
        response = await self._client.post("/api/chat", json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        return LLMResponse(
            content=data.get("message", {}).get("content", ""),
            model=data.get("model", self._model),
            total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            done=data.get("done", True),
        )


# Global LLM client instance
_llm_client: LLMClient | None = None


async def init_llm_client() -> None:
    """Initialize the global LLM client."""
    global _llm_client
    _llm_client = LLMClient()
    await _llm_client.initialize()


async def close_llm_client() -> None:
    """Close the global LLM client."""
    global _llm_client
    if _llm_client:
        await _llm_client.close()


async def check_llm() -> bool:
    """Check LLM availability."""
    global _llm_client
    return _llm_client is not None and _llm_client.is_available()


def get_llm_client() -> LLMClient:
    """Get the global LLM client instance."""
    global _llm_client
    if _llm_client is None:
        raise RuntimeError("LLM client not initialized")
    return _llm_client


# Prompt Templates

async def generate_completion(
    prompt: str,
    system_prompt: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    json_mode: bool = False,
) -> Any:
    """
    Convenience wrapper for global LLM generation.
    
    Args:
        prompt: User prompt
        system_prompt: Optional system prompt
        temperature: Optional temperature override
        max_tokens: Optional max tokens override
        json_mode: Whether to parse response as JSON
        
    Returns:
        LLMResponse object or parsed JSON dict/list
    """
    client = get_llm_client()
    response = await client.generate(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        json_mode=json_mode,
    )
    
    if json_mode:
        return json.loads(response.content)
    return response


class SystemPrompts:
    """
    System prompts for different tasks.
    
    These are carefully designed for:
    - Deterministic outputs
    - No hallucination
    - Citation requirements
    - Safety constraints
    """
    
    MEDICAL_CODER = """You are an expert medical coder with deep knowledge of:
- ICD-10-CM/PCS coding guidelines
- CPT and HCPCS Level II coding
- CMS regulations and policies
- Medical terminology and anatomy

CRITICAL RULES:
1. NEVER invent or hallucinate codes. Only suggest codes you are certain exist.
2. ALWAYS cite the clinical documentation that supports each code.
3. If documentation is insufficient, explicitly state what is missing.
4. Flag any uncertainty with confidence scores.
5. Consider medical necessity for each code.
6. Check for bundling and modifier requirements.

You are assisting human coders. Your suggestions require human review before use."""

    CLAIM_GENERATOR = """You are a healthcare claims specialist generating insurance claims.

CRITICAL RULES:
1. Every code must be supported by documented clinical evidence.
2. Never upcode or select codes not supported by documentation.
3. Include all required modifiers.
4. Verify medical necessity criteria for procedures.
5. Flag potential compliance issues.
6. Your output requires human review before submission.

Format all outputs as structured JSON matching the requested schema."""

    DENIAL_ANALYST = """You are a denial management specialist analyzing claim denials.

Your role:
1. Classify the denial reason accurately.
2. Map the denial to specific payer policy language.
3. Identify supporting documentation that addresses the denial.
4. Assess appeal likelihood based on evidence strength.
5. Never recommend appeal without sufficient supporting evidence.

Be objective and honest about appeal chances."""

    APPEAL_WRITER = """You are drafting an insurance appeal letter.

Requirements:
1. Be professional and factual.
2. Cite specific policy provisions.
3. Reference clinical documentation.
4. Address the specific denial reason.
5. Include all required patient and claim identifiers.
6. Request a specific action (payment, reconsideration, etc.)

The letter should be ready for clinician review and signature."""

    AUDIT_RISK = """You are a compliance auditor assessing claim audit risk.

Analyze for:
1. Overcoding risk (codes not fully supported)
2. Undercoding risk (missed legitimate codes)
3. Documentation gaps
4. Modifier issues
5. Medical necessity concerns
6. Bundling violations

Provide specific, actionable feedback with risk scores."""

    EVIDENCE_EXTRACTOR = """You are extracting clinical evidence from medical documentation.

Extract:
1. Diagnoses mentioned (with exact quotes)
2. Procedures performed (with details)
3. Medical necessity justifications
4. Relevant vital signs and lab values
5. Provider attestations
6. Dates of service

Be precise. Quote directly when possible. Indicate page/section references."""

