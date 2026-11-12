import os
import re
import logging
from typing import Dict, Any, List, Union

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SecurityGuard")

# =====================================================================
# 1. COMPILED PII REGEX PATTERNS (INDIAN PII & AGRICULTURAL METADATA)
# =====================================================================

# 1. Aadhaar Numbers (12 digits, formatted as 4-4-4, 4-4-4 with hyphens, or 12 continuous digits starting with 2-9)
AADHAAR_REGEX = re.compile(
    r'\b[2-9]\d{3}[\s-]?\d{4}[\s-]?\d{4}\b'
    r'|\b\d{4}[\s-]\d{4}[\s-]\d{4}\b'
)

# 2. Indian 10-digit Mobile Numbers (starting with 6, 7, 8, 9, optional +91/91/0 prefix) and international formats
PHONE_REGEX = re.compile(
    r'(?:\+?91[\-\s]?)?[6-9]\d{4}[\-\s]?\d{5}\b'
    r'|\b0?[6-9]\d{9}\b'
    r'|(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
)

# 3. Email Addresses
EMAIL_REGEX = re.compile(
    r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
)

# 4. GPS Coordinates (e.g. "37.7749, -122.4194", "28.6139° N, 77.2090° E", "Lat: 28.6139, Long: 77.2090")
GPS_REGEX = re.compile(
    r'(?:(?:lat(?:itude)?\s*:\s*)?-?\d{1,3}\.\d+\s*°?\s*[NS]?\s*,\s*(?:long?(?:itude)?\s*:\s*)?-?\d{1,3}\.\d+\s*°?\s*[EW]?)'
    r'|(?:lat(?:itude)?\s*:\s*-?\d{1,3}\.\d+\s*°?\s*[NS]?(?:,|\s+)\s*long?(?:itude)?\s*:\s*-?\d{1,3}\.\d+\s*°?\s*[EW]?)'
    r'|-?\d{1,3}\.\d+\s*°?\s*[NS]?\s*,\s*-?\d{1,3}\.\d+\s*°?\s*[EW]?',
    re.IGNORECASE
)

# 5. Explicit Farmer/User Names like "Farmer: Ramesh Kumar" or "Name: Alice"
EXPLICIT_NAME_REGEX = re.compile(
    r'(?:farmer|name|user)\s*:\s*([a-zA-Z]+(?:\s+[a-zA-Z]+){0,3})',
    re.IGNORECASE
)

# 6. Introductory Names like "My name is Ramesh Kumar" or "I am Alice"
INTRO_NAME_REGEX = re.compile(
    r'\b(?:my name is|i am)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)\b',
    re.IGNORECASE
)

# Banned chemical list for agricultural bio-compliance screening
BANNED_CHEMICALS = [
    "ddt", "paraquat", "chlorpyrifos", "glyphosate", 
    "dieldrin", "heptachlor", "endosulfan", "lindane",
    "carbofuran", "aldicarb", "methyl parathion"
]

# =====================================================================
# 2. PII SCRUBBING FUNCTIONS
# =====================================================================

def scrub_pii(text: str) -> str:
    """
    Scrubs Personally Identifiable Information (PII) from user input strings
    before transmitting data to external LLM APIs or downstream vLLM inference engines.
    Redacts:
    - Indian Aadhaar numbers -> [REDACTED_AADHAAR]
    - 10-digit Indian & international mobile numbers -> [REDACTED_PHONE]
    - Email addresses -> [REDACTED_EMAIL]
    - GPS coordinates -> [REDACTED_COORDINATES]
    - Farmer and personal names -> [REDACTED_NAME]
    """
    if not text or not isinstance(text, str):
        return text

    scrubbed = text

    # 1. Redact Indian Aadhaar numbers
    scrubbed = AADHAAR_REGEX.sub("[REDACTED_AADHAAR]", scrubbed)

    # 2. Redact Phone numbers (Indian 10-digit mobile & international formats)
    scrubbed = PHONE_REGEX.sub("[REDACTED_PHONE]", scrubbed)

    # 3. Redact Emails
    scrubbed = EMAIL_REGEX.sub("[REDACTED_EMAIL]", scrubbed)

    # 4. Redact GPS coordinates
    scrubbed = GPS_REGEX.sub("[REDACTED_COORDINATES]", scrubbed)

    # 5. Redact explicit names ("Farmer: Ramesh Kumar")
    for match in EXPLICIT_NAME_REGEX.finditer(scrubbed):
        captured_name = match.group(1).strip()
        # Protect common agricultural/botanical terms from inadvertent redaction
        if captured_name.lower() not in ["tomato", "potato", "corn", "wheat", "citrus", "orange", "lemon", "lime", "barley", "cucurbits"]:
            scrubbed = scrubbed.replace(captured_name, "[REDACTED_NAME]")

    # 6. Redact introductory names ("My name is John Doe")
    for match in INTRO_NAME_REGEX.finditer(scrubbed):
        captured_name = match.group(1).strip()
        if captured_name.lower() not in ["tomato", "potato", "corn", "wheat", "citrus", "orange", "lemon", "lime", "barley", "cucurbits"]:
            scrubbed = scrubbed.replace(captured_name, "[REDACTED_NAME]")

    logger.debug("PII scrubbing filter applied successfully.")
    return scrubbed

def sanitize_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Security Shift-Left Gatekeeper:
    Ensures every message payload sent through the FastAPI gateway has all PII redacted.
    Handles both plain string content and structured multimodal content blocks.
    """
    sanitized: List[Dict[str, Any]] = []
    for msg in messages:
        msg_copy = dict(msg)
        content = msg_copy.get("content")
        if isinstance(content, str):
            msg_copy["content"] = scrub_pii(content)
        elif isinstance(content, list):
            # Multimodal parts: list of dicts (e.g., text, image_url)
            sanitized_parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    part_copy = dict(part)
                    part_copy["text"] = scrub_pii(part_copy.get("text", ""))
                    sanitized_parts.append(part_copy)
                else:
                    sanitized_parts.append(part)
            msg_copy["content"] = sanitized_parts
        sanitized.append(msg_copy)
    return sanitized

def verify_environment() -> Dict[str, str]:
    """
    Verifies the Sovereign inference setup configuration.
    Defaults to FastAPI Security Gateway at http://localhost:8080/v1.
    """
    gateway_url = (
        os.getenv("GATEWAY_BASE_URL")
        or os.getenv("OPENAI_BASE_URL")
        or "http://localhost:8080/v1"
    ).strip()

    api_key = (
        os.getenv("GATEWAY_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or "agrivision-sovereign-key-2026"
    ).strip()

    model_name = (
        os.getenv("OPENAI_MODEL_NAME")
        or os.getenv("VLLM_MODEL")
        or "meta-llama/Meta-Llama-3.1-8B-Instruct"
    ).strip()

    return {
        "base_url": gateway_url,
        "api_key": api_key,
        "model_name": model_name
    }
