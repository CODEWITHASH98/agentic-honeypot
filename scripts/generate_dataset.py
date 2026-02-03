import json
import hashlib
import re

def normalize(text):
    """Normalize text for fingerprinting"""
    # Lowercase
    text = text.lower()
    # Remove numbers
    text = re.sub(r'\d+', 'NUM', text)
    # Remove special chars
    text = re.sub(r'[^\w\s]', '', text)
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def create_fingerprint(text):
    """Create sorted unique word fingerprint"""
    words = sorted(set(normalize(text).split()))
    return " ".join(words)

def create_hash(fingerprint):
    """Create MD5 hash of fingerprint"""
    return hashlib.md5(fingerprint.encode()).hexdigest()

PATTERNS = [
    # Banking Fraud
    {"text": "Your bank account has been blocked. Click here to verify KYC.", "category": "banking", "confidence": 95},
    {"text": "Alert: Your SBI account is suspended. Update PAN number immediately.", "category": "banking", "confidence": 95},
    {"text": "Dear customer, your HDFC debit card points expiring soon. Redeem now.", "category": "banking", "confidence": 90},
    {"text": "K.Y.C pending. Account will be freezed. Call manager.", "category": "banking", "confidence": 92},
    
    # Job Scams
    {"text": "Part-time job offer. Daily payment Rs 5000. Work from home.", "category": "job", "confidence": 88},
    {"text": "Hiring for Amazon data entry. No experience needed. WhatsApp now.", "category": "job", "confidence": 90},
    {"text": "Congratulations! You are selected for WFH job. Salary 50k/month.", "category": "job", "confidence": 85},
    
    # Prize/Lottery
    {"text": "You won 25 Lakhs in KBC lottery. Contact Rana Pratap Singh.", "category": "prize", "confidence": 98},
    {"text": "Lucky Draw Winner! Your number matches first prize. Claim reward.", "category": "prize", "confidence": 95},
    {"text": "Congratulations! You won a Tata Safari car. Pay registration fee.", "category": "prize", "confidence": 92},

    # Tech Support
    {"text": "Your computer has a virus. Call Microsoft support immediately.", "category": "tech_support", "confidence": 85},
    {"text": "Security Alert: Suspicious login detected. Verify identity.", "category": "tech_support", "confidence": 80},
]

def generate_dataset():
    dataset = {}
    
    print(f"Generating patterns from {len(PATTERNS)} templates...")
    
    for template in PATTERNS:
        fingerprint = create_fingerprint(template["text"])
        pattern_hash = create_hash(fingerprint)
        
        dataset[pattern_hash] = {
            "category": template["category"],
            "confidence": template["confidence"],
            "raw_text": template["text"],
            "fingerprint": fingerprint
        }
        
    # Manual Additions for Variation
    dataset["MANUAL_1"] = {"category": "banking", "confidence": 95, "fingerprint": "account bank blocked kyc verify num"}
    dataset["MANUAL_2"] = {"category": "job", "confidence": 90, "fingerprint": "daily home job num parttime payment work"}
    
    with open("data/scam_patterns.json", "w") as f:
        json.dump(dataset, f, indent=2)
        
    print(f"Successfully created data/scam_patterns.json with {len(dataset)} entries.")

if __name__ == "__main__":
    generate_dataset()
