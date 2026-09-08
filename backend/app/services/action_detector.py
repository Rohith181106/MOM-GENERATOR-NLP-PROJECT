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

    def detect_action_in_text(self, text: str, speaker_name: Optional[str] = None, timestamp_str: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Evaluates whether an utterance contains an explicit action item / task commitment.
        Excludes opinions, problem descriptions, and non-committal banter.
        """
        text_clean = text.strip()
        text_lower = text_clean.lower()
        
        # 1. Non-action filter (instant rejection of observational / state descriptions)
        non_action_starters = [
            "we have had", "we had", "there was", "there were", "it was", "this was",
            "performance was", "performance is", "issues were", "issue was", "problem was",
            "this will allow", "it will allow", "that will allow", "this will be", "it will be",
            "there will be", "we will see", "i think", "i feel", "i noticed", "they discussed",
            "we discussed", "just wondering", "what do you think", "how does that sound"
        ]
        if any(text_lower.startswith(prefix) for prefix in non_action_starters):
            return None

        # 2. Strict actionable intent patterns
        action_verbs = r"(?:finish|complete|implement|fix|prepare|send|review|deliver|schedule|conduct|create|update|organize|draft|verify|deploy|follow up on|check|set up)"
        
        explicit_commitment_patterns = [
            # First person commitment: "I will finish...", "I'll take care of..."
            rf"\b(?:i will|i'll|i am going to)\s+{action_verbs}\b\s*(.*)",
            rf"\b(?:i will|i'll|i can)\s+(?:take ownership of|take care of|lead|handle)\b\s*(.*)",
            # Explicit delegation to named person: "Dharun will finish...", "Sarah, please review..."
            rf"\b([A-Z][a-z]{2,})\s+(?:will|is going to)\s+{action_verbs}\b\s*(.*)",
            rf"\b([A-Z][a-z]{2,}),?\s+(?:can you please|please|could you)\s+{action_verbs}\b\s*(.*)",
            # Explicit action item syntax
            rf"\b(?:action item|action-item)\s*(?:is|for)?\s*(?:([A-Z][a-z]+|me|us))?\s*(?:to)?\s*(.*)",
            # Clear team delegation: "Let's make sure to schedule...", "Please make sure to send..."
            rf"\b(?:let's|let us|please)\s+(?:make sure to|ensure we)\s+{action_verbs}\b\s*(.*)"
        ]

        is_action = False
        matched_owner = "NEEDS_REVIEW"

        for pat in explicit_commitment_patterns:
            match = re.search(pat, text_clean, re.IGNORECASE)
            if match:
                is_action = True
                # Extract owner if pattern captured person name
                groups = match.groups()
                if groups and groups[0] and re.match(r"^[A-Z][a-z]{2,}$", groups[0]):
                    matched_owner = groups[0]
                break

        # 3. Optional Zero-shot verification with high confidence threshold
        classifier = self._get_classifier()
        if classifier and not is_action:
            try:
                # Require high confidence (>0.88) and presence of at least one actionable verb
                has_verb = bool(re.search(action_verbs, text_lower))
                if has_verb and len(text_clean.split()) >= 4:
                    res = classifier(text_clean, candidate_labels=["an assigned task commitment with explicit ownership", "general conversation or commentary"])
                    if res['labels'][0] == "an assigned task commitment with explicit ownership" and res['scores'][0] > 0.88:
                        is_action = True
            except Exception:
                pass

        if not is_action:
            return None

        # 4. Resolve owner candidate
        owner_candidate = matched_owner
        if owner_candidate == "NEEDS_REVIEW":
            if re.search(r"\b(i will|i'll|i am going to|i can)\b", text_lower):
                owner_candidate = speaker_name if speaker_name else "NEEDS_REVIEW"
            else:
                named_person = re.search(r"\b([A-Z][a-z]{2,})\s+(?:will|shall|is going to|can you)\b", text_clean)
                if named_person and named_person.group(1) not in ["Today", "Tomorrow", "Monday", "Friday", "Let", "What"]:
                    owner_candidate = named_person.group(1)

        # 5. Resolve deadline candidate
        deadline_candidate = "NEEDS_REVIEW"
        deadline_match = re.search(r"\b(by\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|next\s+[a-z]+|end\s+of\s+month|today|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+|\d{4}-\d{2}-\d{2})|before\s+[a-z]+)\b", text_lower)
        if deadline_match:
            deadline_candidate = deadline_match.group(1)

        # 6. Task cleaning
        clean_task = text_clean
        clean_task = re.sub(r"^(?:yes,?\s*)?(?:(?:i|we|[A-Za-z0-9_]+)\s+(?:will|'ll|must|shall|need to|is going to)|can you(?:\s+please)?|please(?:\s+make sure to)?|let's\s+make sure to)\s+", "", clean_task, flags=re.IGNORECASE)
        clean_task = re.sub(r"\s+by\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|next\s+[a-z]+|end\s+of\s+month|today).*$", "", clean_task, flags=re.IGNORECASE)
        clean_task = clean_task.strip().rstrip(".,")
        if len(clean_task) < 5:
            clean_task = text_clean

        full_evidence = f"{timestamp_str}: {text_clean}" if timestamp_str else text_clean

        return {
            "task": clean_task,
            "owner": owner_candidate,
            "deadline": deadline_candidate,
            "evidence": full_evidence,
            "source_timestamp": timestamp_str or "00:00",
            "confidence": 0.94,
            "needs_review": (owner_candidate == "NEEDS_REVIEW" or deadline_candidate == "NEEDS_REVIEW")
        }

    def extract_actions_from_segments(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        actions = []
        for seg in segments:
            text = seg.get("text", "")
            speaker = seg.get("speaker_name")
            start = seg.get("start_time", 0.0)
            end = seg.get("end_time", 0.0)
            ts = f"[{int(start//60):02d}:{int(start%60):02d} - {int(end//60):02d}:{int(end%60):02d}]"
            detected = self.detect_action_in_text(text, speaker_name=speaker, timestamp_str=ts)
            if detected:
                actions.append(detected)
        return actions

action_detector = ActionItemDetector()
