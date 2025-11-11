"""Segment merging service for highlight detection."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MergedSegment:
    """Merged and padded segment."""

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
    context_before_seconds: float
    context_after_seconds: float


class SegmentMerger:
    """
    Service for merging overlapping segments and adding context padding.

    Merges nearby highlights, adds context padding, and ensures segments
    don't exceed video boundaries.
    """

    def __init__(
        self,
        merge_threshold: float = 3.0,
        context_before: float = 2.0,
        context_after: float = 3.0,
    ):
        """
        Initialize segment merger.

        Args:
            merge_threshold: Max gap between segments to merge (default: 3.0)
            context_before: Seconds of context before highlight (default: 2.0)
            context_after: Seconds of context after highlight (default: 3.0)
        """
        self.merge_threshold = merge_threshold
        self.context_before = context_before
        self.context_after = context_after

    def merge_segments(
        self, segments: list, video_duration: float
    ) -> list[MergedSegment]:
        """
        Merge overlapping segments and add context padding.

        Args:
            segments: List of ScoredSegment objects
            video_duration: Total video duration in seconds

        Returns:
            List of MergedSegment objects
        """
        if not segments:
            return []

        try:
            # Sort segments by start time
            sorted_segments = sorted(segments, key=lambda s: s.start_time)

            # Merge overlapping and adjacent segments
            merged = self._merge_overlapping(sorted_segments)

            # Add context padding
            padded = self._add_context_padding(merged, video_duration)

            return padded

        except Exception as e:
            logger.error(f"Error merging segments: {e}")
            return []

    def _merge_overlapping(self, segments: list) -> list:
        """
        Merge overlapping or adjacent segments.

        Args:
            segments: Sorted list of ScoredSegment objects

        Returns:
            List of merged ScoredSegment objects
        """
        if not segments:
            return []

        merged = [segments[0]]

        for current in segments[1:]:
            last = merged[-1]

            # Check if segments should be merged
            gap = current.start_time - last.end_time

            if gap <= self.merge_threshold:
                # Merge segments
                merged_segment = self._merge_two_segments(last, current)
                merged[-1] = merged_segment
            else:
                # Keep segments separate
                merged.append(current)

        return merged

    def _merge_two_segments(self, seg1, seg2):
        """
        Merge two segments into one.

        Args:
            seg1: First ScoredSegment
            seg2: Second ScoredSegment

        Returns:
            Merged ScoredSegment
        """
        # Use dataclass from seg1 to create merged segment
        from .composite_scorer import ScoredSegment

        # Calculate weighted average scores based on duration
        duration1 = seg1.end_time - seg1.start_time
        duration2 = seg2.end_time - seg2.start_time
        total_duration = duration1 + duration2

        if total_duration == 0:
            weight1 = 0.5
            weight2 = 0.5
        else:
            weight1 = duration1 / total_duration
            weight2 = duration2 / total_duration

        # Merge scores (weighted average)
        overall_score = int(
            seg1.overall_score * weight1 + seg2.overall_score * weight2
        )
        audio_score = int(
            seg1.audio_energy_score * weight1 + seg2.audio_energy_score * weight2
        )
        scene_score = int(
            seg1.scene_change_score * weight1 + seg2.scene_change_score * weight2
        )
        speech_score = int(
            seg1.speech_density_score * weight1 + seg2.speech_density_score * weight2
        )
        keyword_score = int(
            seg1.keyword_score * weight1 + seg2.keyword_score * weight2
        )

        # Combine keywords
        combined_keywords = list(
            set(seg1.detected_keywords + seg2.detected_keywords)
        )

        # Use higher confidence
        confidence = max(seg1.confidence_level, seg2.confidence_level)

        # Span from start of first to end of second
        start_time = seg1.start_time
        end_time = seg2.end_time
        duration = end_time - start_time

        return ScoredSegment(
            start_time=start_time,
            end_time=end_time,
            overall_score=overall_score,
            audio_energy_score=audio_score,
            scene_change_score=scene_score,
            speech_density_score=speech_score,
            keyword_score=keyword_score,
            detected_keywords=combined_keywords,
            confidence_level=confidence,
            duration_seconds=duration,
        )

    def _add_context_padding(
        self, segments: list, video_duration: float
    ) -> list[MergedSegment]:
        """
        Add context padding to segments.

        Args:
            segments: List of ScoredSegment objects
            video_duration: Total video duration

        Returns:
            List of MergedSegment objects with padding
        """
        padded_segments = []

        for segment in segments:
            # Add context padding
            padded_start = max(0.0, segment.start_time - self.context_before)
            padded_end = min(video_duration, segment.end_time + self.context_after)

            # Calculate actual padding applied
            actual_context_before = segment.start_time - padded_start
            actual_context_after = padded_end - segment.end_time

            # Create merged segment with padding info
            merged_segment = MergedSegment(
                start_time=padded_start,
                end_time=padded_end,
                overall_score=segment.overall_score,
                audio_energy_score=segment.audio_energy_score,
                scene_change_score=segment.scene_change_score,
                speech_density_score=segment.speech_density_score,
                keyword_score=segment.keyword_score,
                detected_keywords=segment.detected_keywords,
                confidence_level=segment.confidence_level,
                duration_seconds=padded_end - padded_start,
                context_before_seconds=actual_context_before,
                context_after_seconds=actual_context_after,
            )

            padded_segments.append(merged_segment)

        # Remove any overlaps created by padding
        padded_segments = self._remove_padding_overlaps(padded_segments)

        return padded_segments

    def _remove_padding_overlaps(
        self, segments: list[MergedSegment]
    ) -> list[MergedSegment]:
        """
        Remove overlaps created by context padding.

        Args:
            segments: List of MergedSegment objects

        Returns:
            List of non-overlapping MergedSegment objects
        """
        if len(segments) <= 1:
            return segments

        adjusted = [segments[0]]

        for current in segments[1:]:
            last = adjusted[-1]

            # Check for overlap
            if current.start_time < last.end_time:
                # Adjust boundaries to midpoint
                midpoint = (last.end_time + current.start_time) / 2

                # Update last segment's end
                last.end_time = midpoint
                last.duration_seconds = last.end_time - last.start_time

                # Update current segment's start
                current.start_time = midpoint
                current.duration_seconds = current.end_time - current.start_time

            adjusted.append(current)

        return adjusted
