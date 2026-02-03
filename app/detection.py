import time
import asyncio
import re
from app.schemas import DetectionResult
from app.dataset import dataset_validator
from app.groq_client import groq_client
from app.url_validator import get_url_validator

class DetectionPipeline:
    """
    Multi-Tiered Scam Detection System
    
    Tier 1: Rule-based (Keywords, Patterns) - Ultra Fast
    Tier 2: Dataset Matching (Known Hash Patterns) - Fast
    Tier 2.5: URL Threat Scoring (Phishing/Malware) - Fast
    Tier 3: LLM Context Analysis (Groq Llama 3) - Intelligent
    Tier 4: Self-Validation (Consensus Check) - Roboust
    """
    def __init__(self):
        # Initialize models here in the future
        self.url_validator = get_url_validator()

    async def detect(self, message: str) -> DetectionResult:
        start_time = time.time()
        
        # Tier 1: Rule-based (Fast - 50ms)
        rule_score = self._rule_based_detection(message)
        scam_type = self._classify_by_keywords(message)
        
        # Tier 2: Dataset Validation (Fast - 50ms)
        dataset_match = dataset_validator.validate(message)
        
        final_score = rule_score
        reasoning_parts = [f"T1-Rules:{rule_score:.0f}"]
        
        if dataset_match and dataset_match["is_match"]:
            boost = dataset_match["confidence"] * 0.15
            final_score = min(final_score + boost, 100)
            scam_type = dataset_match["category"]
            reasoning_parts.append(f"T2-Dataset:+{boost:.0f}")
        
        # Tier 2.5: URL Validation (Fast - 10ms)
        url_result = self.url_validator.validate_message(message)
        if url_result["is_suspicious"]:
            url_boost = url_result["confidence"] * 0.25
            final_score = min(final_score + url_boost, 100)
            if url_result["results"]:
                top_url = url_result["results"][0]
                if top_url.get("category"):
                    scam_type = scam_type or f"phishing_{top_url['category']}"
            reasoning_parts.append(f"T2.5-URL:+{url_boost:.0f}")
        
        # Tier 3: LLM Analysis (if score uncertain 45-90%)
        # Lowered threshold to catch subtle job scams that score around 50
        if 45 <= final_score <= 90:
            llm_result = await groq_client.analyze_scam(message)
            if llm_result:
                llm_conf = llm_result.get("confidence", 0)
                is_llm_scam = llm_result.get("is_scam", False)
                
                if is_llm_scam:
                    final_score = max(final_score, llm_conf)
                    scam_type = llm_result.get("scam_type", scam_type)
                    reasoning_parts.append(f"T3-LLM:{llm_conf}")
                    
                    # Tier 4: Self-validation (if still uncertain 70-90%)
                    if 70 <= final_score <= 90:
                        validation = await groq_client.validate_detection(message, llm_result)
                        if validation:
                            val_conf = validation.get("confidence", 0)
                            is_val_scam = validation.get("is_scam", False)
                            
                            if is_val_scam:
                                # Both agree it's a scam -> Boost confidence
                                boost_val = (val_conf * 0.2)
                                final_score = min(final_score + boost_val, 99) 
                                reasoning_parts.append(f"T4-Valid:+{boost_val:.0f}")
                            else:
                                # Disagreement -> Penalize confidence
                                final_score = final_score * 0.8
                                reasoning_parts.append("T4-Valid:Disagree(-20%)")
        
        joined_reasoning = " | ".join(reasoning_parts)
        
        # Decision
        if final_score > 70:
            return DetectionResult(
                is_scam=True,
                confidence=final_score,
                scam_type=scam_type,
                detection_time_ms=int((time.time() - start_time) * 1000),
                reasoning=joined_reasoning
            )
        
        return DetectionResult(
            is_scam=False,
            confidence=final_score,
            scam_type=None,
            detection_time_ms=int((time.time() - start_time) * 1000),
            reasoning=joined_reasoning or "No scam detected"
        )

    def _rule_based_detection(self, message: str) -> float:
        """Rule-based scoring with keyword and pattern matching"""
        
        score = 0.0
        message_lower = message.lower()
        
        # Urgency keywords (+20 each)
        urgency_keywords = ["urgent", "immediately", "today", "now", "hurry", "limited time", "at risk", "blocked", "suspended"]
        score += sum(20 for kw in urgency_keywords if kw in message_lower)
        
        # Financial keywords (+25 each)
        financial_keywords = ["bank account", "upi", "transfer", "payment", "money", "₹", "rupees", "wallet", "credit", "debit"]
        score += sum(25 for kw in financial_keywords if kw in message_lower)
        
        # Authority claims (+30 each)
        authority_keywords = ["government", "police", "tax", "rbi", "official", "department", "customs", "court", "legal"]
        score += sum(30 for kw in authority_keywords if kw in message_lower)
        
        # Reward/Prize (+35 each)
        reward_keywords = ["won", "prize", "congratulations", "selected", "winner", "lottery", "gift", "reward", "lucky"]
        score += sum(35 for kw in reward_keywords if kw in message_lower)
        
        # Job/Opportunity (+25)
        job_keywords = ["hiring", "job", "salary", "work from home", "part time", "recruit", "offer letter", "interview"]
        score += sum(25 for kw in job_keywords if kw in message_lower)
        
        # Tech Support (+25)
        tech_keywords = ["virus", "hacked", "compromised", "security alert", "antivirus", "remote access", "teamviewer"]
        score += sum(25 for kw in tech_keywords if kw in message_lower)
        
        # Pattern detection (+40 each)
        if re.search(r'[a-zA-Z0-9._-]+@[a-zA-Z]+', message):  # UPI pattern
            score += 40
        if re.search(r'\b\d{10,18}\b', message):  # Account number pattern
            score += 40
        if 'http' in message or 'bit.ly' in message or 'goo.gl' in message:  # URL
            score += 35
        if re.search(r'(?:\+91)?[6-9]\d{9}', message):  # Phone pattern
            score += 25
        
        return min(score, 100.0)

    def _classify_by_keywords(self, message: str) -> str:
        """Keyword-based scam type classification"""
        msg = message.lower()
        
        # Priority order for classification
        if any(x in msg for x in ["job", "hiring", "salary", "work from home", "offer letter"]):
            return "job"
        if any(x in msg for x in ["bank", "account blocked", "kyc", "verify account", "suspended"]):
            return "banking"
        if any(x in msg for x in ["won", "prize", "lottery", "winner", "lucky draw"]):
            return "prize"
        if any(x in msg for x in ["virus", "hacked", "security", "antivirus", "remote"]):
            return "tech_support"
        if any(x in msg for x in ["loan", "interest", "invest", "profit", "returns"]):
            return "investment"
        if any(x in msg for x in ["love", "relationship", "marriage", "lonely"]):
            return "romance"
        return "unknown"

detection_pipeline = DetectionPipeline()
