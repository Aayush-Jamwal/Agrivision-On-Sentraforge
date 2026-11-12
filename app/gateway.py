import os
import json
import logging
from typing import Dict, Any, Optional
import httpx
from fastapi import FastAPI, Request, HTTPException, Security, Depends, status
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.schemas import (
    ChatCompletionRequest,
    GatewayHealthResponse,
    CropDiseaseLookupInput,
    CropDiseaseLookupOutput,
    WeatherCallInput,
    WeatherCallOutput
)
from utils.security import scrub_pii, sanitize_messages
from tools.mcp_tools import lookup_crop_disease, get_weather_forecast

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SovereignGateway")

# Gateway Configuration
GATEWAY_API_KEY = os.getenv("GATEWAY_API_KEY", "agrivision-sovereign-key-2026")
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1").rstrip("/")
RATE_LIMIT_RULE = os.getenv("GATEWAY_RATE_LIMIT", "60/minute")

# Initialize SlowAPI Rate Limiter
limiter = Limiter(key_func=get_remote_address, default_limits=[RATE_LIMIT_RULE])

# Initialize FastAPI App
app = FastAPI(
    title="AgriVision Sovereign Security Gateway",
    description="Sovereign AI API Gateway: PII Sanitization, API Key Auth, Rate Limiting, and vLLM Proxy",
    version="2.0.0"
)

# Attach SlowAPI exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key Security Scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(
    request: Request,
    api_key_from_header: Optional[str] = Security(api_key_header)
) -> str:
    """
    Validates incoming request authentication.
    Accepts X-API-Key header OR standard Authorization: Bearer <key> header.
    """
    # 1. Check X-API-Key header
    provided_key = api_key_from_header
    
    # 2. Check Authorization: Bearer <key> if X-API-Key is missing
    if not provided_key:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            provided_key = auth_header[7:].strip()
            
    if not provided_key or provided_key != GATEWAY_API_KEY:
        logger.warning(f"Unauthorized access attempt from {get_remote_address(request)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Missing or invalid API key. Please supply a valid 'X-API-Key' header."
        )
    return provided_key

# =====================================================================
# GATEWAY HEALTH & METRICS ENDPOINTS
# =====================================================================

@app.get("/health", response_model=GatewayHealthResponse)
async def health_check():
    """
    Gateway health monitor reporting proxy status, rate limits, PII filter,
    and downstream vLLM server reachability.
    """
    downstream_ok = False
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            resp = await client.get(f"{VLLM_BASE_URL}/models")
            downstream_ok = resp.status_code in [200, 401, 403]
    except Exception:
        downstream_ok = False

    return GatewayHealthResponse(
        status="ONLINE",
        gateway_port=8080,
        vllm_downstream_url=VLLM_BASE_URL,
        rate_limit=RATE_LIMIT_RULE,
        pii_redaction="Active (Aadhaar, Indian Phone, Email, GPS, Name)",
        downstream_reachable=downstream_ok
    )

@app.get("/")
async def root():
    return {
        "service": "AgriVision Sovereign Security Gateway",
        "version": "2.0.0",
        "endpoints": {
            "chat_completions": "/v1/chat/completions",
            "models": "/v1/models",
            "tools_crop_disease": "/v1/tools/crop_disease_lookup",
            "tools_weather": "/v1/tools/weather_call",
            "health": "/health"
        }
    }

# =====================================================================
# OPENAI-COMPATIBLE PROXY ENDPOINTS (vLLM DOWNSTREAM)
# =====================================================================

