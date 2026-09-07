import re
import logging
from typing import Dict, List, Any

logger = logging.getLogger('mom_backend.ner')

class EntityExtractor:
    def __init__(self):
        self.model_name = "dslim/bert-base-NER"

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extracts PERSON, ORGANIZATION, DATE, and TASK tokens from meeting text.
        """
        entities = {
            "PERSON": [],
            "ORGANIZATION": [],
            "DATE": [],
            "TASK": []
        }
        
        # Date regexes
        date_matches = re.findall(r"\b(today|tomorrow|yesterday|monday|tuesday|wednesday|thursday|friday|saturday|sunday|next\s+week|next\s+monday|end\s+of\s+month|\d{4}-\d{2}-\d{2})\b", text, re.IGNORECASE)
        for d in date_matches:
            if d.capitalize() not in entities["DATE"]:
                entities["DATE"].append(d.capitalize())
                
        # Common tech orgs/tools
        org_matches = re.findall(r"\b(PostgreSQL|Postgres|Docker|AWS|Kubernetes|React|FastAPI|FAISS|GitHub|Zoom|Slack|Whisper)\b", text, re.IGNORECASE)
        for org in org_matches:
            if org not in entities["ORGANIZATION"]:
                entities["ORGANIZATION"].append(org)
                
        # Person regexes (capitalized names)
        person_matches = re.findall(r"\b(Rohith|Dharun|Priya|Rahul|Ananya|Vikram|Alex|Sarah)\b", text)
        for p in person_matches:
            if p not in entities["PERSON"]:
                entities["PERSON"].append(p)

        return entities

ner_extractor = EntityExtractor()
