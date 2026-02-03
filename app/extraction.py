import re
import httpx
import asyncio
from typing import Dict, List, Any
from app.schemas import ExtractedIntelligence

class ExtractionPipeline:

    # Regex Patterns
    UPI_PATTERN = re.compile(r'[a-zA-Z0-9._-]+@[a-zA-Z]+')
    BANK_ACCOUNT_PATTERN = re.compile(r'\b\d{9,18}\b')
    PHONE_PATTERN = re.compile(r'(?:\+91[\s-]?)?[6-9]\d{9}')
    URL_PATTERN = re.compile(r'(?:https?://)?(?:www\.)?[a-zA-Z0-9.-]+\.[a-z]{2,}(?:/[^\s]*)?')
    IFSC_PATTERN = re.compile(r'[A-Z]{4}0[A-Z0-9]{6}')

    def __init__(self):
        self.client = None

    async def get_client(self):
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=2.0)
        return self.client
    
    async def close(self):
        if self.client:
            await self.client.aclose()
            self.client = None

    async def extract(self, message: str) -> ExtractedIntelligence:
        # Method 1: Regex Extraction
        regex_results = self._extract_with_regex(message)
        
        # Merge and Validate
        validated = await self._validate_and_enrich(regex_results)
        
        # Calculate Completeness Score
        completeness = self._calculate_completeness(validated)
        
        return ExtractedIntelligence(
            upi_ids=validated.get("upi_ids", []),
            bank_accounts=validated.get("bank_accounts", []),
            phone_numbers=validated.get("phone_numbers", []),
            urls=validated.get("urls", []),
            extraction_completeness=completeness
        )

    def _extract_with_regex(self, message: str) -> Dict[str, List[Any]]:
        """Extract all entities using regex patterns"""
        return {
            "upi_ids": self.UPI_PATTERN.findall(message),
            "bank_accounts": self.BANK_ACCOUNT_PATTERN.findall(message),
            "phone_numbers": self.PHONE_PATTERN.findall(message),
            "urls": self.URL_PATTERN.findall(message),
            "ifsc_codes": self.IFSC_PATTERN.findall(message)
        }

    async def _validate_and_enrich(self, extracted: Dict) -> Dict:
        """Validate formats and enrich with additional data"""
        validated = {
            "upi_ids": [],
            "bank_accounts": [],
            "phone_numbers": [],
            "urls": []
        }
        
        # Validate UPI IDs
        for upi in set(extracted.get("upi_ids", [])):
            if self._is_valid_upi(upi):
                provider = self._get_upi_provider(upi)
                validated["upi_ids"].append(upi)
        
        # Validate Bank Accounts
        for account in set(extracted.get("bank_accounts", [])):
            if self._is_valid_account(account):
                validated["bank_accounts"].append({
                    "account_number": account,
                    "ifsc_code": "",
                    "bank_name": "Unknown"
                })
        
        # Validate Phone Numbers
        for phone in set(extracted.get("phone_numbers", [])):
            normalized = self._normalize_phone(phone)
            if self._is_valid_indian_mobile(normalized):
                validated["phone_numbers"].append(normalized)
        
        # Validate URLs (Parallelized)
        unique_urls = list(set(extracted.get("urls", [])))
        if unique_urls:
            url_tasks = [self._process_url(url) for url in unique_urls]
            processed_urls = await asyncio.gather(*url_tasks)
            validated["urls"] = processed_urls
        
        return validated

    async def _process_url(self, url: str) -> Dict:
        """Process a single URL: expand and assess threat"""
        expanded = await self._expand_url(url)
        threat_score = self._assess_threat(expanded)
        return {
            "original": url,
            "expanded": expanded,
            "threat_score": threat_score
        }

    def _is_valid_upi(self, upi: str) -> bool:
        """Check if UPI ID is in valid format"""
        known_providers = ["paytm", "ybl", "okaxis", "okicici", "okhdfcbank", "upi", "apl", "ibl", "axl", "sbi", "icici", "hdfc", "gpay", "phonepe"]
        parts = upi.split("@")
        if len(parts) != 2:
            return False
        return parts[1].lower() in known_providers or len(parts[1]) >= 2

    def _get_upi_provider(self, upi: str) -> str:
        """Get UPI provider name"""
        provider_map = {
            "paytm": "Paytm", "ybl": "PhonePe", "okaxis": "Google Pay",
            "okicici": "Google Pay", "okhdfcbank": "Google Pay", "apl": "Amazon Pay",
            "ibl": "iMobile Pay", "axl": "Axis Bank", "sbi": "SBI Buddy"
        }
        parts = upi.split("@")
        return provider_map.get(parts[1].lower(), parts[1].upper())

    def _is_valid_account(self, account: str) -> bool:
        """Check if bank account number is valid"""
        return 9 <= len(account) <= 18

    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number to +91XXXXXXXXXX format"""
        digits = re.sub(r'\D', '', phone)
        if len(digits) == 10:
            return f"+91{digits}"
        elif len(digits) == 12 and digits.startswith("91"):
            return f"+{digits}"
        return phone

    def _is_valid_indian_mobile(self, phone: str) -> bool:
        """Check if valid Indian mobile number"""
        clean = re.sub(r'\D', '', phone)
        if len(clean) == 10:
            return clean[0] in "6789"
        elif len(clean) == 12 and clean.startswith("91"):
            return clean[2] in "6789"
        return False

    async def _expand_url(self, url: str) -> str:
        """Expand shortened URLs"""
        short_domains = ["bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly"]
        try:
            if any(d in url for d in short_domains):
                if not url.startswith("http"):
                    url = "http://" + url
                
                client = await self.get_client()
                response = await client.head(url, follow_redirects=True)
                return str(response.url)
        except:
            pass
        return url

    def _assess_threat(self, url: str) -> int:
        """Basic threat scoring for URLs"""
        score = 0
        suspicious_keywords = ["login", "verify", "bank", "secure", "account", "update", "confirm", "click"]
        for kw in suspicious_keywords:
            if kw in url.lower():
                score += 15
        if url.startswith("http://"):
            score += 20
        if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url):  # IP-based URL
            score += 30
        return min(score, 100)

    def _calculate_completeness(self, validated: Dict) -> float:
        """Calculate extraction completeness score"""
        score = 0
        if validated.get("upi_ids"):
            score += 40
        if validated.get("bank_accounts"):
            score += 30
        if validated.get("phone_numbers"):
            score += 20
        if validated.get("urls"):
            score += 10
        return min(score, 100)

extraction_pipeline = ExtractionPipeline()
