import os
import io
import wave
import tempfile
import logging
import subprocess
from typing import List, Dict, Any, Optional

logger = logging.getLogger('mom_backend.asr')

class SpeechToTextService:
    def __init__(self, model_size="base"):
        self.model_size = model_size
        self._model = None
        self._initialized = False

    def _get_model(self):
        if not self._initialized:
            try:
                from faster_whisper import WhisperModel
                device = "cpu"
                compute_type = "int8"
                logger.info(f"Loading faster-whisper model ({self.model_size}) on {device} ({compute_type})...")
                self._model = WhisperModel(self.model_size, device=device, compute_type=compute_type)
                logger.info("faster-whisper model loaded successfully.")
            except Exception as e:
                logger.error(f"faster-whisper failed to load: {e}")
                self._model = None
            self._initialized = True
        return self._model

    def extract_audio_to_wav(self, media_path: str) -> str:
        """
        Extracts/converts audio from any video (MP4, MOV, WebM, AVI, MKV)
        or audio file (MP3, M4A, FLAC, OGG, WAV) to standardized 16kHz mono 16-bit PCM WAV.
        """
        if not os.path.exists(media_path):
            raise FileNotFoundError(f"Media file not found at: {media_path}")

        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            ffmpeg_exe = "ffmpeg"

        base_name, _ = os.path.splitext(media_path)
        wav_path = f"{base_name}_extracted_16k.wav"

        cmd = [
            ffmpeg_exe,
            "-y",
            "-i", media_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            wav_path
        ]
        logger.info(f"Extracting 16kHz mono WAV from '{media_path}' via ffmpeg...")
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            err_msg = res.stderr.decode("utf-8", errors="ignore")
            logger.error(f"FFmpeg extraction failed: {err_msg}")
            raise RuntimeError(f"FFmpeg extraction failed: {err_msg}")

        if not os.path.exists(wav_path) or os.path.getsize(wav_path) == 0:
            raise RuntimeError(f"Extracted audio WAV is missing or empty for '{media_path}'")

        return wav_path

    def transcribe_audio_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Transcribe a recorded meeting audio or video file using faster-whisper.
        Guaranteed: No synthetic or fallback transcripts. Raises error if processing fails.
        """
        if not file_path or not os.path.exists(file_path):
            raise FileNotFoundError(f"Media file does not exist: {file_path}")

        if not file_path.endswith("_extracted_16k.wav"):
            wav_path = self.extract_audio_to_wav(file_path)
        else:
            wav_path = file_path

        model = self._get_model()
        if not model:
            raise RuntimeError("faster-whisper model is not available or failed to initialize.")

        try:
            logger.info(f"Starting faster-whisper transcription on: {wav_path}")
            segments, info = model.transcribe(wav_path, beam_size=5, word_timestamps=True)
            results = []
            for s in segments:
                text = s.text.strip()
                if text:
                    results.append({
                        "start": round(s.start, 2),
                        "end": round(s.end, 2),
                        "text": text,
                        "confidence": round(getattr(s, "avg_logprob", 0.95), 3)
                    })
            logger.info(f"Transcription complete: {len(results)} segments detected (language={info.language}).")
            return results
        except Exception as e:
            logger.error(f"Error during faster-whisper transcription: {e}")
            raise RuntimeError(f"Transcription failed: {str(e)}")

    def transcribe_audio_chunk(self, audio_bytes: bytes, current_offset_sec: float = 0.0) -> Optional[Dict[str, Any]]:
        """
        Transcribes a live audio chunk received over WebSocket streaming.
        """
        if not audio_bytes or len(audio_bytes) < 1000:
            return None

        model = self._get_model()
        if not model:
            return None

        tmp_raw = None
        tmp_wav = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".raw", delete=False) as f:
                f.write(audio_bytes)
                tmp_raw = f.name

            try:
                import imageio_ffmpeg
                ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            except Exception:
                ffmpeg_exe = "ffmpeg"

            tmp_wav = tmp_raw + ".wav"
            cmd = [
                ffmpeg_exe,
                "-y",
                "-i", tmp_raw,
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                tmp_wav
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            target_file = tmp_wav if (os.path.exists(tmp_wav) and os.path.getsize(tmp_wav) > 0) else tmp_raw
            segments, _ = model.transcribe(target_file, beam_size=3)

            text_list = [s.text.strip() for s in segments if s.text.strip()]
            if text_list:
                return {
                    "text": " ".join(text_list),
                    "start": round(current_offset_sec, 2),
                    "end": round(current_offset_sec + max(1.0, len(audio_bytes) / 32000.0), 2),
                    "confidence": 0.92
                }
        except Exception as e:
            logger.error(f"Live chunk transcription error: {e}")
        finally:
            if tmp_raw and os.path.exists(tmp_raw):
                try: os.remove(tmp_raw)
                except Exception: pass
            if tmp_wav and os.path.exists(tmp_wav):
                try: os.remove(tmp_wav)
                except Exception: pass

        return None

stt_service = SpeechToTextService()
