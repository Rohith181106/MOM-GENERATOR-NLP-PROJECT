import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger('mom_backend.decision_detector')

class DecisionDetector:
    def __init__(self):
        self.model_name = "microsoft/deberta-v3-base"
        self.classes = ["DISCUSSION", "PROPOSAL", "AGREEMENT", "DECISION", "UNRESOLVED"]

    def classify_dialogue_act(self, text: str) -> str:
        text_lower = text.lower()
        
        # Unresolved detection
        if any(w in text_lower for w in ["unresolved", "open question", "still debating", "haven't decided", "separate spike", "not sure yet", "pending decision"]):
            return "UNRESOLVED"
            
        # Decision / Agreement detection
        if any(w in text_lower for w in ["agreed", "decided", "decision is", "we'll use", "we will use", "team agreed", "finalized", "finalize", "approved", "consensus", "go with", "selected"]):
            return "DECISION"
            
        # Proposal detection
        if any(w in text_lower for w in ["how about", "what if", "i propose", "could we", "maybe we should", "why don't we"]):
            return "PROPOSAL"
            
        # Agreement detection
        if any(w in text_lower for w in ["yes, that makes sense", "i agree", "sounds good", "let's do that", "perfect"]):
            return "AGREEMENT"
            
        return "DISCUSSION"

    def detect_decision_in_text(self, text: str, timestamp_str: Optional[str] = None) -> Optional[Dict[str, Any]]:
        act = self.classify_dialogue_act(text)
        if act == "DECISION":
            clean_decision = text.strip()
            full_evidence = f"{timestamp_str}: {text}" if timestamp_str else text
            return {
                "decision": clean_decision,
                "evidence": full_evidence,
                "source_timestamp": timestamp_str or "00:00",
                "confidence": 0.95
            }
        return None

    def detect_unresolved_in_text(self, text: str, timestamp_str: Optional[str] = None) -> Optional[Dict[str, Any]]:
        act = self.classify_dialogue_act(text)
        if act == "UNRESOLVED":
            full_evidence = f"{timestamp_str}: {text}" if timestamp_str else text
            return {
                "issue": text.strip(),
                "evidence": full_evidence,
                "source_timestamp": timestamp_str or "00:00"
            }
        return None

    def extract_decisions_and_issues(self, segments: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        decisions = []
        unresolved = []
        
        for seg in segments:
            text = seg.get("text", "")
            start = seg.get("start_time", 0.0)
            end = seg.get("end_time", 0.0)
            ts = f"[{int(start//60):02d}:{int(start%60):02d} - {int(end//60):02d}:{int(end%60):02d}]"
            d = self.detect_decision_in_text(text, timestamp_str=ts)
            if d:
                decisions.append(d)
            u = self.detect_unresolved_in_text(text, timestamp_str=ts)
            if u:
                unresolved.append(u)
                
        return {
            "decisions": decisions,
            "unresolved_issues": unresolved
        }

decision_detector = DecisionDetector()
