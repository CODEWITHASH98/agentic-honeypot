import asyncio
import sys
import os
import time
from typing import Tuple

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import app modules
# We need to mock redis if it tries to connect on import, but state_manager connects lazily.
# detection.py imports groq_client, which might try to load env vars.
from app.detection import detection_pipeline
from app.extraction import extraction_pipeline

async def test_performance_flow():
    print("Testing pipeline flow...")
    message = "Urgent! Click this link http://bit.ly/scam to win 1000$ and send money to upi@okaxis"
    
    start = time.time()
    
    # 4 & 5. Detection and Extraction (Parallel)
    # This exactly mimics the logic in main.py
    print("Starting parallel tasks...")
    detection_task = detection_pipeline.detect(message)
    extraction_task = extraction_pipeline.extract(message)
    
    results: Tuple = await asyncio.gather(detection_task, extraction_task)
    detection_result, extraction_result = results
    
    end = time.time()
    
    print(f"Execution took: {(end - start)*1000:.2f}ms")
    print(f"Detection: Is Scam? {detection_result.is_scam}")
    print(f"Extraction: URLs found: {len(extraction_result.urls)}")
    print(f"Extraction: UPIS found: {len(extraction_result.upi_ids)}")
    
    assert len(extraction_result.urls) > 0
    assert len(extraction_result.upi_ids) > 0
    
    # Cleanup
    await extraction_pipeline.close()
    print("Test passed!")

if __name__ == "__main__":
    asyncio.run(test_performance_flow())
