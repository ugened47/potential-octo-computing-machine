"""Keyword-based scoring service for highlight detection."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Default highlight keywords
DEFAULT_HIGHLIGHT_KEYWORDS = [
    "important",
    "key",
    "best",
    "amazing",
    "wow",
    "incredible",
    "unbelievable",
    "watch",
    "look",
    "check",
    "awesome",
    "perfect",
    "great",
    "excellent",
    "fantastic",
]


@dataclass
class KeywordSegment:
    """Represents a segment with keyword matches."""

    start_time: float
    end_time: float
    keyword_score: int
    detected_keywords: list[str]
    keyword_count: int


class KeywordAnalysisService:
    """
    Service for keyword-based highlight scoring.

    Detects important keywords in transcripts and scores segments based
    on keyword presence, density, and clustering.
    """

    def __init__(
        self,
        highlight_keywords: list[str] | None = None,
        window_size: float = 10.0,
        cluster_bonus_threshold: int = 2,
    ):
        """
        Initialize keyword analysis service.

        Args:
            highlight_keywords: List of keywords to detect (default: DEFAULT_HIGHLIGHT_KEYWORDS)
            window_size: Size of analysis window in seconds (default: 10.0)
            cluster_bonus_threshold: Min keywords for cluster bonus (default: 2)
        """
        self.highlight_keywords = (
            highlight_keywords
            if highlight_keywords is not None
            else DEFAULT_HIGHLIGHT_KEYWORDS.copy()
        )
        # Convert to lowercase for case-insensitive matching
        self.highlight_keywords = [k.lower() for k in self.highlight_keywords]

        self.window_size = window_size
        self.cluster_bonus_threshold = cluster_bonus_threshold

    def analyze_transcript(
        self,
        word_timestamps: list[dict[str, any]],
        custom_keywords: list[str] | None = None,
    ) -> list[KeywordSegment]:
        """
        Analyze transcript for keyword matches.

        Args:
            word_timestamps: List of word timestamp dicts with keys:
                - word: str
                - start: float (seconds)
                - end: float (seconds)
            custom_keywords: Optional additional keywords to search for

        Returns:
            List of KeywordSegment objects with scores
        """
        if not word_timestamps:
            logger.warning("No word timestamps provided for keyword analysis")
            return []

        # Combine default and custom keywords
        keywords = self.highlight_keywords.copy()
        if custom_keywords:
            keywords.extend([k.lower() for k in custom_keywords])

        try:
            # Find keyword matches
            keyword_matches = self._find_keyword_matches(word_timestamps, keywords)

            if not keyword_matches:
                logger.info("No keywords found in transcript")
                return []

            # Create segments around keyword matches
            segments = self._create_keyword_segments(keyword_matches, word_timestamps)

            # Score segments
            scored_segments = self._score_segments(segments)

            return scored_segments

        except Exception as e:
            logger.error(f"Error analyzing keywords: {e}")
            return []

    def _find_keyword_matches(
        self, word_timestamps: list[dict[str, any]], keywords: list[str]
    ) -> list[tuple[float, str]]:
        """
        Find all keyword matches in transcript.

        Args:
            word_timestamps: List of word timestamp dicts
            keywords: List of keywords to search for

        Returns:
            List of (timestamp, keyword) tuples
        """
        matches = []

        for word_data in word_timestamps:
            word = word_data.get("word", "").lower().strip()
            timestamp = word_data.get("start", 0.0)

            # Check if word matches any keyword
            for keyword in keywords:
                if keyword in word or word in keyword:
                    matches.append((timestamp, keyword))
                    break  # Only count once per word

        return matches

    def _create_keyword_segments(
        self,
        keyword_matches: list[tuple[float, str]],
        word_timestamps: list[dict[str, any]],
    ) -> list[tuple[float, float, list[str]]]:
        """
        Create segments around keyword matches.

        Args:
            keyword_matches: List of (timestamp, keyword) tuples
            word_timestamps: List of word timestamp dicts

        Returns:
            List of (start_time, end_time, [keywords]) tuples
        """
        if not keyword_matches:
            return []

        segments = []
        i = 0

        while i < len(keyword_matches):
            match_time, keyword = keyword_matches[i]

            # Define segment window around keyword
            segment_start = max(0, match_time - self.window_size / 2)
            segment_end = match_time + self.window_size / 2

            # Collect all keywords in this window
            segment_keywords = [keyword]
            j = i + 1

            while j < len(keyword_matches):
                next_time, next_keyword = keyword_matches[j]
                if next_time <= segment_end:
                    segment_keywords.append(next_keyword)
                    j += 1
                else:
                    break

            # Adjust segment boundaries to actual word boundaries
            actual_start, actual_end = self._adjust_to_word_boundaries(
                segment_start, segment_end, word_timestamps
            )

            segments.append((actual_start, actual_end, segment_keywords))

            # Move to next non-overlapping segment
            i = j if j > i + 1 else i + 1

        return segments

    def _adjust_to_word_boundaries(
        self, start_time: float, end_time: float, word_timestamps: list[dict[str, any]]
    ) -> tuple[float, float]:
        """
        Adjust segment boundaries to word boundaries.

        Args:
            start_time: Proposed start time
            end_time: Proposed end time
            word_timestamps: List of word timestamp dicts

        Returns:
            Tuple of (adjusted_start, adjusted_end)
        """
        if not word_timestamps:
            return start_time, end_time

        # Find first word at or after start_time
        actual_start = start_time
        for word_data in word_timestamps:
            if word_data["start"] >= start_time:
                actual_start = word_data["start"]
                break

        # Find last word at or before end_time
        actual_end = end_time
        for word_data in reversed(word_timestamps):
            if word_data["end"] <= end_time:
                actual_end = word_data["end"]
                break

        return actual_start, actual_end

    def _score_segments(
        self, segments: list[tuple[float, float, list[str]]]
    ) -> list[KeywordSegment]:
        """
        Score segments based on keyword presence and density.

        Args:
            segments: List of (start_time, end_time, [keywords]) tuples

        Returns:
            List of KeywordSegment objects with scores
        """
        scored_segments = []

        for start_time, end_time, keywords in segments:
            keyword_count = len(keywords)

            # Base score based on keyword count
            # Multiple keywords (>=3): 80-100
            # Two keywords: 60-79
            # Single keyword: 50-59
            # Related/minor (bonus): 30-49
            if keyword_count >= 3:
                base_score = 80 + min(keyword_count - 3, 5) * 4  # Up to 100
            elif keyword_count == 2:
                base_score = 60 + 10  # 70
            else:
                base_score = 50

            # Cluster bonus for multiple nearby keywords
            if keyword_count >= self.cluster_bonus_threshold:
                cluster_bonus = min(keyword_count * 5, 20)  # Up to +20
                base_score += cluster_bonus

            # Unique keyword bonus (more variety = higher score)
            unique_keywords = len(set(keywords))
            if unique_keywords >= 2:
                unique_bonus = (unique_keywords - 1) * 3  # +3 per unique keyword
                base_score += unique_bonus

            score = max(0, min(100, base_score))  # Clamp to 0-100

            scored_segments.append(
                KeywordSegment(
                    start_time=start_time,
                    end_time=end_time,
                    keyword_score=score,
                    detected_keywords=list(set(keywords)),  # Unique keywords
                    keyword_count=keyword_count,
                )
            )

        return scored_segments
