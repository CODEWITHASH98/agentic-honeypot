from fastapi.testclient import TestClient
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app, settings

client = TestClient(app)

def test_api_security():
    print("Testing Security...")
    
    # 1. No Header -> Should Fail
    response = client.post(
        "/api/v1/scam-analysis",
        json={"conversation_id": "test", "message": "hi"}
    )
    assert response.status_code == 401
    print("[SUCCESS] Rejected request without API Key")
    
    # 2. Wrong Header -> Should Fail
    response = client.post(
        "/api/v1/scam-analysis",
        json={"conversation_id": "test", "message": "hi"},
        headers={"x-api-key": "wrong-key"}
    )
    assert response.status_code == 401
    print("[SUCCESS] Rejected request with wrong API Key")

def test_api_success():
    print("Testing Success Flow...")
    
    # 3. Correct Header -> Should Pass (mocking internal logic mostly via normal flow)
    # Note: We expect 200 OK. Detection might run fully.
    
    payload = {
        "conversation_id": "e2e-test-123",
        "message": "Hello, I received a message about a lottery win.", 
        "session_metadata": {"source": "test"}
    }
    
    response = client.post(
        "/api/v1/scam-analysis",
        json=payload,
        headers={"x-api-key": settings.API_SECRET_KEY}
    )
    
    if response.status_code != 200:
        print(f"[FAILURE] Response: {response.text}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["conversation_id"] == "e2e-test-123"
    assert "detection" in data
    assert "agent_response" in data
    print(f"[SUCCESS] API returned valid response: {data['detection']['confidence']}% confidence")

if __name__ == "__main__":
    test_api_security()
    test_api_success()
