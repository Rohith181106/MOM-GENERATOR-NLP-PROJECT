import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger('mom_backend.validator')

class ValidationService:
    @staticmethod
    def validate_action_items(
        candidate_actions: List[Dict[str, Any]],
        transcript_segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if not candidate_actions or not transcript_segments:
            return []

        all_text = ' '.join([s.get('text', '').lower() for s in transcript_segments])
        non_action_starters = [
            'we had', 'we have had', 'there were', 'there was', 'it was',
            'performance is', 'issues were', 'problem was', 'they discussed',
            'users were', 'i think', 'i feel', 'i noticed', 'we noticed',
            'maybe we could', 'just wondering', 'this was', 'that was',
            'which will allow', 'that will happen', 'it will be', 'there will be'
        ]

        validated = []
        seen_tasks = set()

        for act in candidate_actions:
            task = act.get('task', '').strip()
            evidence = act.get('evidence', '').strip()
            task_lower = task.lower()

            if not task or len(task) < 5:
                continue

            raw_evidence = re.sub(r'^\[\d{2}:\d{2}\s*-\s*\d{2}:\d{2}\]:?\s*', '', evidence).strip()
            if raw_evidence and (raw_evidence.lower() not in all_text and task_lower not in all_text):
                logger.info(f'Filtered ungrounded action item: {task}')
                continue

            if any(task_lower.startswith(prefix) for prefix in non_action_starters):
                logger.info(f'Filtered descriptive observation: {task}')
                continue

            clean_key = re.sub(r'[^\w\s]', '', task_lower)
            clean_key = ' '.join(clean_key.split()[:5])
            if clean_key in seen_tasks:
                continue
            seen_tasks.add(clean_key)

            owner = act.get('owner', 'NEEDS_REVIEW')
            if owner and owner != 'NEEDS_REVIEW':
                if owner.lower() not in raw_evidence.lower() and not act.get('speaker_name'):
                    act['owner'] = 'NEEDS_REVIEW'
                    act['needs_review'] = True

            deadline = act.get('deadline', 'NEEDS_REVIEW')
            if deadline and deadline != 'NEEDS_REVIEW':
                if deadline.lower() not in raw_evidence.lower():
                    act['deadline'] = 'NEEDS_REVIEW'
                    act['needs_review'] = True

            validated.append(act)

        validated_sorted = sorted(validated, key=lambda x: (not x.get('needs_review', False), x.get('confidence', 0.9)), reverse=True)
        return validated_sorted[:15]

    @staticmethod
    def validate_decisions(
        candidate_decisions: List[Dict[str, Any]],
        transcript_segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if not candidate_decisions or not transcript_segments:
            return []

        all_text = ' '.join([s.get('text', '').lower() for s in transcript_segments])
        proposal_starters = [
            'what if', 'how about', 'could we', 'maybe we', 'we might',
            'not sure', 'open question', 'should we'
        ]

        validated = []
        seen = set()

        for dec in candidate_decisions:
            statement = dec.get('decision', '').strip()
            evidence = dec.get('evidence', '').strip()
            stmt_lower = statement.lower()

            if not statement or len(statement) < 5:
                continue

            raw_evidence = re.sub(r'^\[\d{2}:\d{2}\s*-\s*\d{2}:\d{2}\]:?\s*', '', evidence).strip()
            if raw_evidence and (raw_evidence.lower() not in all_text and stmt_lower not in all_text):
                continue

            if any(stmt_lower.startswith(p) for p in proposal_starters) or stmt_lower.endswith('?'):
                continue

            key = ' '.join(stmt_lower.split()[:6])
            if key in seen:
                continue
            seen.add(key)

            validated.append(dec)

        return validated[:10]

validator_service = ValidationService()
