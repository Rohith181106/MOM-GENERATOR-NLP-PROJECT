import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger('mom_backend.action_detector')

class ActionItemDetector:
    def __init__(self):
        self.model_name = "microsoft/deberta-v3-base"
        self._classifier = None
        self._initialized = False

    def _get_classifier(self):
        if not self._initialized:
            try:
                from transformers import pipeline
                # Initialize zero-shot or sequence classifier pipeline
                self._classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
            except Exception as e:
                logger.info(f"Transformers pipeline not loaded locally: {e}. Utilizing regex/heuristic action classifier.")
                self._classifier = None
            self._initialized = True
        return self._classifier

    def detect_action_in_text(self, text: str, speaker_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Evaluates whether a single utterance contains an action item.
        Used for both live preliminary notifications and batch processing.
        """
        text_lower = text.lower()
        
        # Action intent patterns:
        action_patterns = [
            r"(i will|i'll|will finish|will complete|going to complete|take ownership|can you take|will wrap up|assigned to|please make sure to|need to finish|needs to implement|action item)\s+(.*)",
            r"(let's|let us)\s+(make sure|implement|deploy|finish|schedule)\s+(.*)",
            r"([a-z]+)\s+(will|shall|is going to)\s+(finish|complete|implement|fix|prepare|send|review|deliver)\s+(.*)"
        ]
        
        is_action = False
        task_candidate = ""
        owner_candidate = "NEEDS_REVIEW"
        deadline_candidate = "NEEDS_REVIEW"
        
        for pattern in action_patterns:
            match = re.search(pattern, text_lower)
            if match:
                is_action = True
                break
                
        # Also check with classifier if loaded
        classifier = self._get_classifier()
        if classifier and not is_action:
            try:
                res = classifier(text, candidate_labels=["an action item or task commitment", "general discussion statement"])
                if res['labels'][0] == "an action item or task commitment" and res['scores'][0] > 0.70:
                    is_action = True
            except Exception:
                pass
                
        if not is_action:
            return None

        # Extract Task, Owner, Deadline
        # 1. Owner extraction heuristic from speaker context
        if re.search(r"\b(i will|i'll|i am going to)\b", text_lower):
            owner_candidate = speaker_name if speaker_name else "NEEDS_REVIEW"
        else:
            # Check if text mentions a known person name
            names_match = re.search(r"\b([A-Z][a-z]+)\s+(will|is going to|can you)\b", text)
            if names_match:
                owner_candidate = names_match.group(1)

        # 2. Deadline detection
        deadline_match = re.search(r"\b(by\s+(?:friday|monday|tuesday|wednesday|thursday|tomorrow|next\s+week|next\s+monday|end\s+of\s+month|today)|before\s+[a-z]+)\b", text_lower)
        if deadline_match:
            deadline_candidate = deadline_match.group(1)

        # 3. Task cleaning
        clean_task = text
        # Remove prefixes like "I will finish", "Dharun will"
        clean_task = re.sub(r"^(yes,?\s*)?(i will|i'll|we need to|dharun will|priya will|can you)\s+", "", clean_task, flags=re.IGNORECASE)
        # Remove trailing deadline from task
        clean_task = re.sub(r"\s+by\s+(?:friday|monday|tuesday|wednesday|thursday|tomorrow|next\s+week|next\s+monday|end\s+of\s+month|today).*$", "", clean_task, flags=re.IGNORECASE)
        clean_task = clean_task.strip().rstrip(".,")
        if not clean_task:
            clean_task = text

        return {
            "task": clean_task,
            "owner": owner_candidate,
            "deadline": deadline_candidate,
            "evidence": text,
            "confidence": 0.94,
            "needs_review": (owner_candidate == "NEEDS_REVIEW" or deadline_candidate == "NEEDS_REVIEW")
        }

    def extract_actions_from_segments(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        actions = []
        for seg in segments:
            text = seg.get("text", "")
            speaker = seg.get("speaker_name")
            detected = self.detect_action_in_text(text, speaker_name=speaker)
            if detected:
                actions.append(detected)
        return actions

action_detector = ActionItemDetector()
