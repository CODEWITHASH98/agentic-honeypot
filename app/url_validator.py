"""
URL Validator Module - Phishing URL Detection

This module validates URLs against known phishing patterns, suspicious TLDs,
and a blacklist of known malicious domains.
"""

import json
import os
import re
from typing import Dict, List, Optional
from urllib.parse import urlparse


class URLValidator:
    """
    Validates URLs against phishing patterns and blacklists.
    
    Uses multiple detection methods:
    1. Domain blacklist matching
    2. Suspicious TLD detection
    3. Suspicious keyword matching
    4. Suspicious hosting pattern detection
    5. Typosquatting detection for popular brands
    """
    
    def __init__(self):
        self.blacklist_data = {}
        self.load_blacklist()
        
        # Popular brands for typosquatting detection
        self.popular_brands = [
            "google", "facebook", "amazon", "apple", "microsoft",
            "netflix", "paypal", "ebay", "instagram", "twitter",
            "linkedin", "whatsapp", "tiktok", "spotify", "uber",
            "airbnb", "dropbox", "zoom", "slack", "github",
            "chase", "wellsfargo", "bankofamerica", "citibank", "capitalone",
            "amex", "discover", "usbank", "pnc", "tdbank"
        ]
        
    def load_blacklist(self):
        """Load URL blacklist from JSON file"""
        try:
            file_path = os.path.join("data", "url_blacklist.json")
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    self.blacklist_data = json.load(f)
                print(f"Loaded URL blacklist: {len(self.blacklist_data.get('blacklisted_domains', []))} domains, "
                      f"{len(self.blacklist_data.get('suspicious_patterns', []))} patterns")
            else:
                print("Warning: data/url_blacklist.json not found. Using defaults.")
                self._set_defaults()
        except Exception as e:
            print(f"Failed to load URL blacklist: {e}")
            self._set_defaults()
            
    def _set_defaults(self):
        """Set default suspicious patterns"""
        self.blacklist_data = {
            "suspicious_patterns": [
                "godaddysites.com", "weebly.com", "wcomhost.com",
                "azurewebsites.net", "ngrok.io", "16mb.com"
            ],
            "suspicious_tlds": [
                ".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top", ".pw"
            ],
            "suspicious_keywords": [
                "login", "signin", "verify", "confirm", "secure", "account", "update"
            ],
            "blacklisted_domains": []
        }
        
    def validate(self, url: str) -> Dict:
        """
        Validate a URL for phishing indicators.
        
        Args:
            url: The URL to validate
            
        Returns:
            Dict with is_suspicious, confidence, reasons, and category
        """
        if not url:
            return {"is_suspicious": False, "confidence": 0, "reasons": [], "category": None}
            
        # Normalize URL
        url = url.lower().strip()
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
            
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            full_url = url
        except Exception:
            return {"is_suspicious": True, "confidence": 50, "reasons": ["Invalid URL format"], "category": "malformed"}
            
        reasons = []
        total_score = 0
        category = None
        
        # Check 1: Exact domain blacklist match
        if domain in self.blacklist_data.get("blacklisted_domains", []):
            reasons.append("Domain in blacklist")
            total_score += 100
            category = "blacklisted"
            
        # Check 2: Suspicious TLD
        for tld in self.blacklist_data.get("suspicious_tlds", []):
            if domain.endswith(tld):
                reasons.append(f"Suspicious TLD: {tld}")
                total_score += 30
                category = category or "suspicious_tld"
                break
                
        # Check 3: Suspicious hosting patterns
        for pattern in self.blacklist_data.get("suspicious_patterns", []):
            if pattern in domain:
                reasons.append(f"Suspicious hosting: {pattern}")
                total_score += 40
                category = category or "suspicious_host"
                break
                
        # Check 4: Suspicious keywords in URL
        keywords_found = []
        for keyword in self.blacklist_data.get("suspicious_keywords", []):
            if keyword in full_url:
                keywords_found.append(keyword)
        if keywords_found:
            reasons.append(f"Suspicious keywords: {', '.join(keywords_found[:3])}")
            total_score += min(10 * len(keywords_found), 30)
            category = category or "suspicious_content"
            
        # Check 5: Typosquatting detection
        typosquat_matches = self._detect_typosquatting(domain)
        if typosquat_matches:
            reasons.append(f"Possible typosquatting: {', '.join(typosquat_matches)}")
            total_score += 50
            category = category or "typosquatting"
            
        # Check 6: IP address as domain
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', domain):
            reasons.append("IP address used as domain")
            total_score += 40
            category = category or "ip_domain"
            
        # Check 7: Excessive subdomains
        subdomain_count = domain.count('.')
        if subdomain_count > 3:
            reasons.append(f"Excessive subdomains ({subdomain_count})")
            total_score += 20
            category = category or "subdomain_abuse"
            
        # Check 8: Very long domain name
        if len(domain) > 50:
            reasons.append(f"Unusually long domain ({len(domain)} chars)")
            total_score += 15
            category = category or "obfuscation"
            
        # Cap confidence at 100
        confidence = min(total_score, 100)
        
        return {
            "is_suspicious": confidence >= 30,
            "confidence": confidence,
            "reasons": reasons,
            "category": category,
            "domain": domain
        }
        
    def _detect_typosquatting(self, domain: str) -> List[str]:
        """Detect potential typosquatting of popular brands"""
        matches = []
        
        # Remove TLD for comparison
        domain_parts = domain.split('.')
        domain_name = domain_parts[0] if domain_parts else domain
        
        for brand in self.popular_brands:
            # Skip exact matches (legitimate)
            if domain_name == brand:
                continue
                
            # Check for similar strings (Levenshtein distance approximation)
            if self._is_similar(domain_name, brand):
                matches.append(brand)
                
            # Check for brand in subdomain with suspicious TLD
            if brand in domain and not domain.endswith(f".{brand}.com"):
                matches.append(brand)
                
        return matches[:3]  # Limit to top 3 matches
        
    def _is_similar(self, str1: str, str2: str) -> bool:
        """Check if two strings are suspiciously similar (simple heuristic)"""
        # Remove common modifications
        str1_clean = str1.replace('-', '').replace('_', '').replace('0', 'o').replace('1', 'l')
        str2_clean = str2.replace('-', '').replace('_', '').replace('0', 'o').replace('1', 'l')
        
        # Check if one contains the other with slight modifications
        if str1_clean == str2_clean:
            return True
            
        # Check character difference
        if abs(len(str1) - len(str2)) <= 2:
            diff_count = sum(1 for a, b in zip(str1, str2) if a != b)
            if diff_count <= 2 and diff_count > 0:
                return True
                
        return False
        
    def extract_urls(self, text: str) -> List[str]:
        """Extract all URLs from a text message"""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        short_pattern = r'(?:bit\.ly|goo\.gl|tinyurl\.com|t\.co|ow\.ly)/[^\s]+'
        domain_pattern = r'(?:www\.)?[a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z]{2,})+(?:/[^\s]*)?'
        
        urls = []
        
        # Find full URLs
        urls.extend(re.findall(url_pattern, text, re.IGNORECASE))
        
        # Find short URLs
        for match in re.findall(short_pattern, text, re.IGNORECASE):
            urls.append('http://' + match)
            
        # Find domain-like patterns
        for match in re.findall(domain_pattern, text, re.IGNORECASE):
            if match not in urls and '.' in match:
                urls.append('http://' + match)
                
        return list(set(urls))
        
    def validate_message(self, message: str) -> Dict:
        """
        Validate all URLs in a message.
        
        Returns aggregate suspicion score and detailed results for each URL.
        """
        urls = self.extract_urls(message)
        
        if not urls:
            return {
                "has_urls": False,
                "is_suspicious": False,
                "confidence": 0,
                "url_count": 0,
                "results": []
            }
            
        results = []
        max_confidence = 0
        
        for url in urls:
            result = self.validate(url)
            results.append({"url": url, **result})
            max_confidence = max(max_confidence, result["confidence"])
            
        return {
            "has_urls": True,
            "is_suspicious": max_confidence >= 30,
            "confidence": max_confidence,
            "url_count": len(urls),
            "results": results
        }


# Singleton instance
_validator = None


def get_url_validator() -> URLValidator:
    """Get singleton URLValidator instance"""
    global _validator
    if _validator is None:
        _validator = URLValidator()
    return _validator
