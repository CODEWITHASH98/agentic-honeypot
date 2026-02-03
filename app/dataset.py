import json
import hashlib
import re
import os
from typing import Optional, Dict

class DatasetValidator:
    def __init__(self):
        self.dataset = {}
        self.load_dataset()

    def load_dataset(self):
        """Load scam patterns from JSON file"""
        try:
            file_path = os.path.join("data", "scam_patterns.json")
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    self.dataset = json.load(f)
                print(f"Loaded {len(self.dataset)} scam patterns.")
            else:
                print("Warning: data/scam_patterns.json not found.")
        except Exception as e:
            print(f"Failed to load dataset: {e}")

    def validate(self, message: str) -> Optional[Dict]:
        """Check if message matches any known scam pattern"""
        try:
            fingerprint = self._create_fingerprint(message)
            pattern_hash = self._create_hash(fingerprint)
            
            # 1. Exact Match via Hash
            if pattern_hash in self.dataset:
                match = self.dataset[pattern_hash]
                return {
                    "is_match": True,
                    "confidence": match["confidence"],
                    "category": match["category"],
                    "source": "dataset_exact_match"
                }

            # 2. Fuzzy Match (Partial Fingerprint overlap)
            # This is O(N) but fast for N < 10000. For production use Elasticsearch.
            msg_tokens = set(fingerprint.split())
            best_match = None
            max_overlap = 0

            for key, data in self.dataset.items():
                pattern_tokens = set(data.get("fingerprint", "").split())
                if not pattern_tokens: continue
                
                intersection = msg_tokens.intersection(pattern_tokens)
                overlap_ratio = len(intersection) / len(pattern_tokens)
                
                if overlap_ratio > 0.8:  # 80% similarity threshold
                    if overlap_ratio > max_overlap:
                        max_overlap = overlap_ratio
                        best_match = data

            if best_match:
                return {
                    "is_match": True,
                    "confidence": int(best_match["confidence"] * 0.9),  # penalty for fuzzy
                    "category": best_match["category"],
                    "source": "dataset_fuzzy_match"
                }

        except Exception as e:
            print(f"Validation error: {e}")
            
        return None

    def _create_fingerprint(self, text):
        """Normalize text for fingerprinting"""
        text = text.lower()
        text = re.sub(r'\d+', 'NUM', text)
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        words = sorted(set(text.split()))
        return " ".join(words)

    def _create_hash(self, fingerprint):
        """Create MD5 hash of fingerprint"""
        return hashlib.md5(fingerprint.encode()).hexdigest()

dataset_validator = DatasetValidator()
