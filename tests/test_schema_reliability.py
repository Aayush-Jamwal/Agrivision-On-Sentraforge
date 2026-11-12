import os
import sys
import json
import unittest
from typing import List, Dict, Any

# Ensure AgriVision-Disease-Guard is in python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.schemas import (
    DiagnosticianOutput,
    StrategyBrokerOutput,
    AgriVisionAdvisory,
    CropDiseaseLookupInput,
    CropDiseaseLookupOutput,
    WeatherCallInput,
    WeatherCallOutput
)
from agents.workflow import resolve_pathology
from tools.mcp_tools import crop_disease_lookup, weather_call
from utils.security import BANNED_CHEMICALS

class TestSchemaReliability(unittest.TestCase):
    """
    Sovereign AI Schema Reliability Test Suite.
    Executes repeated batch iterations against Pydantic schemas to prove
    0% schema failure rate and strict constraint compliance.
    """

    def setUp(self):
        # Diverse set of test pathology scenarios
        self.scenarios = [
            ("Tomato", "Lower leaves show dark brown spots with yellow halos. Papery margins with fuzzy white undersides."),
            ("Wheat", "Orange, powdery rust-like pustules have formed in neat lines along leaf sheaths and stems."),
            ("Citrus", "The leaves are mottled yellow asynchronously. Fruit is lopsided, small, and bitter."),
            ("Potato", "Dark water-soaked lesions expanding rapidly across foliage after heavy monsoon rains."),
            ("Tomato", "Circular spots with dark brown margins and sunken centers observed predominantly on lower canopy."),
            ("Barley", "Orange and brown powdery pustules scattered across lower leaf blades."),
            ("Citrus", "Foliar blotchy mottle with narrow upright leaves."),
            ("Cucurbits", "Leaf surface displays white powdery fungal mycelium patches in shaded canopy."),
            ("Wheat", "Powdery white fungal coating spreading over wheat leaf surface."),
            ("Tomato", "Fuzzy white underside with black lesions after humid weather.")
        ]

    def test_01_vllm_guided_json_schema_validity(self):
        """Verify that all Pydantic schemas export valid JSON Schemas for vLLM guided decoding."""
        schemas = [
            ("DiagnosticianOutput", DiagnosticianOutput.model_json_schema()),
            ("StrategyBrokerOutput", StrategyBrokerOutput.model_json_schema()),
            ("AgriVisionAdvisory", AgriVisionAdvisory.model_json_schema()),
            ("CropDiseaseLookupOutput", CropDiseaseLookupOutput.model_json_schema()),
            ("WeatherCallOutput", WeatherCallOutput.model_json_schema())
        ]
        
        for name, schema in schemas:
            self.assertIsInstance(schema, dict, f"Schema {name} is not a dict")
            self.assertIn("properties", schema, f"Schema {name} lacks properties")
            self.assertIn("type", schema, f"Schema {name} lacks type definition")
            self.assertEqual(schema["type"], "object", f"Schema {name} type is not object")
            # Verify serialization
            json_str = json.dumps(schema)
            self.assertTrue(len(json_str) > 0)
        print("\n[OK] All vLLM guided_json schemas are structurally valid.")

    def test_02_repeated_batch_schema_validation(self):
        """
        Executes a 20-iteration batch test across multiple crops and symptom combinations.
        Proves 100% schema reliability (0 validation errors).
        """
        total_iterations = 20
        validation_errors = 0
        successful_parses = 0

        print(f"\n[START] Executing {total_iterations} repeated iterations for schema reliability...")

        for i in range(total_iterations):
            crop, symptoms = self.scenarios[i % len(self.scenarios)]
            
            # 1. Execute Weather Call Tool
            weather_out = weather_call(location=f"Field {i+1}, Zone-{chr(65 + (i % 6))}")
            weather_pydantic = WeatherCallOutput(**weather_out)
            self.assertIsInstance(weather_pydantic.temperature_c, float)
            self.assertIn(weather_pydantic.spore_germination_risk, ["Low", "Medium", "High"])

            # 2. Execute Pathology Reasoning Engine
            try:
                diag_obj = resolve_pathology(crop, symptoms, weather_out, is_fallback=False)
                # Verify raw JSON dump and re-validation
                json_dump = diag_obj.model_dump_json()
                revalidated = DiagnosticianOutput.model_validate_json(json_dump)
                
                # Check strict range constraints
                self.assertTrue(0.0 <= revalidated.confidence <= 100.0)
                self.assertIn(revalidated.severity, ["Low", "Medium", "High"])
                self.assertTrue(len(revalidated.disease_name) > 0)
                self.assertTrue(len(revalidated.reasoning) > 0)
            except Exception as e:
                validation_errors += 1
                self.fail(f"DiagnosticianOutput schema validation failed on iteration {i}: {e}")

            # 3. Execute Crop Disease Lookup Tool
            tool_out = crop_disease_lookup(crop_name=crop, symptoms=symptoms, disease_name=diag_obj.disease_name)
            tool_pydantic = CropDiseaseLookupOutput(**tool_out)
            self.assertTrue(len(tool_pydantic.organic_treatments) > 0)

            # 4. Validate Master AgriVisionAdvisory Schema
            try:
                advisory_data = {
                    "crop_name": crop,
                    "diagnosed_condition": diag_obj.disease_name,
                    "confidence": diag_obj.confidence,
                    "severity": diag_obj.severity,
                    "reasoning": diag_obj.reasoning,
                    "weather_assessment": f"Temperature {weather_out['temperature_c']}C with {weather_out['relative_humidity_pct']}% RH.",
                    "organic_treatments": tool_pydantic.organic_treatments,
                    "cultural_practices": tool_pydantic.cultural_practices,
                    "safety_compliance": "APPROVED: 100% Bio-UDA Certified",
                    "warnings": tool_pydantic.warnings
                }
                advisory_obj = AgriVisionAdvisory.model_validate(advisory_data)
                self.assertEqual(advisory_obj.crop_name, crop)
                self.assertIn(advisory_obj.severity, ["Low", "Medium", "High"])
                
                # Check zero banned chemicals in treatments
                for treatment in advisory_obj.organic_treatments:
                    for banned in BANNED_CHEMICALS:
                        self.assertNotIn(banned, treatment.lower(), f"Banned chemical {banned} detected in {treatment}")
                
                successful_parses += 1
            except Exception as e:
                validation_errors += 1
                self.fail(f"AgriVisionAdvisory schema validation failed on iteration {i}: {e}")

        self.assertEqual(validation_errors, 0, f"Expected 0 validation errors, got {validation_errors}")
        self.assertEqual(successful_parses, total_iterations)
        print(f"[PASSED] {successful_parses}/{total_iterations} iterations validated successfully (100% schema reliability, 0 errors).")

    def test_03_invalid_payload_rejection(self):
        """Verifies that Pydantic properly rejects out-of-range or malformed payloads."""
        # 1. Invalid confidence > 100.0
        with self.assertRaises(Exception):
            DiagnosticianOutput(
                disease_name="Late Blight",
                confidence=125.0,  # Invalid: > 100.0
                severity="High",
                reasoning="Test"
            )

        # 2. Invalid severity
        with self.assertRaises(Exception):
            DiagnosticianOutput(
                disease_name="Late Blight",
                confidence=85.0,
                severity="Critical",  # Invalid: not in Literal["Low", "Medium", "High"]
                reasoning="Test"
            )

if __name__ == "__main__":
    unittest.main()

