import json
import logging
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.future import select

from backend.app.core.database import AsyncSessionLocal
from backend.app.models.orm_models import Meeting, TranscriptSegment, Participant
from backend.app.services.speech_to_text import stt_service
from backend.app.services.action_detector import action_detector
from backend.app.services.decision_detector import decision_detector

logger = logging.getLogger('mom_backend.websocket')

class MeetingConnectionManager:
    def __init__(self):
        # meeting_id -> Set of active WebSockets
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # meeting_id -> current audio offset in seconds
        self.meeting_timers: Dict[int, float] = {}

    async def connect(self, meeting_id: int, websocket: WebSocket):
        await websocket.accept()
        if meeting_id not in self.active_connections:
            self.active_connections[meeting_id] = set()
            self.meeting_timers[meeting_id] = 0.0
        self.active_connections[meeting_id].add(websocket)
        logger.info(f"WebSocket client connected to meeting {meeting_id}")

    def disconnect(self, meeting_id: int, websocket: WebSocket):
        if meeting_id in self.active_connections:
            self.active_connections[meeting_id].discard(websocket)
            if not self.active_connections[meeting_id]:
                del self.active_connections[meeting_id]
                self.meeting_timers.pop(meeting_id, None)
        logger.info(f"WebSocket client disconnected from meeting {meeting_id}")

    async def broadcast_event(self, meeting_id: int, event_data: dict):
        if meeting_id in self.active_connections:
            msg = json.dumps(event_data)
            for connection in list(self.active_connections[meeting_id]):
                try:
                    await connection.send_text(msg)
                except Exception as e:
                    logger.warning(f"Error broadcasting to socket: {e}")

    async def handle_audio_stream_or_message(self, meeting_id: int, data: str or bytes, user_id: int):
        """
        Processes incoming live audio chunks or JSON control messages.
        """
        if isinstance(data, bytes):
            # Binary audio chunk from microphone
            current_offset = self.meeting_timers.get(meeting_id, 0.0)
            res = stt_service.transcribe_audio_chunk(data, current_offset)
            if res and res.get("text"):
                chunk_text = res["text"].strip()
                self.meeting_timers[meeting_id] = res["end"]
                
                # Check if it looks like a complete utterance
                is_sentence = chunk_text.endswith((".", "?", "!")) or len(chunk_text.split()) >= 6
                if is_sentence:
                    speaker_label = "SPEAKER_00"
                    speaker_name = "Speaker"
                    async with AsyncSessionLocal() as session:
                        segment = TranscriptSegment(
                            meeting_id=meeting_id,
                            speaker_label=speaker_label,
                            speaker_name=speaker_name,
                            start_time=res["start"],
                            end_time=res["end"],
                            text=chunk_text,
                            confidence=res.get("confidence", 0.92),
                            is_final=True
                        )
                        session.add(segment)
                        await session.commit()
                        await session.refresh(segment)
                        seg_id = segment.id

                    await self.broadcast_event(meeting_id, {
                        "type": "transcript_final",
                        "id": seg_id,
                        "meeting_id": meeting_id,
                        "speaker": speaker_name,
                        "speaker_label": speaker_label,
                        "start": res["start"],
                        "end": res["end"],
                        "text": chunk_text
                    })

                    # Check for live action detection
                    action_item = action_detector.detect_action_in_text(chunk_text, speaker_name=speaker_name)
                    if action_item:
                        await self.broadcast_event(meeting_id, {
                            "type": "action_detected",
                            "meeting_id": meeting_id,
                            "task": action_item["task"],
                            "owner": action_item["owner"],
                            "deadline": action_item["deadline"],
                            "evidence": chunk_text
                        })

                    # Check for live decision detection
                    decision = decision_detector.detect_decision_in_text(chunk_text)
                    if decision:
                        await self.broadcast_event(meeting_id, {
                            "type": "decision_detected",
                            "meeting_id": meeting_id,
                            "decision": decision["decision"],
                            "evidence": chunk_text
                        })
                else:
                    await self.broadcast_event(meeting_id, {
                        "type": "transcript_partial",
                        "meeting_id": meeting_id,
                        "text": chunk_text
                    })
            return

        try:
            payload = json.loads(data)
        except Exception:
            return

        msg_type = payload.get("type")

        if msg_type == "client_speech":
            # Client provided a speech turn (e.g. from Web Speech API / mic streamer)
            text = payload.get("text", "").strip()
            speaker_name = payload.get("speaker", "Speaker")
            speaker_label = payload.get("speaker_label", "SPEAKER_00")
            is_final = payload.get("is_final", True)
            start_time = round(payload.get("start_time", self.meeting_timers.get(meeting_id, 0.0)), 2)
            end_time = round(payload.get("end_time", start_time + 4.0), 2)
            self.meeting_timers[meeting_id] = end_time

            if not text:
                return

            if not is_final:
                # Broadcast interim transcript
                await self.broadcast_event(meeting_id, {
                    "type": "transcript_partial",
                    "meeting_id": meeting_id,
                    "speaker": speaker_name,
                    "speaker_label": speaker_label,
                    "text": text
                })
                return

            # Finalize transcript segment & persist to database
            async with AsyncSessionLocal() as session:
                segment = TranscriptSegment(
                    meeting_id=meeting_id,
                    speaker_label=speaker_label,
                    speaker_name=speaker_name,
                    start_time=start_time,
                    end_time=end_time,
                    text=text,
                    confidence=0.96,
                    is_final=True
                )
                session.add(segment)
                await session.commit()
                await session.refresh(segment)
                segment_id = segment.id

            # Broadcast final transcript segment to all participants
            await self.broadcast_event(meeting_id, {
                "type": "transcript_final",
                "id": segment_id,
                "meeting_id": meeting_id,
                "speaker": speaker_name,
                "speaker_label": speaker_label,
                "start": start_time,
                "end": end_time,
                "text": text
            })

            # Check for live action item detection
            action_item = action_detector.detect_action_in_text(text, speaker_name=speaker_name)
            if action_item:
                await self.broadcast_event(meeting_id, {
                    "type": "action_detected",
                    "meeting_id": meeting_id,
                    "task": action_item["task"],
                    "owner": action_item["owner"],
                    "deadline": action_item["deadline"],
                    "evidence": text
                })

            # Check for live decision detection
            decision = decision_detector.detect_decision_in_text(text)
            if decision:
                await self.broadcast_event(meeting_id, {
                    "type": "decision_detected",
                    "meeting_id": meeting_id,
                    "decision": decision["decision"],
                    "evidence": text
                })

ws_manager = MeetingConnectionManager()
