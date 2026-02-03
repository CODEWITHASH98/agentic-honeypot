"""
Process Scam Datasets - Generate 1000+ patterns for Tier 2 validation
Processes: spam_ham_india.csv, uci_sms_spam.tsv
"""
import csv
import re
import json
import hashlib
from pathlib import Path

# Paths
DATASET_DIR = Path(r"c:\Users\MIMANGSHA\scam_datasets")
OUTPUT_PATH = Path(r"c:\Users\MIMANGSHA\.gemini\antigravity\playground\pulsing-apollo\data\scam_patterns.json")

# Scam category keywords
CATEGORY_KEYWORDS = {
    "banking": ["bank", "account", "kyc", "blocked", "suspended", "verify", "sbi", "hdfc", "icici", "axis", "credit", "debit", "freeze", "pan", "upi", "loan", "emi"],
    "prize": ["won", "winner", "prize", "lottery", "congratulations", "claim", "reward", "lakhs", "crore", "lucky", "draw", "gift", "bonus"],
    "job": ["job", "work from home", "wfh", "salary", "hiring", "vacancy", "earn", "income", "daily payment", "part-time", "parttime", "amazon", "flipkart"],
    "tech_support": ["virus", "computer", "support", "microsoft", "alert", "security", "login", "password", "suspicious", "locked"],
    "financial": ["investment", "stock", "trading", "forex", "crypto", "bitcoin", "cashback", "offer", "interest", "free", "discount"],
    "telecom": ["recharge", "data", "unlimited", "sim", "mobile", "airtel", "jio", "vi", "vodafone", "5g", "pack", "gb", "valid"]
}

def categorize_message(text: str) -> tuple:
    """Categorize message and return (category, confidence)"""
    text_lower = text.lower()
    
    # Count matches per category
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[category] = score
    
    if not scores:
        return ("general", 70)
    
    # Return highest scoring category
    best_cat = max(scores, key=scores.get)
    confidence = min(70 + scores[best_cat] * 8, 98)
    return (best_cat, confidence)

def create_fingerprint(text: str) -> str:
    """Create normalized fingerprint for matching"""
    # Normalize
    text = text.lower().strip()
    # Remove URLs
    text = re.sub(r'http\S+|www\.\S+|bit\.ly/\S+', 'URL', text)
    # Replace numbers with NUM
    text = re.sub(r'\d+', 'NUM', text)
    # Remove special chars, keep letters and spaces
    text = re.sub(r'[^a-z\s]', '', text)
    # Tokenize
    words = text.split()
    # Remove stopwords
    stopwords = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'to', 'from', 'for', 'and', 'or', 'in', 'on', 'at', 'by', 'of', 'with', 'you', 'your', 'our', 'we', 'this', 'that', 'it', 'be', 'has', 'have', 'will', 'can', 'get', 'now'}
    words = [w for w in words if w not in stopwords and len(w) > 2]
    # Return sorted unique words
    return ' '.join(sorted(set(words)))

def process_india_csv():
    """Process spam_ham_india.csv"""
    patterns = {}
    csv_path = DATASET_DIR / "spam_ham_india.csv"
    
    if not csv_path.exists():
        print(f"File not found: {csv_path}")
        return patterns
    
    print(f"Processing: {csv_path}")
    
    with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('Label', '').strip().lower() != 'spam':
                continue
            
            msg = row.get('Msg', '').strip()
            if len(msg) < 20:
                continue
            
            fingerprint = create_fingerprint(msg)
            if len(fingerprint.split()) < 3:
                continue
            
            hash_id = hashlib.md5(fingerprint.encode()).hexdigest()[:16]
            
            if hash_id not in patterns:
                category, confidence = categorize_message(msg)
                patterns[hash_id] = {
                    "category": category,
                    "confidence": confidence,
                    "fingerprint": fingerprint,
                    "sample": msg[:100] + "..." if len(msg) > 100 else msg,
                    "source": "india_csv"
                }
    
    print(f"  Found {len(patterns)} spam patterns")
    return patterns

