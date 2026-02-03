"""
Merge all CSV datasets and generate scam patterns
Step 1: Merge spam_ham_india.csv + uci_sms_spam.csv
Step 2: Extract spam patterns
Step 3: Save to scam_patterns.json
"""
import csv
import re
import json
import hashlib
import sys
from pathlib import Path

# Paths
DATASET_DIR = Path(r"c:\Users\MIMANGSHA\scam_datasets")
OUTPUT_PATH = Path(r"c:\Users\MIMANGSHA\.gemini\antigravity\playground\pulsing-apollo\data\scam_patterns.json")
MERGED_FILE = DATASET_DIR / "merged_spam.csv"

# Scam category keywords
CATEGORY_KEYWORDS = {
    "banking": ["bank", "account", "kyc", "blocked", "suspended", "verify", "sbi", "hdfc", "icici", "axis", "credit", "debit", "freeze", "pan", "upi", "loan", "emi"],
    "prize": ["won", "winner", "prize", "lottery", "congratulations", "claim", "reward", "lakhs", "crore", "lucky", "draw", "gift", "bonus", "cash", "guaranteed"],
    "job": ["job", "work from home", "wfh", "salary", "hiring", "vacancy", "earn", "income", "daily payment", "part-time", "parttime", "amazon", "flipkart"],
    "tech_support": ["virus", "computer", "support", "microsoft", "alert", "security", "login", "password", "suspicious", "locked"],
    "financial": ["investment", "stock", "trading", "forex", "crypto", "bitcoin", "cashback", "offer", "interest", "free", "discount"],
    "telecom": ["recharge", "data", "unlimited", "sim", "mobile", "airtel", "jio", "vi", "vodafone", "5g", "pack", "gb", "valid", "ringtone"]
}

def categorize_message(text):
    """Categorize message and return (category, confidence)"""
    text_lower = text.lower()
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[category] = score
    if not scores:
        return ("general", 70)
    best_cat = max(scores, key=scores.get)
    confidence = min(70 + scores[best_cat] * 8, 98)
    return (best_cat, confidence)

def create_fingerprint(text):
    """Create normalized fingerprint for matching"""
    text = text.lower().strip()
    text = re.sub(r'http\S+|www\.\S+|bit\.ly/\S+', 'URL', text)
    text = re.sub(r'\d+', 'NUM', text)
    text = re.sub(r'[^a-z\s]', '', text)
    words = text.split()
    stopwords = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'to', 'from', 'for', 'and', 'or', 'in', 'on', 'at', 'by', 'of', 'with', 'you', 'your', 'our', 'we', 'this', 'that', 'it', 'be', 'has', 'have', 'will', 'can', 'get', 'now'}
    words = [w for w in words if w not in stopwords and len(w) > 2]
    return ' '.join(sorted(set(words)))

def merge_datasets():
    """Merge all spam messages into one file"""
    print("=" * 50, flush=True)
    print("Step 1: Merging datasets...", flush=True)
    
    all_spam = []
    
    # Process spam_ham_india.csv (Msg,Label format)
    india_csv = DATASET_DIR / "spam_ham_india.csv"
    if india_csv.exists():
        print(f"  Reading: {india_csv.name}", flush=True)
        with open(india_csv, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                label = row.get('Label', '').strip().lower()
                if label == 'spam':
                    msg = row.get('Msg', '').strip()
                    if len(msg) > 20:
                        all_spam.append(msg)
                        count += 1
            print(f"    Found {count} spam messages", flush=True)
    
    # Process uci_sms_spam.csv (label<tab>message format)
    uci_csv = DATASET_DIR / "uci_sms_spam.csv"
    if uci_csv.exists():
        print(f"  Reading: {uci_csv.name}", flush=True)
        with open(uci_csv, 'r', encoding='utf-8', errors='ignore') as f:
            count = 0
            for line in f:
                line = line.strip()
                if line.startswith('spam\t'):
                    msg = line[5:]  # Remove 'spam\t'
                    if len(msg) > 20:
                        all_spam.append(msg)
                        count += 1
            print(f"    Found {count} spam messages", flush=True)
    
    # Save merged file
    with open(MERGED_FILE, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['message'])
        for msg in all_spam:
            writer.writerow([msg])
    
    print(f"  Total spam messages merged: {len(all_spam)}", flush=True)
    return all_spam

def process_patterns(spam_messages):
    """Generate patterns from spam messages"""
    print("\nStep 2: Generating patterns...", flush=True)
    
    patterns = {}
    for msg in spam_messages:
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
            }
    
    # Add manual high-quality patterns
    manual = {
        "MANUAL_BANK_1": {"category": "banking", "confidence": 98, "fingerprint": "account bank blocked kyc verify immediately", "sample": "Your bank account blocked. Verify KYC immediately."},
        "MANUAL_BANK_2": {"category": "banking", "confidence": 97, "fingerprint": "account alert pan sbi suspended update", "sample": "SBI Alert: Account suspended. Update PAN now."},
        "MANUAL_PRIZE_1": {"category": "prize", "confidence": 99, "fingerprint": "congratulations kbc lakhs lottery won", "sample": "Congratulations! You won 25 Lakhs in KBC Lottery!"},
        "MANUAL_JOB_1": {"category": "job", "confidence": 95, "fingerprint": "daily home job offer parttime payment work", "sample": "Part-time job offer. Daily payment Rs 5000."},
    }
    patterns.update(manual)
    
    print(f"  Generated {len(patterns)} unique patterns", flush=True)
    return patterns

def save_patterns(patterns):
    """Save patterns to JSON file"""
    print("\nStep 3: Saving patterns...", flush=True)
    
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(patterns, f, indent=2, ensure_ascii=False)
    
    print(f"  Saved to: {OUTPUT_PATH}", flush=True)
    
    # Category distribution
    categories = {}
    for p in patterns.values():
        cat = p["category"]
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\n📊 Category Distribution:", flush=True)
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"   {cat}: {count}", flush=True)

def main():
    try:
        spam_messages = merge_datasets()
        patterns = process_patterns(spam_messages)
        save_patterns(patterns)
        print("\n✅ SUCCESS! Pattern database updated.", flush=True)
    except Exception as e:
        print(f"\n❌ ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
