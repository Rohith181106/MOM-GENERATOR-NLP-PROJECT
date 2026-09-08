import re
import logging
import numpy as np
from typing import List, Dict, Any

logger = logging.getLogger('mom_backend.topic_segmenter')

class TopicSegmenter:
    def __init__(self):
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self._model = None
        self._initialized = False

    def _get_model(self):
        if not self._initialized:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading SentenceTransformer '{self.model_name}' for dynamic topic segmentation...")
                self._model = SentenceTransformer(self.model_name)
                logger.info("SentenceTransformer loaded successfully.")
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformer locally: {e}")
                self._model = None
            self._initialized = True
        return self._model

    def _extract_candidates(self, text: str) -> List[str]:
        """Extracts multi-word noun phrase candidates from text."""
        stopwords = {
            "the", "and", "that", "this", "with", "have", "from", "they", "will", "would",
            "there", "their", "what", "about", "which", "when", "make", "like", "time", "just",
            "know", "take", "into", "year", "your", "good", "some", "could", "them", "other",
            "than", "then", "also", "well", "because", "even", "most", "really", "right", "yeah",
            "okay", "sure", "think", "going", "want", "mean", "look", "said", "talk", "team",
            "thing", "things", "meeting", "call", "discussion"
        }
        words = re.findall(r"\b[A-Za-z]{3,}\b", text)
        candidates = []
        # Bigrams and Trigrams
        for i in range(len(words) - 1):
            w1 = words[i].lower()
            w2 = words[i+1].lower()
            if w1 not in stopwords and w2 not in stopwords:
                candidates.append(f"{words[i]} {words[i+1]}")
                if i + 2 < len(words):
                    w3 = words[i+2].lower()
                    if w3 not in stopwords:
                        candidates.append(f"{words[i]} {words[i+1]} {words[i+2]}")
        # Single strong words as fallback
        for w in words:
            if len(w) > 4 and w.lower() not in stopwords:
                candidates.append(w)
        return list(dict.fromkeys(candidates))

    def _label_block(self, block_text: str, model) -> str:
        """Dynamically labels a topic block using KeyBERT semantic similarity against block text."""
        candidates = self._extract_candidates(block_text)
        if not candidates:
            return "General Discussion"

        if model:
            try:
                block_emb = model.encode([block_text])[0]
                cand_embs = model.encode(candidates[:35])
                # Compute cosine similarities
                norm_b = np.linalg.norm(block_emb) + 1e-9
                norms_c = np.linalg.norm(cand_embs, axis=1) + 1e-9
                sims = np.dot(cand_embs, block_emb) / (norms_c * norm_b)
                top_idx = int(np.argmax(sims))
                best_phrase = candidates[top_idx]
                return best_phrase.strip().title()
            except Exception as e:
                logger.warning(f"KeyBERT topic label extraction error: {e}")

        # Heuristic fallback: pick longest distinct multi-word candidate
        multi_words = [c for c in candidates if " " in c]
        if multi_words:
            return multi_words[0].strip().title()
        return candidates[0].strip().title()

    def segment_topics(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Dynamically groups transcript segments into coherent topical blocks
        using sentence embeddings and dynamic KeyBERT phrase extraction.
        Strictly zero hardcoded categories.
        """
        if not segments:
            return []

        # If very short meeting (< 4 segments), produce a single dynamic topic
        full_text = " ".join([s.get("text", "") for s in segments])
        model = self._get_model()

        if len(segments) <= 5:
            topic_label = self._label_block(full_text, model)
            return [{
                "topic_name": topic_label,
                "start_time": segments[0].get("start_time", 0.0),
                "end_time": segments[-1].get("end_time", 10.0),
                "summary": full_text[:250] + ("..." if len(full_text) > 250 else "")
            }]

        # Group speech turns into chunks of 3-5 segments
        chunk_size = 4
        chunks = []
        for i in range(0, len(segments), chunk_size):
            slice_segs = segments[i:i + chunk_size]
            c_text = " ".join([s.get("text", "") for s in slice_segs if s.get("text", "").strip()])
            if c_text:
                chunks.append({
                    "start_time": slice_segs[0].get("start_time", 0.0),
                    "end_time": slice_segs[-1].get("end_time", slice_segs[0].get("start_time", 0.0) + 5.0),
                    "text": c_text,
                    "segments": slice_segs
                })

        if not chunks:
            return []

        # Calculate semantic boundaries between adjacent chunks
        boundaries = [0]
        if model and len(chunks) > 1:
            try:
                chunk_texts = [c["text"] for c in chunks]
                embs = model.encode(chunk_texts)
                norms = np.linalg.norm(embs, axis=1, keepdims=True) + 1e-9
                embs_norm = embs / norms

                # Compute adjacent similarities
                sims = [np.dot(embs_norm[i], embs_norm[i+1]) for i in range(len(chunks) - 1)]
                sim_mean = float(np.mean(sims))
                sim_std = float(np.std(sims))
                threshold = max(0.40, sim_mean - 0.4 * sim_std)

                for i, sim in enumerate(sims):
                    if sim < threshold:
                        boundaries.append(i + 1)
            except Exception as e:
                logger.warning(f"Error computing chunk embeddings: {e}")
                # Fallback: create a boundary every 3 chunks
                for i in range(3, len(chunks), 3):
                    boundaries.append(i)
        else:
            for i in range(3, len(chunks), 3):
                boundaries.append(i)

        if boundaries[-1] != len(chunks):
            boundaries.append(len(chunks))

        # Build topic blocks
        topics_found = []
        seen_titles = set()

        for b_idx in range(len(boundaries) - 1):
            start_c = boundaries[b_idx]
            end_c = boundaries[b_idx + 1]
            block_chunks = chunks[start_c:end_c]
            block_text = " ".join([c["text"] for c in block_chunks])
            t_start = block_chunks[0]["start_time"]
            t_end = block_chunks[-1]["end_time"]

            raw_label = self._label_block(block_text, model)
            # Ensure unique title if repeated
            clean_title = raw_label
            counter = 2
            while clean_title in seen_titles:
                clean_title = f"{raw_label} (Part {counter})"
                counter += 1
            seen_titles.add(clean_title)

            # Summarize block by picking the most representative 1-2 sentences
            sentences = [s.strip() for s in re.split(r"(?<=[.?!])\s+", block_text) if len(s.strip()) > 15]
            summary = " ".join(sentences[:2]) if sentences else block_text[:180]

            topics_found.append({
                "topic_name": clean_title,
                "start_time": round(float(t_start), 2),
                "end_time": round(float(t_end), 2),
                "summary": summary
            })

        return topics_found

topic_segmenter = TopicSegmenter()
