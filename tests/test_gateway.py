import os
import sys
import unittest
from fastapi.testclient import TestClient

# Ensure AgriVision-Disease-Guard is in python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.gateway import app, GATEWAY_API_KEY
from utils.security import scrub_pii

class TestFastAPIGateway(unittest.TestCase):
    """
    Test suite for the Sovereign FastAPI Security Gateway.
    Verifies authentication, Indian PII redaction, rate limiting, and tool proxying.
    """

    def setUp(self):
        self.client = TestClient(app)
        self.valid_headers = {"X-API-Key": GATEWAY_API_KEY}

    def test_01_health_check(self):
        """Verify health check endpoint returns 200 and reports security layer status."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ONLINE")
        self.assertEqual(data["gateway_port"], 8080)
        self.assertIn("Aadhaar", data["pii_redaction"])

    def test_02_authentication_enforcement(self):
        """Verify that requests without valid X-API-Key or Bearer token are rejected with 401."""
        # 1. Missing header
        res_missing = self.client.post("/v1/tools/crop_disease_lookup", json={"crop_name": "Tomato"})
        self.assertEqual(res_missing.status_code, 401)
        self.assertIn("Unauthorized", res_missing.json()["detail"])

        # 2. Invalid key
        res_invalid = self.client.post(
            "/v1/tools/crop_disease_lookup",
            json={"crop_name": "Tomato"},
            headers={"X-API-Key": "invalid-hacker-key"}
        )
        self.assertEqual(res_invalid.status_code, 401)

        # 3. Valid key
        res_valid = self.client.post(
            "/v1/tools/crop_disease_lookup",
            json={"crop_name": "Tomato"},
            headers=self.valid_headers
        )
        self.assertEqual(res_valid.status_code, 200)

        # 4. Valid Bearer token
        res_bearer = self.client.post(
            "/v1/tools/crop_disease_lookup",
            json={"crop_name": "Tomato"},
            headers={"Authorization": f"Bearer {GATEWAY_API_KEY}"}
        )
        self.assertEqual(res_bearer.status_code, 200)

    def test_03_indian_pii_redaction(self):
        """Verify that Indian PII (Aadhaar, 10-digit mobile, emails) is scrubbed."""
        raw_text = (
            "Farmer: Ramesh Patel, Aadhaar: 5432 8765 4321, "
            "Phone: +91 98765 43210, Email: ramesh@kisan.gov.in, "
            "Location: 28.6139, 77.2090"
        )
        scrubbed = scrub_pii(raw_text)

        # Verify all Indian PII entities are stripped
        self.assertNotIn("5432 8765 4321", scrubbed)
        self.assertNotIn("98765 43210", scrubbed)
        self.assertNotIn("ramesh@kisan.gov.in", scrubbed)
        self.assertNotIn("Ramesh Patel", scrubbed)
        self.assertNotIn("28.6139, 77.2090", scrubbed)

        # Verify appropriate replacement tokens
        self.assertIn("[REDACTED_AADHAAR]", scrubbed)
        self.assertIn("[REDACTED_PHONE]", scrubbed)
        self.assertIn("[REDACTED_EMAIL]", scrubbed)
        self.assertIn("[REDACTED_NAME]", scrubbed)
        self.assertIn("[REDACTED_COORDINATES]", scrubbed)

    def test_04_tool_endpoints(self):
        """Verify that the sovereign tools are callable directly via the Gateway."""
        # Tool 1: Crop Disease Lookup
        res_lookup = self.client.post(
            "/v1/tools/crop_disease_lookup",
            json={"crop_name": "Wheat", "symptoms": "rust pustules on stems"},
            headers=self.valid_headers
        )
        self.assertEqual(res_lookup.status_code, 200)
        data_lookup = res_lookup.json()
        self.assertIn("Wheat Rust", data_lookup["disease_name"])
        self.assertTrue(len(data_lookup["organic_treatments"]) > 0)

        # Tool 2: Weather Call
        res_weather = self.client.post(
            "/v1/tools/weather_call",
            json={"location": "Punjab District Farm A"},
            headers=self.valid_headers
        )
        self.assertEqual(res_weather.status_code, 200)
        data_weather = res_weather.json()
        self.assertIn("temperature_c", data_weather)
        self.assertIn("spore_germination_risk", data_weather)

if __name__ == "__main__":
    unittest.main()