@app.get("/v1/models")
async def list_models(api_key: str = Depends(verify_api_key)):
    """Proxies model listing downstream or provides default sovereign 8B model metadata."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{VLLM_BASE_URL}/models")
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.warning(f"Downstream model fetch notice: {str(e)}")

    # Default metadata response if vLLM models endpoint is not directly exposing
    return {
        "object": "list",
        "data": [
            {
                "id": "meta-llama/Meta-Llama-3.1-8B-Instruct",
                "object": "model",
                "created": 1720000000,
                "owned_by": "sovereign-vllm"
            }
        ]
    }

@app.post("/v1/chat/completions")
@limiter.limit(RATE_LIMIT_RULE)
async def chat_completions(
    request: Request,
    payload: ChatCompletionRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Core Sovereign Gateway Ingestion Pipeline:
    1. Authenticates X-API-Key header.
    2. Applies IP-based rate limiting (slowapi).
    3. Shift-Left PII Sanitization: strips Indian Aadhaar, phone numbers, emails, coordinates, names.
    4. Forwards sanitized payload to downstream vLLM engine on port 8000 with guided decoding.
    """
    logger.info(f"Incoming ChatCompletion request from {get_remote_address(request)} for model '{payload.model}'")
    
    # 1. SHIFT-LEFT PII REDACTION LAYER
    # Convert incoming messages into sanitized dictionaries
    raw_messages = [msg.model_dump() for msg in payload.messages]
    sanitized_messages = sanitize_messages(raw_messages)
    
    # Reconstruct the downstream payload with scrubbed text
    downstream_payload: Dict[str, Any] = {
        "model": payload.model,
        "messages": sanitized_messages,
        "temperature": payload.temperature,
        "max_tokens": payload.max_tokens,
        "stream": payload.stream
    }
    
    # Preserve vLLM's guided decoding and structured outputs
    if payload.extra_body:
        downstream_payload.update(payload.extra_body)
    if payload.response_format:
        downstream_payload["response_format"] = payload.response_format

    # 2. DISPATCH TO DOWNSTREAM VLLM SERVER (PORT 8000)
    target_url = f"{VLLM_BASE_URL}/chat/completions"
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                target_url,
                json=downstream_payload,
                headers={"Content-Type": "application/json"}
            )
            
            return JSONResponse(
                status_code=resp.status_code,
                content=resp.json()
            )
    except httpx.ConnectError:
        logger.error(f"Downstream vLLM server unreachable at {target_url}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Bad Gateway: Unable to connect to downstream vLLM inference engine at '{target_url}'. Ensure vLLM is running on port 8000."
        )
    except Exception as e:
        logger.error(f"Error proxying request to vLLM: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference Gateway Error: {str(e)}"
        )

# =====================================================================
# SOVEREIGN MODULAR TOOLS ENDPOINTS (ZERO EXTERNAL PAID APIS)
# =====================================================================

@app.post("/v1/tools/crop_disease_lookup", response_model=CropDiseaseLookupOutput)
@limiter.limit(RATE_LIMIT_RULE)
async def tool_crop_disease_lookup(
    request: Request,
    payload: CropDiseaseLookupInput,
    api_key: str = Depends(verify_api_key)
):
    """
    Sovereign Tool 1: Crop Disease Lookup
    Queries the internal local knowledge base of crop diseases, symptoms, and UDA remedies.
    """
    # Enforce PII scrubbing on query parameters
    crop = scrub_pii(payload.crop_name)
    symptoms = scrub_pii(payload.symptoms)
    disease = scrub_pii(payload.disease_name)

    result = lookup_crop_disease(crop_name=crop, symptoms=symptoms, disease_name=disease)
    return CropDiseaseLookupOutput(
        disease_name=result.get("disease_name", "Unknown Pathology"),
        affected_crops=result.get("affected_crops", []),
        symptoms=result.get("symptoms", "No symptoms indexed"),
        organic_treatments=result.get("organic_treatments", []),
        cultural_practices=result.get("cultural_practices", []),
        eco_status=result.get("eco_status", "UDA Organic Standard"),
        warnings=result.get("warnings", []),
        match_type=result.get("match_type")
    )

@app.post("/v1/tools/weather_call", response_model=WeatherCallOutput)
@limiter.limit(RATE_LIMIT_RULE)
async def tool_weather_call(
    request: Request,
    payload: WeatherCallInput,
    api_key: str = Depends(verify_api_key)
):
    """
    Sovereign Tool 2: Weather Call
    Returns localized agricultural weather parameters (temperature, humidity, spore risk).
    Requires zero external paid APIs.
    """
    sanitized_location = scrub_pii(payload.location)
    result = get_weather_forecast(location=sanitized_location)
    
    return WeatherCallOutput(
        location_queried=result.get("location_queried", sanitized_location),
        temperature_c=float(result.get("temperature_c", 22.0)),
        relative_humidity_pct=float(result.get("relative_humidity_pct", 75.0)),
        precipitation_mm=float(result.get("precipitation_mm", 0.0)),
        leaf_wetness_risk=result.get("leaf_wetness_risk", "Moderate"),
        spore_germination_risk=result.get("spore_germination_risk", "Medium"),
        advisory=result.get("advisory", "Standard monitoring advised."),
        source=result.get("source", "AgriVision Sovereign Agro-Climatic Engine")
    )