def process_uci_tsv():
    """Process uci_sms_spam.tsv"""
    patterns = {}
    tsv_path = DATASET_DIR / "uci_sms_spam.csv"
    
    if not tsv_path.exists():
        print(f"File not found: {tsv_path}")
        return patterns
    
    print(f"Processing: {tsv_path}")
    
    with open(tsv_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split('\t', 1)
            if len(parts) < 2:
                continue
            
            label, msg = parts
            if label.lower() != 'spam':
                continue
            
            if len(msg) < 20:
                continue
            
            fingerprint = create_fingerprint(msg)
            if len(fingerprint.split()) < 3:
                continue
            
            hash_id = hashlib.md5(fingerprint.encode()).hexdigest()[:16]
            
            if hash_id not in patterns:
                category, confidence = categorize_message(msg)
                patterns[hash_id] = {
                    "category": category,
                    "confidence": confidence,
                    "fingerprint": fingerprint,
                    "sample": msg[:100] + "..." if len(msg) > 100 else msg,
                    "source": "uci_tsv"
                }
    
    print(f"  Found {len(patterns)} spam patterns")
    return patterns

def add_manual_patterns():
    """Add high-quality manual Indian scam patterns"""
    return {
        "MANUAL_BANK_1": {"category": "banking", "confidence": 98, "fingerprint": "account bank blocked kyc verify immediately", "sample": "Your bank account blocked. Verify KYC immediately.", "source": "manual"},
        "MANUAL_BANK_2": {"category": "banking", "confidence": 97, "fingerprint": "account alert pan sbi suspended update", "sample": "SBI Alert: Your account suspended. Update PAN now.", "source": "manual"},
        "MANUAL_PRIZE_1": {"category": "prize", "confidence": 99, "fingerprint": "congratulations kbc lakhs lottery won", "sample": "Congratulations! You won 25 Lakhs in KBC Lottery!", "source": "manual"},
        "MANUAL_PRIZE_2": {"category": "prize", "confidence": 98, "fingerprint": "claim draw lucky prize winner", "sample": "Lucky Draw Winner! Claim your prize now!", "source": "manual"},
        "MANUAL_JOB_1": {"category": "job", "confidence": 95, "fingerprint": "daily home job offer parttime payment work", "sample": "Part-time job offer. Daily payment Rs 5000. Work from home.", "source": "manual"},
        "MANUAL_JOB_2": {"category": "job", "confidence": 93, "fingerprint": "amazon data entry hiring salary whatsapp", "sample": "Hiring for Amazon data entry. WhatsApp now.", "source": "manual"},
        "MANUAL_OTP_1": {"category": "banking", "confidence": 99, "fingerprint": "otp share transaction valid", "sample": "Your OTP is 123456. Do not share with anyone.", "source": "manual"},
        "MANUAL_UPI_1": {"category": "banking", "confidence": 98, "fingerprint": "failed gpay pending request upi paytm", "sample": "Your UPI request pending. Approve now.", "source": "manual"},
    }

def main():
    print("=" * 50)
    print("Scam Pattern Generator v2.0")
    print("=" * 50)
    
    all_patterns = {}
    
    # Process datasets
    all_patterns.update(process_india_csv())
    all_patterns.update(process_uci_tsv())
    
    # Add manual patterns
    all_patterns.update(add_manual_patterns())
    
    # Save to JSON
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(all_patterns, f, indent=2, ensure_ascii=False)
    
    print("=" * 50)
    print(f"✅ Total patterns generated: {len(all_patterns)}")
    print(f"📁 Saved to: {OUTPUT_PATH}")
    
    # Print category distribution
    categories = {}
    sources = {}
    for p in all_patterns.values():
        cat = p["category"]
        src = p["source"]
        categories[cat] = categories.get(cat, 0) + 1
        sources[src] = sources.get(src, 0) + 1
    
    print("\n📊 Category Distribution:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"   {cat}: {count}")
    
    print("\n📦 Source Distribution:")
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"   {src}: {count}")

if __name__ == "__main__":
    main()
