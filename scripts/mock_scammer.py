import requests
import uuid
import time
import json

BASE_URL = "http://localhost:8000/api/v1/scam-analysis"

def test_banking_scam():
    conversation_id = f"test-{uuid.uuid4()}"
    print(f"Testing Conversation: {conversation_id}")
    
    messages = [
        "Urgent! Your bank account 123456789012 is blocked. Click http://bit.ly/scam to verify.",
        "Please send the OTP to unblock.",
        "You need to transfer ₹1000 to verify@upi for verification."
    ]
    
    history = []
    
    for i, content in enumerate(messages):
        print(f"\n--- Turn {i+1} ---")
        print(f"Scammer: {content}")
        
        msg_obj = {
            "sender": "scammer",
            "content": content,
            "timestamp": str(time.time())
        }
        history.append(msg_obj)
        
        payload = {
            "conversation_id": conversation_id,
            "messages": history,
            "session_metadata": {
                "source": "whatsapp",
                "session_start": str(time.time())
            }
        }
        
        try:
            start = time.time()
            response = requests.post(BASE_URL, json=payload, headers={"X-API-Key": "test"})
            duration = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                agent_msg = data["agent_response"]["message"]
                print(f"Agent ({data['agent_response']['strategy']}): {agent_msg}")
                print(f"Detection Score: {data['detection']['confidence']}")
                print(f"Scam Type: {data['detection']['scam_type']}")
                print(f"Extracted: {data['extracted_intelligence']['upi_ids']}")
                print(f"Latency: {int(duration)}ms")
                
                # Add agent response to history for next turn (client-side simulation)
                history.append({
                    "sender": "agent",
                    "content": agent_msg,
                    "timestamp": str(time.time())
                })
            else:
                print(f"Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Request failed: {e}")
            break

if __name__ == "__main__":
    # Wait for server to start if running via automated script
    time.sleep(2)
    test_banking_scam()
