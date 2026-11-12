from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any, Union

# =====================================================================
# 1. LOCAL MODULAR TOOL SCHEMAS
# =====================================================================

class CropDiseaseLookupInput(BaseModel):
    """Input payload for the sovereign local crop disease lookup tool."""
    crop_name: str = Field(
        default="",
        description="The target agricultural crop type (e.g. Tomato, Wheat, Citrus, Potato)"
    )
    symptoms: str = Field(
        default="",
        description="Observed foliar or morphological symptoms on the crop"
    )
    disease_name: str = Field(
        default="",
        description="Suspected disease or pathogen keyword"
    )

class CropDiseaseLookupOutput(BaseModel):
    """Output schema returned by the sovereign crop disease lookup tool."""
    disease_name: str = Field(description="Standardized name of the diagnosed disease or condition")
    affected_crops: List[str] = Field(default_factory=list, description="Crops susceptible to this condition")
    symptoms: str = Field(description="Clinical symptoms description")
    organic_treatments: List[str] = Field(description="Verified OMRI/UDA-compliant non-synthetic remedies")
    cultural_practices: List[str] = Field(description="Physical cultural, canopy, and sanitation practices")
    eco_status: str = Field(description="Ecological safety and UDA compliance verification note")
    warnings: List[str] = Field(default_factory=list, description="Immediate environmental or vector warnings")
    match_type: Optional[str] = Field(default=None, description="Lookup match type (exact_key or fuzzy_relevance)")

class WeatherCallInput(BaseModel):
    """Input payload for the sovereign local agro-climatic weather tool."""
    location: str = Field(
        default="Regional Agricultural Zone",
        description="General farm district or agro-climatic zone (PII is scrubbed prior to use)"
    )

class WeatherCallOutput(BaseModel):
    """Output schema returned by the sovereign agro-climatic weather tool."""
    location_queried: str = Field(description="Sanitized agricultural location context")
    temperature_c: float = Field(description="Ambient temperature in Celsius")
    relative_humidity_pct: float = Field(description="Relative atmospheric humidity percentage")
    precipitation_mm: float = Field(description="Precipitation level in millimeters")
    leaf_wetness_risk: str = Field(description="Leaf surface moisture accumulation assessment")
    spore_germination_risk: Literal["Low", "Medium", "High"] = Field(
        description="Atmospheric pathogen spore germination and fungal motility risk rating"
    )
    advisory: str = Field(description="Agro-meteorological advisory regarding foliar disease risk")
    source: str = Field(default="AgriVision Sovereign Agro-Climatic Engine")

# =====================================================================
# 2. STRUCTURED MULTI-AGENT INFERENCE SCHEMAS (vLLM GUIDED DECODING)
# =====================================================================

class DiagnosticianOutput(BaseModel):
    """
    Schema for Agent 1 (Visual Diagnostician) enforced via vLLM guided decoding.
    Guarantees strict JSON output with zero schema errors.
    """
    disease_name: str = Field(
        description="Identified plant disease or pathogen"
    )
    confidence: float = Field(
        ge=0.0, le=100.0,
        description="Confidence percentage score between 0.0 and 100.0"
    )
    severity: Literal["Low", "Medium", "High"] = Field(
        description="Assessed severity level of the foliar infection"
    )
    reasoning: str = Field(
        description="Clinical diagnostic explanation connecting symptoms, morphology, and weather factors"
    )
    weather_risk_factor: Optional[str] = Field(
        default=None,
        description="Specific environmental or moisture factor accelerating pathogen transmission"
    )

class StrategyBrokerOutput(BaseModel):
    """
    Schema for Agent 2 (MCP Strategy Broker) enforced via vLLM guided decoding.
    Guarantees strict non-toxic treatment plan output.
    """
    disease_name: str = Field(
        description="Name of the target plant disease"
    )
    organic_treatments: List[str] = Field(
        description="List of verified non-synthetic, OMRI/UDA-approved biological remedies"
    )
    cultural_practices: List[str] = Field(
        description="List of agronomic physical practices, canopy spacing, and sanitation steps"
    )
    eco_status: str = Field(
        description="Official UDA bio-compliance status declaration"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Immediate environmental or vector containment alerts"
    )
    additional_guidance: str = Field(
        description="Comprehensive paragraph of supportive farm management advice"
    )

class AgriVisionAdvisory(BaseModel):
    """
    Master Structured Agricultural Advisory Schema.
    Combines visual diagnosis, environmental weather assessment, organic bio-treatments,
    sanitation barriers, and compliance audits into a single sovereign contract.
    """
    crop_name: str = Field(description="Name of the agricultural crop")
    diagnosed_condition: str = Field(description="Primary plant disease or condition identified")
    confidence: float = Field(ge=0.0, le=100.0, description="Diagnostic certainty score (0-100%)")
    severity: Literal["Low", "Medium", "High"] = Field(description="Infection severity rating")
    reasoning: str = Field(description="Clinical pathological explanation")
    weather_assessment: Optional[str] = Field(default=None, description="Local climatic risk factors")
    organic_treatments: List[str] = Field(description="OMRI-listed organic remedies")
    cultural_practices: List[str] = Field(description="Field sanitation and cultural barriers")
    safety_compliance: str = Field(description="Safety certification under UDA standards")
    warnings: List[str] = Field(default_factory=list, description="Environmental alerts")

# =====================================================================
# 3. FASTAPI GATEWAY REQUEST / RESPONSE SCHEMAS (OPENAI COMPATIBLE)
# =====================================================================

class ChatMessage(BaseModel):
    role: str = Field(description="Message author role: system, user, assistant, or tool")
    content: Union[str, List[Dict[str, Any]]] = Field(description="Message content string or multimodal blocks")

class ChatCompletionRequest(BaseModel):
    """Standard OpenAI Chat Completion request schema accepted by FastAPI Gateway."""
    model: str = Field(default="meta-llama/Meta-Llama-3.1-8B-Instruct", description="Target model identifier")
    messages: List[ChatMessage] = Field(description="List of conversation turns")
    temperature: Optional[float] = Field(default=0.1, description="Sampling temperature")
    max_tokens: Optional[int] = Field(default=1024, description="Maximum tokens to generate")
    stream: Optional[bool] = Field(default=False, description="Whether to stream back partial tokens")
    extra_body: Optional[Dict[str, Any]] = Field(
        default=None,
        description="vLLM guided decoding parameters, including 'guided_json' schema"
    )
    response_format: Optional[Dict[str, Any]] = Field(
        default=None,
        description="OpenAI response format, e.g. {'type': 'json_object'}"
    )

class GatewayHealthResponse(BaseModel):
    """Health check status returned by the FastAPI security gateway."""
    status: str
    gateway_port: int
    vllm_downstream_url: str
    rate_limit: str
    pii_redaction: str
    downstream_reachable: bool

