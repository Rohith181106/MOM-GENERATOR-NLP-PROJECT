import os
import wave
import logging
import numpy as np
from typing import List, Dict, Any, Optional

logger = logging.getLogger('mom_backend.diarization')

class SpeakerDiarizationService:
    def __init__(self):
        self._pipeline = None
        self._initialized = False

    def _get_pipeline(self):
        if not self._initialized:
            try:
                hf_token = os.environ.get("HUGGINGFACE_TOKEN") or os.environ.get("HF_TOKEN")
                if hf_token:
                    from pyannote.audio import Pipeline
                    logger.info("Initializing pyannote.audio pretrained diarization pipeline with HF token...")
                    self._pipeline = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1",
                        use_auth_token=hf_token
                    )
                else:
                    self._pipeline = None
            except Exception as e:
                logger.info(f"pyannote pipeline not directly loadable: {e}. Using acoustic feature clustering diarizer.")
                self._pipeline = None
            self._initialized = True
        return self._pipeline

    def _cluster_acoustic_features(self, wav_path: str, num_speakers: int = 2) -> List[Dict[str, Any]]:
        """
        Performs genuine acoustic spectral & energy feature extraction and Agglomerative Clustering
        on the audio waveform to identify speaker turns (SPEAKER_00, SPEAKER_01, etc.).
        """
        try:
            from scipy.io import wavfile
            from sklearn.cluster import AgglomerativeClustering

            rate, data = wavfile.read(wav_path)
            if data.ndim > 1:
                data = data.mean(axis=1)

            # Normalize to float32 between -1.0 and 1.0
            if data.dtype != np.float32 and data.dtype != np.float64:
                max_val = np.iinfo(data.dtype).max if np.issubdtype(data.dtype, np.integer) else 1.0
                data = data.astype(np.float32) / float(max_val)

            total_duration = len(data) / float(rate)
            if total_duration < 1.0:
                return [{"start": 0.0, "end": round(total_duration, 2), "speaker_label": "SPEAKER_00"}]

            window_sec = 1.0
            step_sec = 0.5
            window_samples = int(window_sec * rate)
            step_samples = int(step_sec * rate)

            features = []
            valid_windows = []

            # Voice Activity Detection (RMS threshold)
            global_rms = np.sqrt(np.mean(data**2))
            silence_thresh = max(0.005, global_rms * 0.25)

            for idx, start_sample in enumerate(range(0, len(data) - window_samples + 1, step_samples)):
                chunk = data[start_sample : start_sample + window_samples]
                rms = np.sqrt(np.mean(chunk**2))
                if rms < silence_thresh:
                    continue

                # Compute spectral features
                fft_mag = np.abs(np.fft.rfft(chunk * np.hanning(len(chunk))))
                freqs = np.fft.rfftfreq(len(chunk), d=1.0 / rate)

                # Spectral centroid
                sum_mag = np.sum(fft_mag)
                if sum_mag > 1e-6:
                    centroid = np.sum(freqs * fft_mag) / sum_mag
                else:
                    centroid = 0.0

                # 6 frequency sub-band energies
                bands = [
                    (50, 300), (300, 600), (600, 1200),
                    (1200, 2400), (2400, 4000), (4000, 8000)
                ]
                band_energies = []
                for low, high in bands:
                    band_idx = (freqs >= low) & (freqs < high)
                    band_energies.append(np.sum(fft_mag[band_idx]) if np.any(band_idx) else 0.0)

                feat_vector = [centroid, rms] + band_energies
                features.append(feat_vector)
                start_t = start_sample / float(rate)
                valid_windows.append((start_t, start_t + window_sec))

            if not features:
                return [{"start": 0.0, "end": round(total_duration, 2), "speaker_label": "SPEAKER_00"}]

            X = np.array(features)
            # Normalize features
            feat_mean = np.mean(X, axis=0)
            feat_std = np.std(X, axis=0) + 1e-6
            X_norm = (X - feat_mean) / feat_std

            n_clusters = min(max(2, num_speakers or 2), len(valid_windows))
            clustering = AgglomerativeClustering(n_clusters=n_clusters)
            labels = clustering.fit_predict(X_norm)

            # Merge contiguous windows with identical speaker cluster
            raw_intervals = []
            for (start_t, end_t), lab in zip(valid_windows, labels):
                raw_intervals.append({
                    "start": start_t,
                    "end": end_t,
                    "speaker_label": f"SPEAKER_{lab:02d}"
                })

            merged = []
            for item in raw_intervals:
                if not merged:
                    merged.append(item)
                else:
                    last = merged[-1]
                    if last["speaker_label"] == item["speaker_label"] and (item["start"] - last["end"] <= 0.8):
                        last["end"] = max(last["end"], item["end"])
                    else:
                        merged.append(item)

            for m in merged:
                m["start"] = round(m["start"], 2)
                m["end"] = round(m["end"], 2)

            return merged

        except Exception as e:
            logger.error(f"Acoustic clustering failed: {e}")
            return []

    def diarize_audio(self, audio_path: str, num_speakers: int = None) -> List[Dict[str, Any]]:
        """
        Diarizes an audio file to determine who spoke when.
        Returns intervals with start, end, and speaker_label (e.g. SPEAKER_00, SPEAKER_01)
        """
        if not audio_path or not os.path.exists(audio_path):
            return []

        pipeline = self._get_pipeline()
        if pipeline:
            try:
                diarization = pipeline(audio_path, num_speakers=num_speakers)
                speaker_turns = []
                for turn, _, speaker in diarization.itertracks(yield_label=True):
                    speaker_turns.append({
                        "start": round(turn.start, 2),
                        "end": round(turn.end, 2),
                        "speaker_label": speaker
                    })
                if speaker_turns:
                    return speaker_turns
            except Exception as e:
                logger.error(f"Error in pyannote diarization: {e}")

        # Ensure WAV format for acoustic clustering
        wav_path = audio_path
        if not audio_path.endswith("_extracted_16k.wav"):
            try:
                from backend.app.services.speech_to_text import stt_service
                wav_path = stt_service.extract_audio_to_wav(audio_path)
            except Exception as ex:
                logger.warning(f"Could not convert to 16k wav for diarization: {ex}")
                wav_path = audio_path

        return self._cluster_acoustic_features(wav_path, num_speakers=num_speakers or 2)

diarization_service = SpeakerDiarizationService()

