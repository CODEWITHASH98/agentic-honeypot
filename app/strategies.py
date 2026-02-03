from dataclasses import dataclass
from typing import List

@dataclass
class Strategy:
    name: str
    description: str
    action: str
    target_extractions: List[str]

# Turn-based strategy definitions
STRATEGIES = {
    "engagement": Strategy(
        name="engagement",
        description="Show interest and curiosity to hook the scammer",
        action="Respond with enthusiasm and ask how to proceed. Show you're interested but slightly confused.",
        target_extractions=[]
    ),
    "initial_extraction": Strategy(
        name="initial_extraction",
        description="Start extracting primary intelligence (UPI/bank details)",
        action="Ask specific questions about how to send money or provide information. Request payment details.",
        target_extractions=["upi_id", "bank_account"]
    ),
    "deep_extraction": Strategy(
        name="deep_extraction",
        description="Extract secondary intelligence (phone, URL, alternatives)",
        action="Pretend technical issues and ask for backup payment methods, phone numbers, or alternative links.",
        target_extractions=["phone_number", "url", "alternative_upi"]
    ),
    "stalling": Strategy(
        name="stalling",
        description="Delay while confirming and re-extracting details",
        action="Mention family/external constraints, request confirmation of details, ask for more time.",
        target_extractions=["confirmation", "additional_details"]
    ),
    "exit": Strategy(
        name="exit",
        description="Gracefully end conversation without suspicion",
        action="Cite interruption (someone at door, phone call) and promise to continue later. Thank them.",
        target_extractions=[]
    )
}

def get_strategy_for_turn(turn_count: int, extraction_progress: float) -> Strategy:
    """Determine conversation strategy based on turn number and extraction progress"""
    
    # If we've extracted enough, start exiting earlier
    if extraction_progress >= 80 and turn_count >= 6:
        return STRATEGIES["exit"]
    
    # Turn-based strategy selection
    if turn_count <= 2:
        return STRATEGIES["engagement"]
    elif turn_count <= 5:
        return STRATEGIES["initial_extraction"]
    elif turn_count <= 8:
        return STRATEGIES["deep_extraction"]
    elif turn_count <= 12:
        return STRATEGIES["stalling"]
    else:
        return STRATEGIES["exit"]

def should_exit_conversation(turn_count: int, extraction_progress: float, last_scammer_msg: str) -> bool:
    """Determine if we should exit the conversation"""
    
    # Exit conditions
    # Exit conditions
    # Use regex word boundaries to prevent substring matching (e.g. "ai" in "claim")
    import re
    exit_keywords = [
        r"\bpolice\b", r"\bfraud\b", r"\bstop\b", r"\breport\b", 
        r"\bsuspicious\b", r"\bbot\b", r"\bai\b", r"\bfake\b", r"\bscam\b"
    ]
    
    # Check 1: Scammer Suspicion
    msg_lower = last_scammer_msg.lower()
    if any(re.search(pattern, msg_lower) for pattern in exit_keywords):
        return True
    
    # Check 2: Hard Turn Limit (Safety)
    if turn_count >= 15:
        return True
    
    # Check 3: Optimal Extraction (Success)
    # If we have gathered significant intel, we can leave early to avoid exposure
    if extraction_progress >= 90 and turn_count >= 6:
        return True
    
    # Check 4: Moderate Extraction + Duration
    # If meaningful intel gathered and we've engaged for a while
    if extraction_progress >= 70 and turn_count >= 10:
        return True
    
    return False
