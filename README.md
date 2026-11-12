# AgriVision Disease Guard 🌿🛡️
*A Sovereign, Air-Gapped AI Assistant for Sustainable Agriculture*

![AgriVision Banner](assets/agrivision_banner.png)

[![FastAPI Gateway CI](https://github.com/Aayush-Jamwal/AgriVision-Disease-Guard/actions/workflows/ci.yml/badge.svg)](https://github.com/Aayush-Jamwal/AgriVision-Disease-Guard/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![vLLM](https://img.shields.io/badge/vLLM-Sovereign%20Engine-brightgreen.svg)](https://github.com/vllm-project/vllm)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 1. What AgriVision Is

**AgriVision Disease Guard** is an intelligent, eco-friendly crop doctor designed for farmers, agricultural extension workers, and agronomists. When crops show signs of illness—such as spotted leaves, powdery mold, or stunted growth—farmers can describe what they see or upload a photo of the affected plant. 

AgriVision analyzes the symptoms, identifies the exact plant disease, assesses how severe the infection is, and generates an **Action Playbook** containing 100% organic, non-toxic remedies. It never recommends harmful synthetic pesticides (like DDT or Paraquat); instead, it focuses on certified bio-fungicides, natural botanical oils, and smart cultural practices like crop rotation and canopy pruning.

Crucially, **AgriVision operates as a Sovereign AI solution**. It runs completely offline on your own local machines or private cloud—requiring **zero third-party cloud APIs** and keeping all sensitive farm telemetry and farmer information safe and private.

---

## 2. What Changed from the Original AgriVision (Plain-English Breakdown)

In our Week 2 refactoring, we transformed AgriVision from a prototype dependent on external cloud services into a secure, enterprise-grade, self-hosted system. Here is what changed and why:

### 1. Self-Hosted Sovereign AI (Moving from Gemini to Local vLLM)
* **How it worked before:** The original app sent farmer questions and photos directly to Google Cloud (Gemini API). If the internet went down, or if the cloud service changed pricing or privacy rules, the app could stop working.
* **How it works now:** We swapped out the proprietary Gemini client for the industry-standard **OpenAI-compatible client library**, targeting our own local **vLLM inference server** running an open-weight 8-billion parameter model (such as `Llama-3.1-8B-Instruct` or `Qwen2.5-7B`).
* **Why it matters:** Sensitive agricultural data never leaves our servers. The app can run in remote rural areas with limited connectivity, without recurring SaaS bills or vendor lock-in.

### 2. A Dedicated Security "Front Door" (FastAPI Gateway on Port 8080)
* **How it worked before:** Any client interface communicated directly with the AI, with no access barrier or traffic control.
* **How it works now:** We placed an asynchronous **FastAPI Security Gateway** in front of the inference engine:
  * **API Key Authentication (`X-API-Key`):** Only authorized clients and dashboard sessions with a valid key can make requests. Unauthenticated requests are rejected immediately with a `401 Unauthorized` error.
  * **Rate Limiting (`slowapi`):** Incoming traffic is capped (e.g., 60 requests per minute per IP address). This prevents a runaway script or malicious user from overwhelming the local GPU hardware.
* **Why it matters:** You would never expose a database directly to the open web without a firewall; your AI model deserves the same protection against denial-of-service and unauthorized use.

### 3. Prompt Externalization (Separating Words from Code)
* **How it worked before:** The instructions given to the AI (system prompts) were hardcoded inside Python strings deep within the code files. Changing a word required editing and redeploying Python scripts.
* **How it works now:** All prompt templates have been moved into dedicated, version-controlled plain text files in the `/prompts` folder (such as `diagnostician_system_v1.txt`). The app loads these files dynamically at runtime.
* **Why it matters:** Prompts can now be tuned, improved, and audited like configuration files. Agronomists can refine instructions without touching Python code or risking syntax errors.

### 4. Guaranteed Output Structure (Pydantic & Guided Decoding)
* **How it worked before:** We politely asked the model in English: *"Please reply in valid JSON."* Sometimes the model added conversational chatter, missed brackets, or returned incomplete fields, which caused the application to crash.
* **How it works now:** We defined strict data blueprints (**Pydantic v2 schemas**) in `app/schemas.py`. When making a call to vLLM, we pass `guided_json` constraints. At the mathematical logit level, vLLM forces the AI to emit *only* valid JSON tokens that match our exact schema.
* **Why it matters:** The failure rate for invalid JSON drops to **0%**. In repeated batch testing of 20 diverse crop scenarios, our pipeline achieved a **100% schema reliability score with zero validation errors**.

### 5. Two Local Helper Tools (Zero-Cost Real-World Facts)
Instead of asking the language model to memorize every single plant disease or guess what the weather looks like, we built two modular local tools in `tools/mcp_tools.py`:
1. **Crop Disease Lookup (`crop_disease_lookup`):** Searches an internal offline verified catalog (`data/disease_database.json`) using exact and fuzzy matching to pull verified organic treatments and safety warnings.
2. **Agricultural Weather Check (`weather_call`):** Calculates local temperature, relative humidity, rain levels, and spore germination risk for any field location.
* **Why it matters:** Both tools run 100% locally with **zero paid external APIs**, giving the AI grounded facts before it produces a recommendation.

### 6. Shift-Left Privacy & Indian PII Redaction
* Before user messages ever touch the AI or its memory buffers, an automated security filter cleans the text:
  * **Aadhaar Numbers:** 12-digit Indian national identity numbers are replaced with `[REDACTED_AADHAAR]`.
  * **Mobile Phone Numbers:** 10-digit Indian phone numbers (including `+91` or `0` prefixes) are replaced with `[REDACTED_PHONE]`.
  * **Emails, GPS Coordinates, and Personal Names:** Cleaned and replaced with `[REDACTED_EMAIL]`, `[REDACTED_COORDINATES]`, and `[REDACTED_NAME]`.
* **Why it matters:** Farmer identities and precise field locations remain strictly private and compliant with data governance principles.

---

## 3. Project Layout

```text
AgriVision-Disease-Guard/
├── .github/
│   └── workflows/
│       └── ci.yml               # Automated GitHub Actions test pipeline
├── .streamlit/
│   └── config.toml              # Streamlit dashboard layout and theme styling
├── agents/
│   └── workflow.py              # Multi-agent state orchestration & OpenAI client logic
├── app/
│   ├── __init__.py              # App package marker
│   ├── gateway.py               # FastAPI Security Gateway (Port 8080 proxy, PII filter, rate limiting)
│   ├── main.py                  # Gateway app entrypoint
│   ├── prompt_loader.py         # Dynamic runtime prompt template loader
│   └── schemas.py               # Strict Pydantic models & vLLM JSON schemas
├── assets/                      # UI banners, flowcharts, and demo sample leaf images
├── data/
│   └── disease_database.json    # Local verified database of eco-friendly remedies
├── notebooks/
│   └── README.md                # Dedicated folder for Week 2 deliverables & analysis notebooks
├── prompts/                     # Externalized, versioned system prompt templates
│   ├── agrivision_advisory_v1.txt
│   ├── diagnostician_system_v1.txt
│   ├── strategy_broker_v1.txt
│   └── tool_system_v1.txt
├── tests/
│   ├── test_gateway.py          # Gateway security & endpoint tests (auth, PII, tools)
│   └── test_schema_reliability.py # 20-iteration batch reliability test (0% schema error rate)
├── tools/
│   └── mcp_tools.py             # Local Python tools (crop_disease_lookup, weather_call)
├── utils/
│   └── security.py              # Indian PII regex patterns and text scrubbing filters
├── .gitignore                   # Ignores .env, models, checkpoints, and cache
├── app.py                       # Bilingual (English & Hindi) Streamlit Dashboard
├── Dockerfile                   # Production Dockerfile for the FastAPI Gateway
├── MIGRATION_GUIDE.md           # Deep architectural migration notes
├── README.md                    # This plain-English project manual
└── requirements.txt             # Minimal, pinned Python dependencies
```

---

## 4. How to Run Locally & via Docker

### Prerequisites
* Python 3.10, 3.11, or 3.12 installed
* Git installed

### Step 1: Clone the Repository & Install Dependencies
```bash
git clone https://github.com/Aayush-Jamwal/AgriVision-Disease-Guard.git
cd AgriVision-Disease-Guard

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables (Optional)
The system has safe, secure defaults preconfigured. If you wish to customize keys or ports, create a `.env` file in the root folder:
```bash
GATEWAY_API_KEY=agrivision-sovereign-key-2026
GATEWAY_URL=http://localhost:8080/v1
VLLM_BASE_URL=http://localhost:8000/v1
GATEWAY_RATE_LIMIT=60/minute
VLLM_MODEL=meta-llama/Llama-3.1-8B-Instruct
```

### Step 3: Launch the FastAPI Security Gateway
In your first terminal, start the gateway server on **Port 8080**:
```bash
python -m uvicorn app.gateway:app --host 0.0.0.0 --port 8080 --reload
```
You can verify it is running by opening `http://localhost:8080/health` in your browser. You will see:
```json
{
  "status": "ONLINE",
  "gateway_port": 8080,
  "vllm_downstream_url": "http://localhost:8000/v1",
  "rate_limit": "60/minute",
  "pii_redaction": "Active (Aadhaar, Indian Phone, Email, GPS, Name)",
  "downstream_reachable": false
}
```

### Step 4: Launch the vLLM Inference Server (GPU Host)
On a machine with GPU hardware, launch vLLM with guided decoding enabled:
```bash
vllm serve meta-llama/Llama-3.1-8B-Instruct \
  --port 8000 \
  --guided-decoding-backend lm-format-enforcer
```
*(If testing on a lightweight laptop without a GPU, the gateway and workflow operate in intelligent local simulation fallback mode automatically).*

### Step 5: Launch the AgriVision Dashboard
In a second terminal, start the interactive web application:
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser. You can click any of the preloaded demo scenarios (Tomato Blight, Wheat Rust, Citrus Greening) or upload your own leaf image, switch languages between English and Hindi, and compile an organic mitigation playbook!

---

### Running via Docker 🐳
You can build and deploy the standalone FastAPI Gateway inside a lightweight Docker container:

```bash
# Build the container image
docker build -t agrivision-gateway:latest .

# Run the container exposing Port 8080
docker run -d -p 8080:8080 --name agrivision-gateway agrivision-gateway:latest

# Check container health
curl http://localhost:8080/health
```

---

## 5. Running Tests

We provide automated unit and reliability tests to guarantee that security, authentication, and output formats work as expected.

Run the full test suite with:
```bash
python -m pytest tests/ -v
```

### What the Tests Verify:
1. **`tests/test_gateway.py`**:
   * Health endpoint returns `200 OK` and reports active security status.
   * Requests without a valid key are rejected with `401 Unauthorized`.
   * Indian PII (Aadhaar, mobile, emails, GPS) is completely scrubbed from inputs.
   * Local tool endpoints (`crop_disease_lookup` and `weather_call`) return valid results.
2. **`tests/test_schema_reliability.py`**:
   * Validates that all Pydantic models export valid JSON Schemas for vLLM.
   * Executes a **20-iteration batch test** covering multiple crops and symptoms, proving **100% schema reliability with 0 errors**.
   * Confirms that malformed or out-of-range payloads (e.g. confidence > 100%) are rejected cleanly.

---

## 6. Author & Week 2 Deliverable Note
* **Author:** [Aayush Jamwal](https://github.com/Aayush-Jamwal)
* **Project Track:** Sovereign AI & Enterprise Agent Architectures (Week 2 Deliverable)
* **License:** MIT License
