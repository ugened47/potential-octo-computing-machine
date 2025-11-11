"""Speech pattern analysis service for highlight detection."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SpeechSegment:
    """Represents an analyzed speech segment."""

    start_time: float
    end_time: float
    speech_score: int
    words_per_minute: float
    pause_ratio: float
    word_count: int


class SpeechAnalysisService:
    """
    Service for analyzing speech patterns from transcripts.

    Analyzes speaking rate, pauses, speech density, and detects segments
    with increased energy or emphasis based on transcript word timestamps.
    """

    def __init__(
        self,
        window_size: float = 10.0,
        high_wpm_threshold: float = 160.0,
        low_wpm_threshold: float = 100.0,
    ):
        """
        Initialize speech analysis service.

        Args:
            window_size: Size of analysis window in seconds (default: 10.0)
            high_wpm_threshold: Threshold for high speaking rate (default: 160)
            low_wpm_threshold: Threshold for low speaking rate (default: 100)
        """
        self.window_size = window_size
        self.high_wpm_threshold = high_wpm_threshold
        self.low_wpm_threshold = low_wpm_threshold

    def analyze_transcript(
        self, word_timestamps: list[dict[str, any]]
    ) -> list[SpeechSegment]:
        """
        Analyze speech patterns from word-level timestamps.

        Args:
            word_timestamps: List of word timestamp dicts with keys:
                - word: str
                - start: float (seconds)
                - end: float (seconds)

        Returns:
            List of SpeechSegment objects with scores
        """
        if not word_timestamps:
            logger.warning("No word timestamps provided for speech analysis")
            return []

        try:
            # Create windows of words
            windows = self._create_windows(word_timestamps)

            # Analyze each window
            segments = []
            for window_words, window_start, window_end in windows:
                segment = self._analyze_window(window_words, window_start, window_end)
                if segment:
                    segments.append(segment)

            return segments

        except Exception as e:
            logger.error(f"Error analyzing speech patterns: {e}")
            return []

    def _create_windows(
        self, word_timestamps: list[dict[str, any]]
    ) -> list[tuple[list[dict], float, float]]:
        """
        Create sliding windows of words.

        Args:
            word_timestamps: List of word timestamp dicts

        Returns:
            List of (window_words, start_time, end_time) tuples
        """
        if not word_timestamps:
            return []

        windows = []
        i = 0

        while i < len(word_timestamps):
            window_start = word_timestamps[i]["start"]
            window_end = window_start + self.window_size

            # Collect words in this window
            window_words = []
            j = i
            while j < len(word_timestamps):
                word_data = word_timestamps[j]
                if word_data["start"] >= window_end:
                    break
                window_words.append(word_data)
                j += 1

            if window_words:
                actual_end = window_words[-1]["end"]
                windows.append((window_words, window_start, actual_end))

            # Move to next window (50% overlap)
            i += max(1, len(window_words) // 2)

        return windows

    def _analyze_window(
        self, words: list[dict[str, any]], start_time: float, end_time: float
    ) -> SpeechSegment | None:
        """
        Analyze a window of words.

        Args:
            words: List of word dicts in window
            start_time: Window start time
            end_time: Window end time

        Returns:
            SpeechSegment object or None
        """
        if not words:
            return None

        # Calculate speaking rate (words per minute)
        duration_minutes = (end_time - start_time) / 60.0
        if duration_minutes <= 0:
            return None

        word_count = len(words)
        wpm = word_count / duration_minutes

        # Calculate pause ratio (time between words vs speaking time)
        pause_ratio = self._calculate_pause_ratio(words)

        # Calculate speech density score (0-100)
        score = self._calculate_speech_score(wpm, pause_ratio)

        return SpeechSegment(
            start_time=start_time,
            end_time=end_time,
            speech_score=score,
            words_per_minute=wpm,
            pause_ratio=pause_ratio,
            word_count=word_count,
        )

    def _calculate_pause_ratio(self, words: list[dict[str, any]]) -> float:
        """
        Calculate ratio of pause time to speaking time.

        Args:
            words: List of word dicts

        Returns:
            Pause ratio (0-1)
        """
        if len(words) < 2:
            return 0.0

        total_pause_time = 0.0
        total_speaking_time = 0.0

        for i in range(len(words)):
            word = words[i]
            # Speaking time for this word
            speaking_time = word["end"] - word["start"]
            total_speaking_time += speaking_time

            # Pause time to next word
            if i < len(words) - 1:
                next_word = words[i + 1]
                pause_time = next_word["start"] - word["end"]
                if pause_time > 0:
                    total_pause_time += pause_time

        if total_speaking_time <= 0:
            return 0.0

        # Return ratio of pause to speaking time
        pause_ratio = total_pause_time / (total_speaking_time + total_pause_time)
        return min(pause_ratio, 1.0)

    def _calculate_speech_score(self, wpm: float, pause_ratio: float) -> int:
        """
        Calculate speech density score based on WPM and pause ratio.

        Args:
            wpm: Words per minute
            pause_ratio: Ratio of pause time (0-1)

        Returns:
            Speech score (0-100)
        """
        # Score based on speaking rate
        # High WPM (>160): 80-100
        # Medium WPM (100-160): 50-79
        # Low WPM (<100): 0-49
        if wpm >= self.high_wpm_threshold:
            wpm_score = 80 + min((wpm - self.high_wpm_threshold) / 40.0 * 20, 20)
        elif wpm >= self.low_wpm_threshold:
            wpm_score = (
                50 + (wpm - self.low_wpm_threshold) / 60.0 * 30
            )  # 100-160 WPM range
        else:
            wpm_score = wpm / self.low_wpm_threshold * 50  # 0-100 WPM range

        # Score based on pause ratio (less pause = higher score)
        # Low pauses (<0.2): High score
        # Medium pauses (0.2-0.4): Medium score
        # High pauses (>0.4): Low score
        if pause_ratio < 0.2:
            pause_score = 100 - pause_ratio / 0.2 * 20  # 80-100
        elif pause_ratio < 0.4:
            pause_score = 50 + (0.4 - pause_ratio) / 0.2 * 30  # 50-80
        else:
            pause_score = max((1.0 - pause_ratio) / 0.6 * 50, 0)  # 0-50

        # Combined score (weighted average)
        score = int(wpm_score * 0.6 + pause_score * 0.4)
        return max(0, min(100, score))
