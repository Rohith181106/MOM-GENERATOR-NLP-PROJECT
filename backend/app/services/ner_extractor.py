import re
import logging
from typing import Dict, List, Any

logger = logging.getLogger('mom_backend.ner')

class EntityExtractor:
    def __init__(self):
        self.model_name = "dslim/bert-base-NER"
        self._pipeline = None
        self._initialized = False

    def _get_pipeline(self):
        if not self._initialized:
            try:
                from transformers import pipeline
                self._pipeline = pipeline("ner", model=self.model_name, aggregation_strategy="simple")
                logger.info("dslim/bert-base-NER pipeline initialized successfully.")
            except Exception as e:
                logger.info(f"BERT NER pipeline not loaded locally: {e}. Utilizing dynamic heuristic extractor.")
                self._pipeline = None
            self._initialized = True
        return self._pipeline

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extracts PERSON, ORGANIZATION, DATE, and TASK tokens from meeting text dynamically.
        """
        entities = {
            "PERSON": [],
            "ORGANIZATION": [],
            "DATE": [],
            "TASK": []
        }
        
        # 1. Date regexes
        date_matches = re.findall(r"\b(today|tomorrow|yesterday|monday|tuesday|wednesday|thursday|friday|saturday|sunday|next\s+week|next\s+[a-z]+|end\s+of\s+month|\d{4}-\d{2}-\d{2})\b", text, re.IGNORECASE)
        for d in date_matches:
            val = d.capitalize()
            if val not in entities["DATE"]:
                entities["DATE"].append(val)

        # 2. Try transformer model if loaded
        pipe = self._get_pipeline()
        if pipe:
            try:
                ner_results = pipe(text)
                for item in ner_results:
                    entity_group = item.get("entity_group", "")
                    word = item.get("word", "").strip()
                    if entity_group == "PER" and word and word not in entities["PERSON"]:
                        entities["PERSON"].append(word)
                    elif entity_group == "ORG" and word and word not in entities["ORGANIZATION"]:
                        entities["ORGANIZATION"].append(word)
                if entities["PERSON"] or entities["ORGANIZATION"]:
                    return entities
            except Exception as e:
                logger.warning(f"Error executing NER pipeline: {e}")

        # 3. Dynamic linguistic entity extraction fallback (No hardcoded names)
        # Tech organizations & platforms
        org_matches = re.findall(r"\b(PostgreSQL|Postgres|Docker|AWS|Azure|GCP|Kubernetes|React|FastAPI|FAISS|GitHub|Zoom|Slack|Whisper|Python|Node|Redis|MongoDB)\b", text, re.IGNORECASE)
        for org in org_matches:
            if org not in entities["ORGANIZATION"]:
                entities["ORGANIZATION"].append(org)

        # Dynamic Person matching via dialogue patterns:
        # e.g., "Alex, can you", "Hi Sarah", "assigned to David", "John will"
        dialogue_person_patterns = [
            r"\b(?:hi|hey|hello|ask|with|assign to|assigned to|cc)\s+([A-Z][a-z]{2,})\b",
            r"\b([A-Z][a-z]{2,}),\s*(?:can you|could you|please|will you)\b",
            r"\b([A-Z][a-z]{2,})\s+(?:will|agreed|suggested|mentioned|said|noted)\b"
        ]
        stopwords = {"Today", "Tomorrow", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "First", "Next", "Then", "Let", "What", "How", "Why", "The", "Our", "We", "You", "One", "Yes", "No", "Good", "Morning"}

        for pat in dialogue_person_patterns:
            matches = re.findall(pat, text, flags=re.IGNORECASE)
            for m in matches:
                name = m.strip().capitalize()
                if name not in stopwords and name not in entities["PERSON"]:
                    entities["PERSON"].append(name)

        return entities

ner_extractor = EntityExtractor()
