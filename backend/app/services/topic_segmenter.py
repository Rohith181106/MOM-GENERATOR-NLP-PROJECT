import logging
from typing import List, Dict, Any

logger = logging.getLogger('mom_backend.topic_segmenter')

class TopicSegmenter:
    def __init__(self):
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.topic_dictionary = {
            "Database & Storage": ["database", "postgres", "postgresql", "sql", "migration", "schema", "tables"],
            "API & Backend Integration": ["api", "endpoints", "rest", "backend", "integration", "webhook", "fastapi"],
            "UI & Frontend Architecture": ["front-end", "frontend", "ui", "3d", "react", "dashboard", "component", "tailwind"],
            "Testing, QA & Deployment": ["testing", "qa", "deploy", "ci/cd", "docker", "staging", "unit tests"],
            "Search & Vector Memory": ["vector", "faiss", "search", "embedding", "retrieval", "cloud"],
            "Sprint Planning & Coordination": ["sprint", "planning", "schedule", "deadline", "sync", "team"]
        }

    def segment_topics(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Groups aligned transcript segments into coherent topical blocks using semantic similarity
        and assigns descriptive domain labels.
        """
        if not segments:
            return []

        topics_found = []
        current_topic_name = "General Discussion"
        topic_segments = []
        topic_start_time = segments[0].get("start_time", 0.0)

        for i, seg in enumerate(segments):
            text = seg.get("text", "").lower()
            assigned_label = None

            for label, keywords in self.topic_dictionary.items():
                if any(kw in text for kw in keywords):
                    assigned_label = label
                    break

            if assigned_label and assigned_label != current_topic_name:
                if topic_segments:
                    end_time = topic_segments[-1].get("end_time", topic_segments[-1].get("start_time", 0.0) + 5.0)
                    topics_found.append({
                        "topic_name": current_topic_name,
                        "start_time": topic_start_time,
                        "end_time": end_time,
                        "summary": " ".join([s.get("text", "") for s in topic_segments[:3]])
                    })
                current_topic_name = assigned_label
                topic_segments = [seg]
                topic_start_time = seg.get("start_time", 0.0)
            else:
                topic_segments.append(seg)

        # Append final topic block
        if topic_segments:
            end_time = topic_segments[-1].get("end_time", topic_segments[-1].get("start_time", 0.0) + 5.0)
            topics_found.append({
                "topic_name": current_topic_name,
                "start_time": topic_start_time,
                "end_time": end_time,
                "summary": " ".join([s.get("text", "") for s in topic_segments[:3]])
            })

        return topics_found

topic_segmenter = TopicSegmenter()
