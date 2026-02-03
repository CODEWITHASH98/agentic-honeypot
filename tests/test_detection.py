import asyncio
import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.detection import detection_pipeline

async def test_detection_tiers():
    print("Testing Detection Tiers...")
    
    # Mock Groq Client
    with patch("app.groq_client.groq_client.analyze_scam") as mock_analyze, \
         patch("app.groq_client.groq_client.validate_detection") as mock_validate:
        
        # Scenario 1: Agreement (Both say Scam)
        mock_analyze.return_value = {"is_scam": True, "confidence": 85, "scam_type": "job"}
        mock_validate.return_value = {"is_scam": True, "confidence": 90}
        
        # Message that triggers Rule-based score around 60-70 to activate LLM
        # "urgent" (20) + "job" (25) + "salary" (25) = 70 base score using rules
        message = "Urgent job offer with high salary"
        
        result = await detection_pipeline.detect(message)
        
        print(f"Scenario 1 Result: {result.confidence} | Reasoning: {result.reasoning}")
        assert result.confidence > 85
        assert "T4-Valid:+" in result.reasoning
        print("[SUCCESS] Tier 4 Boosted Confidence")

        # Scenario 2: Disagreement (T3 says Scam, T4 says Safe)
        mock_analyze.return_value = {"is_scam": True, "confidence": 80, "scam_type": "job"}
        mock_validate.return_value = {"is_scam": False, "confidence": 90}  # Validator says safe
        
        result_disagree = await detection_pipeline.detect(message)
        
        print(f"Scenario 2 Result: {result_disagree.confidence} | Reasoning: {result_disagree.reasoning}")
        assert result_disagree.confidence < 80
        assert "Disagree" in result_disagree.reasoning
        print("[SUCCESS] Tier 4 Penalized Confidence")

if __name__ == "__main__":
    asyncio.run(test_detection_tiers())
