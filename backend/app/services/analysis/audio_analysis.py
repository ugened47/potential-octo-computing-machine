"""Audio analysis service for highlight detection."""

import logging
from dataclasses import dataclass
from pathlib import Path

import av
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class AudioSegment:
    """Represents an analyzed audio segment."""

    start_time: float
    end_time: float
    audio_score: int
    energy_level: float
    is_high_energy: bool


class AudioAnalysisService:
    """
    Service for analyzing audio features from videos.

    Extracts audio waveform, calculates energy levels, detects high-energy
    segments, and scores audio features on a 0-100 scale.
    """

    def __init__(
        self,
        window_size: float = 0.5,
        energy_threshold: float = 0.6,
        high_energy_duration: float = 3.0,
    ):
        """
        Initialize audio analysis service.

        Args:
            window_size: Size of analysis window in seconds (default: 0.5)
            energy_threshold: Threshold for high-energy detection (default: 0.6)
            high_energy_duration: Min duration for sustained high energy (default: 3.0)
        """
        self.window_size = window_size
        self.energy_threshold = energy_threshold
        self.high_energy_duration = high_energy_duration

    def analyze_video(self, video_path: str | Path) -> list[AudioSegment]:
        """
        Analyze audio from video file.

        Args:
            video_path: Path to video file

        Returns:
            List of AudioSegment objects with scores and energy levels
        """
        video_path = Path(video_path)

        if not video_path.exists():
            logger.error(f"Video file not found: {video_path}")
            return []

        try:
            # Extract audio data from video
            audio_data, sample_rate = self._extract_audio(video_path)

            if audio_data is None or len(audio_data) == 0:
                logger.warning(f"No audio data found in video: {video_path}")
                return []

            # Calculate energy for each window
            energy_windows = self._calculate_energy_windows(audio_data, sample_rate)

            # Detect high-energy segments
            segments = self._detect_segments(energy_windows)

            # Calculate scores for each segment
            scored_segments = self._score_segments(segments, energy_windows)

            return scored_segments

        except Exception as e:
            logger.error(f"Error analyzing audio from {video_path}: {e}")
            return []

    def _extract_audio(self, video_path: Path) -> tuple[np.ndarray | None, int]:
        """
        Extract audio waveform from video using PyAV.

        Args:
            video_path: Path to video file

        Returns:
            Tuple of (audio data as numpy array, sample rate)
        """
        try:
            container = av.open(str(video_path))
            audio_stream = next(
                (s for s in container.streams if s.type == "audio"), None
            )

            if audio_stream is None:
                logger.warning(f"No audio stream found in video: {video_path}")
                return None, 0

            # Resample to 16kHz for consistent processing
            audio_stream.codec_context.sample_rate = 16000
            sample_rate = 16000

            # Extract audio frames
            audio_frames = []
            for frame in container.decode(audio=0):
                audio_array = frame.to_ndarray()
                # Convert to mono if stereo
                if len(audio_array.shape) > 1:
                    audio_array = audio_array.mean(axis=0)
                audio_frames.append(audio_array)

            container.close()

            if not audio_frames:
                return None, sample_rate

            # Concatenate all frames
            audio_data = np.concatenate(audio_frames)

            return audio_data, sample_rate

        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            return None, 0

    def _calculate_energy_windows(
        self, audio_data: np.ndarray, sample_rate: int
    ) -> list[tuple[float, float, float]]:
        """
        Calculate audio energy (RMS) for each window.

        Args:
            audio_data: Audio waveform as numpy array
            sample_rate: Sample rate in Hz

        Returns:
            List of (start_time, end_time, energy_level) tuples
        """
        window_samples = int(self.window_size * sample_rate)
        hop_samples = window_samples  # No overlap for simplicity

        energy_windows = []

        for i in range(0, len(audio_data), hop_samples):
            window = audio_data[i : i + window_samples]

            if len(window) < window_samples // 2:  # Skip small windows at end
                break

            # Calculate RMS energy
            rms_energy = np.sqrt(np.mean(window**2))

            # Normalize energy to 0-1 range (assuming max RMS ~0.5 for typical audio)
            normalized_energy = min(rms_energy / 0.5, 1.0)

            start_time = i / sample_rate
            end_time = (i + len(window)) / sample_rate

            energy_windows.append((start_time, end_time, normalized_energy))

        return energy_windows

    def _detect_segments(
        self, energy_windows: list[tuple[float, float, float]]
    ) -> list[tuple[float, float]]:
        """
        Detect high-energy segments and sustained periods.

        Args:
            energy_windows: List of (start_time, end_time, energy_level) tuples

        Returns:
            List of (start_time, end_time) tuples for detected segments
        """
        segments = []
        current_segment_start = None
        last_high_energy_time = None

        for start_time, end_time, energy_level in energy_windows:
            is_high_energy = energy_level >= self.energy_threshold

            if is_high_energy:
                if current_segment_start is None:
                    current_segment_start = start_time
                last_high_energy_time = end_time
            else:
                # End segment if we had one
                if current_segment_start is not None:
                    segment_duration = last_high_energy_time - current_segment_start
                    # Only keep segments that meet minimum duration
                    if segment_duration >= self.high_energy_duration:
                        segments.append((current_segment_start, last_high_energy_time))
                    current_segment_start = None

        # Handle segment at end of audio
        if current_segment_start is not None and last_high_energy_time is not None:
            segment_duration = last_high_energy_time - current_segment_start
            if segment_duration >= self.high_energy_duration:
                segments.append((current_segment_start, last_high_energy_time))

        # Also detect energy peaks (sudden changes)
        segments.extend(self._detect_energy_peaks(energy_windows))

        # Remove overlaps and sort
        segments = self._merge_overlapping_segments(segments)

        return segments

    def _detect_energy_peaks(
        self, energy_windows: list[tuple[float, float, float]]
    ) -> list[tuple[float, float]]:
        """
        Detect sudden energy changes (peaks after quiet periods).

        Args:
            energy_windows: List of (start_time, end_time, energy_level) tuples

        Returns:
            List of (start_time, end_time) tuples for peak segments
        """
        peaks = []

        for i in range(1, len(energy_windows)):
            prev_start, prev_end, prev_energy = energy_windows[i - 1]
            curr_start, curr_end, curr_energy = energy_windows[i]

            # Detect significant increase in energy
            if prev_energy < 0.3 and curr_energy > 0.7:
                # Include a few windows around the peak
                peak_start = prev_start
                peak_end = min(
                    curr_end + 2.0, energy_windows[-1][1]
                )  # 2 seconds after peak
                peaks.append((peak_start, peak_end))

        return peaks

    def _merge_overlapping_segments(
        self, segments: list[tuple[float, float]]
    ) -> list[tuple[float, float]]:
        """
        Merge overlapping segments.

        Args:
            segments: List of (start_time, end_time) tuples

        Returns:
            List of non-overlapping (start_time, end_time) tuples
        """
        if not segments:
            return []

        # Sort by start time
        sorted_segments = sorted(segments, key=lambda x: x[0])

        merged = [sorted_segments[0]]

        for current_start, current_end in sorted_segments[1:]:
            last_start, last_end = merged[-1]

            # Check for overlap
            if current_start <= last_end:
                # Merge segments
                merged[-1] = (last_start, max(last_end, current_end))
            else:
                merged.append((current_start, current_end))

        return merged

    def _score_segments(
        self,
        segments: list[tuple[float, float]],
        energy_windows: list[tuple[float, float, float]],
    ) -> list[AudioSegment]:
        """
        Calculate scores for detected segments.

        Args:
            segments: List of (start_time, end_time) tuples
            energy_windows: List of (start_time, end_time, energy_level) tuples

        Returns:
            List of AudioSegment objects with scores
        """
        scored_segments = []

        for seg_start, seg_end in segments:
            # Find all energy windows within this segment
            segment_energies = [
                energy
                for start, end, energy in energy_windows
                if start >= seg_start and end <= seg_end
            ]

            if not segment_energies:
                continue

            # Calculate average energy for segment
            avg_energy = np.mean(segment_energies)

            # Calculate score on 0-100 scale
            # High energy (>0.7): 80-100
            # Medium energy (0.5-0.7): 50-79
            # Low energy (<0.5): 0-49
            if avg_energy >= 0.7:
                score = int(80 + (avg_energy - 0.7) / 0.3 * 20)
            elif avg_energy >= 0.5:
                score = int(50 + (avg_energy - 0.5) / 0.2 * 29)
            else:
                score = int(avg_energy / 0.5 * 49)

            score = max(0, min(100, score))  # Clamp to 0-100

            scored_segments.append(
                AudioSegment(
                    start_time=seg_start,
                    end_time=seg_end,
                    audio_score=score,
                    energy_level=avg_energy,
                    is_high_energy=avg_energy >= self.energy_threshold,
                )
            )

        return scored_segments
