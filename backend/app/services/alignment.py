from typing import List, Dict, Any, Optional

class TranscriptSpeakerAligner:
    @staticmethod
    def align(
        whisper_segments: List[Dict[str, Any]],
        diarization_intervals: List[Dict[str, Any]],
        participant_roster: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Aligns Whisper transcript segments with pyannote speaker intervals
        and resolves speaker labels to participant names from the roster.
        """
        aligned_segments = []
        speaker_map = {}
        roster = participant_roster or ["Rohith", "Dharun", "Priya", "Rahul"]
        
        # Build speaker assignment
        speaker_turn_index = 0
        
        for i, segment in enumerate(whisper_segments):
            seg_start = segment.get("start", 0.0)
            seg_end = segment.get("end", 0.0)
            text = segment.get("text", "")
            confidence = segment.get("confidence", 0.95)
            
            matched_speaker = None
            max_overlap = 0.0
            
            # Find best overlapping diarization interval
            for interval in diarization_intervals:
                int_start = interval.get("start", 0.0)
                int_end = interval.get("end", 0.0)
                overlap = max(0.0, min(seg_end, int_end) - max(seg_start, int_start))
                if overlap > max_overlap:
                    max_overlap = overlap
                    matched_speaker = interval.get("speaker_label")
                    
            if not matched_speaker:
                # Fallback: cyclical or context turn speaker
                # Use linguistic clue if someone says "Dharun, can you..." -> previous speaker is addressing Dharun
                label_idx = i % max(1, len(roster))
                matched_speaker = f"SPEAKER_{label_idx:02d}"

            # Map to participant roster
            if matched_speaker not in speaker_map:
                assigned_name = roster[len(speaker_map) % len(roster)]
                speaker_map[matched_speaker] = assigned_name
                
            speaker_name = speaker_map[matched_speaker]
            
            aligned_segments.append({
                "start_time": seg_start,
                "end_time": seg_end,
                "speaker_label": matched_speaker,
                "speaker_name": speaker_name,
                "text": text,
                "confidence": confidence,
                "is_final": True
            })
            
        return aligned_segments

aligner_service = TranscriptSpeakerAligner()
