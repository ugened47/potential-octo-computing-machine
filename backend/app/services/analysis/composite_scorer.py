"""Composite scoring service for highlight detection."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ScoreWeights:
    """Weights for component scores."""

    audio_energy: float = 0.35
    scene_change: float = 0.20
    speech_density: float = 0.25
    keyword: float = 0.20

    def normalize(self) -> "ScoreWeights":
        """Normalize weights to sum to 1.0."""
        total = (
            self.audio_energy + self.scene_change + self.speech_density + self.keyword
        )
        if total == 0:
            return self

        return ScoreWeights(
            audio_energy=self.audio_energy / total,
            scene_change=self.scene_change / total,
            speech_density=self.speech_density / total,
            keyword=self.keyword / total,
        )


@dataclass
class ScoredSegment:
    """Segment with composite score and all component scores."""

    start_time: float
    end_time: float
    overall_score: int
    audio_energy_score: int
    scene_change_score: int
    speech_density_score: int
    keyword_score: int
    detected_keywords: list[str]
    confidence_level: float
    duration_seconds: float


class CompositeScorer:
    """
    Service for calculating composite scores from component scores.

    Combines audio, video, speech, and keyword scores using weighted
    averages and applies bonus multipliers for aligned signals.
    """

    def __init__(self, weights: ScoreWeights | None = None):
        """
        Initialize composite scorer.

        Args:
            weights: Score weights (default: ScoreWeights with default values)
        """
        self.weights = weights if weights is not None else ScoreWeights()
        self.weights = self.weights.normalize()

    def score_segments(
        self,
        audio_segments: list,
        video_segments: list,
        speech_segments: list,
        keyword_segments: list,
        video_duration: float,
    ) -> list[ScoredSegment]:
        """
        Calculate composite scores for all segments.

        Args:
            audio_segments: List of AudioSegment objects
            video_segments: List of SceneSegment objects
            speech_segments: List of SpeechSegment objects
            keyword_segments: List of KeywordSegment objects
            video_duration: Total video duration in seconds

        Returns:
            List of ScoredSegment objects with composite scores
        """
        try:
            # Create time windows covering the video
            windows = self._create_time_windows(
                audio_segments,
                video_segments,
                speech_segments,
                keyword_segments,
                video_duration,
            )

            # Score each window
            scored_segments = []
            for window in windows:
                segment = self._score_window(
                    window,
                    audio_segments,
                    video_segments,
                    speech_segments,
                    keyword_segments,
                )
                if segment:
                    scored_segments.append(segment)

            return scored_segments

        except Exception as e:
            logger.error(f"Error calculating composite scores: {e}")
            return []

    def _create_time_windows(
        self,
        audio_segments: list,
        video_segments: list,
        speech_segments: list,
        keyword_segments: list,
        video_duration: float,
        window_size: float = 10.0,
    ) -> list[tuple[float, float]]:
        """
        Create time windows for scoring.

        Args:
            audio_segments: List of AudioSegment objects
            video_segments: List of SceneSegment objects
            speech_segments: List of SpeechSegment objects
            keyword_segments: List of KeywordSegment objects
            video_duration: Total video duration
            window_size: Window size in seconds

        Returns:
            List of (start_time, end_time) tuples
        """
        # Collect all significant time points
        time_points = set([0.0, video_duration])

        for seg in audio_segments:
            time_points.add(seg.start_time)
            time_points.add(seg.end_time)

        for seg in video_segments:
            time_points.add(seg.start_time)
            time_points.add(seg.end_time)

        for seg in speech_segments:
            time_points.add(seg.start_time)
            time_points.add(seg.end_time)

        for seg in keyword_segments:
            time_points.add(seg.start_time)
            time_points.add(seg.end_time)

        # Sort time points
        sorted_points = sorted(time_points)

        # Create windows
        windows = []
        for i in range(len(sorted_points) - 1):
            start = sorted_points[i]
            end = sorted_points[i + 1]

            # Skip very small windows
            if end - start < 1.0:
                continue

            windows.append((start, end))

        return windows

    def _score_window(
        self,
        window: tuple[float, float],
        audio_segments: list,
        video_segments: list,
        speech_segments: list,
        keyword_segments: list,
    ) -> ScoredSegment | None:
        """
        Score a single time window.

        Args:
            window: (start_time, end_time) tuple
            audio_segments: List of AudioSegment objects
            video_segments: List of SceneSegment objects
            speech_segments: List of SpeechSegment objects
            keyword_segments: List of KeywordSegment objects

        Returns:
            ScoredSegment or None
        """
        start_time, end_time = window
        duration = end_time - start_time

        # Get scores for each component
        audio_score = self._get_score_for_window(window, audio_segments, "audio_score")
        scene_score = self._get_score_for_window(window, video_segments, "scene_score")
        speech_score = self._get_score_for_window(
            window, speech_segments, "speech_score"
        )
        keyword_score = self._get_score_for_window(
            window, keyword_segments, "keyword_score"
        )

        # Get detected keywords
        detected_keywords = self._get_keywords_for_window(window, keyword_segments)

        # Calculate weighted average
        overall_score = (
            audio_score * self.weights.audio_energy
            + scene_score * self.weights.scene_change
            + speech_score * self.weights.speech_density
            + keyword_score * self.weights.keyword
        )

        # Apply bonus multipliers
        overall_score = self._apply_bonuses(
            overall_score,
            audio_score,
            scene_score,
            speech_score,
            keyword_score,
            duration,
        )

        # Normalize to 0-100
        overall_score = max(0, min(100, int(overall_score)))

        # Calculate confidence based on how many components have scores
        confidence = self._calculate_confidence(
            audio_score, scene_score, speech_score, keyword_score
        )

        return ScoredSegment(
            start_time=start_time,
            end_time=end_time,
            overall_score=overall_score,
            audio_energy_score=audio_score,
            scene_change_score=scene_score,
            speech_density_score=speech_score,
            keyword_score=keyword_score,
            detected_keywords=detected_keywords,
            confidence_level=confidence,
            duration_seconds=duration,
        )

    def _get_score_for_window(
        self, window: tuple[float, float], segments: list, score_attr: str
    ) -> int:
        """
        Get average score for window from segments.

        Args:
            window: (start_time, end_time) tuple
            segments: List of segment objects
            score_attr: Name of score attribute

        Returns:
            Average score (0-100)
        """
        start_time, end_time = window
        scores = []

        for seg in segments:
            # Check if segment overlaps with window
            if seg.end_time <= start_time or seg.start_time >= end_time:
                continue

            # Calculate overlap
            overlap_start = max(start_time, seg.start_time)
            overlap_end = min(end_time, seg.end_time)
            overlap_duration = overlap_end - overlap_start

            if overlap_duration > 0:
                score = getattr(seg, score_attr, 0)
                scores.append(score)

        if not scores:
            return 0

        # Return average score
        return int(sum(scores) / len(scores))

    def _get_keywords_for_window(
        self, window: tuple[float, float], keyword_segments: list
    ) -> list[str]:
        """
        Get all detected keywords for window.

        Args:
            window: (start_time, end_time) tuple
            keyword_segments: List of KeywordSegment objects

        Returns:
            List of unique keywords
        """
        start_time, end_time = window
        keywords = []

        for seg in keyword_segments:
            # Check if segment overlaps with window
            if seg.end_time <= start_time or seg.start_time >= end_time:
                continue

            keywords.extend(seg.detected_keywords)

        # Return unique keywords
        return list(set(keywords))

    def _apply_bonuses(
        self,
        base_score: float,
        audio_score: int,
        scene_score: int,
        speech_score: int,
        keyword_score: int,
        duration: float,
    ) -> float:
        """
        Apply bonus multipliers for aligned signals.

        Args:
            base_score: Base composite score
            audio_score: Audio energy score
            scene_score: Scene change score
            speech_score: Speech density score
            keyword_score: Keyword score
            duration: Segment duration

        Returns:
            Score with bonuses applied
        """
        bonus = 0.0

        # Multiple high signals aligned (2+ scores > 70): +10%
        high_scores = sum(
            1
            for score in [audio_score, scene_score, speech_score, keyword_score]
            if score > 70
        )
        if high_scores >= 2:
            bonus += 0.10

        # Sustained high scores (duration > 5s and score > 70): +15%
        if duration > 5.0 and base_score > 70:
            bonus += 0.15

        # Keywords + high energy (keyword > 50 and audio > 70): +20%
        if keyword_score > 50 and audio_score > 70:
            bonus += 0.20

        # Apply bonuses
        score_with_bonus = base_score * (1.0 + bonus)

        return score_with_bonus

    def _calculate_confidence(
        self,
        audio_score: int,
        scene_score: int,
        speech_score: int,
        keyword_score: int,
    ) -> float:
        """
        Calculate confidence based on component score availability.

        Args:
            audio_score: Audio score
            scene_score: Scene change score
            speech_score: Speech score
            keyword_score: Keyword score

        Returns:
            Confidence level (0-1)
        """
        # Count how many components have meaningful scores
        components_with_scores = sum(
            1
            for score in [audio_score, scene_score, speech_score, keyword_score]
            if score > 0
        )

        # Confidence based on number of components
        confidence = components_with_scores / 4.0

        return round(confidence, 2)
