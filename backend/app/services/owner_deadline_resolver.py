from datetime import datetime
from typing import Optional, List
import dateparser
import logging

logger = logging.getLogger('mom_backend.resolver')

class OwnerDeadlineResolver:
    @staticmethod
    def resolve_deadline(raw_deadline: str, base_date_str: Optional[str] = None) -> str:
        """
        Converts relative natural date expressions ('Friday', 'tomorrow', 'next week')
        into normalized ISO format (YYYY-MM-DD). If ambiguous, returns NEEDS_REVIEW.
        """
        if not raw_deadline or raw_deadline.upper() == "NEEDS_REVIEW":
            return "NEEDS_REVIEW"

        # Clean words like 'by', 'before'
        cleaned = raw_deadline.lower().replace("by ", "").replace("before ", "").strip()
        
        # Base anchor date
        base_date = datetime.utcnow()
        if base_date_str:
            try:
                base_date = datetime.strptime(base_date_str, "%Y-%m-%d")
            except Exception:
                pass
                
        try:
            parsed = dateparser.parse(
                cleaned,
                settings={
                    'RELATIVE_BASE': base_date,
                    'PREFER_DATES_FROM': 'future'
                }
            )
            if parsed:
                return parsed.strftime("%Y-%m-%d")
        except Exception as e:
            logger.error(f"Error parsing date '{raw_deadline}': {e}")
            
        return "NEEDS_REVIEW"

    @staticmethod
    def resolve_owner(
        raw_owner: str,
        speaker_name: Optional[str] = None,
        roster: Optional[List[str]] = None
    ) -> str:
        """
        Maps ambiguous references ('I', 'me', 'we') to actual speaker or roster name.
        If cannot be resolved reliably, returns NEEDS_REVIEW.
        """
        if not raw_owner or raw_owner.upper() == "NEEDS_REVIEW":
            if speaker_name:
                return speaker_name
            return "NEEDS_REVIEW"

        if raw_owner.lower() in ["i", "me", "myself", "we"]:
            return speaker_name if speaker_name else "NEEDS_REVIEW"

        roster_names = [r.strip() for r in (roster or []) if r and r.strip()]
        for name in roster_names:
            if name.lower() in raw_owner.lower():
                return name

        return raw_owner

resolver_service = OwnerDeadlineResolver()
