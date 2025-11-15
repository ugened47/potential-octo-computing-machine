"""Video analysis service for scene change detection."""

import logging
from dataclasses import dataclass
from pathlib import Path

import av
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class SceneSegment:
    """Represents an analyzed scene segment."""

    start_time: float
    end_time: float
    scene_score: int
    change_count: int
    avg_change_magnitude: float


class VideoAnalysisService:
    """
    Service for analyzing video features and detecting scene changes.

    Detects scene changes using frame-to-frame differences, analyzes
    scene transitions, and scores segments based on visual activity.
    """

    def __init__(
        self,
        scene_threshold: float = 30.0,
        min_scene_duration: float = 1.0,
        sample_fps: float = 2.0,
    ):
        """
        Initialize video analysis service.

        Args:
            scene_threshold: Threshold for scene change detection (default: 30.0)
            min_scene_duration: Minimum scene duration in seconds (default: 1.0)
            sample_fps: Frame sampling rate (default: 2.0 fps)
        """
        self.scene_threshold = scene_threshold
        self.min_scene_duration = min_scene_duration
        self.sample_fps = sample_fps

    def analyze_video(self, video_path: str | Path) -> list[SceneSegment]:
        """
        Analyze video for scene changes.

        Args:
            video_path: Path to video file

        Returns:
            List of SceneSegment objects with scores
        """
        video_path = Path(video_path)

        if not video_path.exists():
            logger.error(f"Video file not found: {video_path}")
            return []

        try:
            # Extract frames and detect scene changes
            scene_changes = self._detect_scene_changes(video_path)

            if not scene_changes:
                logger.warning(f"No scene changes detected in video: {video_path}")
                return []

            # Group into segments
            segments = self._create_segments(scene_changes)

            # Score segments based on scene change activity
            scored_segments = self._score_segments(segments)

            return scored_segments

        except Exception as e:
            logger.error(f"Error analyzing video {video_path}: {e}")
            return []

    def _detect_scene_changes(self, video_path: Path) -> list[tuple[float, float]]:
        """
        Detect scene changes using frame-to-frame differences.

        Args:
            video_path: Path to video file

        Returns:
            List of (timestamp, change_magnitude) tuples
        """
        try:
            container = av.open(str(video_path))
            video_stream = next(
                (s for s in container.streams if s.type == "video"), None
            )

            if video_stream is None:
                logger.warning(f"No video stream found in: {video_path}")
                return []

            # Get video properties
            fps = float(video_stream.average_rate)
            duration = float(video_stream.duration * video_stream.time_base)

            # Sample frames at specified rate
            frame_interval = int(fps / self.sample_fps)
            if frame_interval < 1:
                frame_interval = 1

            prev_frame = None
            prev_timestamp = None
            scene_changes = []
            frame_count = 0

            for frame in container.decode(video=0):
                frame_count += 1

                # Sample frames
                if frame_count % frame_interval != 0:
                    continue

                timestamp = float(frame.pts * video_stream.time_base)

                # Convert frame to PIL Image and resize for faster processing
                img = frame.to_image().resize((320, 240))
                current_frame = np.array(img)

                if prev_frame is not None:
                    # Calculate frame difference
                    diff_magnitude = self._calculate_frame_difference(
                        prev_frame, current_frame
                    )

                    # Detect significant change
                    if diff_magnitude >= self.scene_threshold:
                        scene_changes.append((timestamp, diff_magnitude))

                prev_frame = current_frame
                prev_timestamp = timestamp

            container.close()

            return scene_changes

        except Exception as e:
            logger.error(f"Error detecting scene changes: {e}")
            return []

    def _calculate_frame_difference(
        self, frame1: np.ndarray, frame2: np.ndarray
    ) -> float:
        """
        Calculate difference between two frames using histogram comparison.

        Args:
            frame1: First frame as numpy array
            frame2: Second frame as numpy array

        Returns:
            Difference magnitude (0-100)
        """
        try:
            # Convert to grayscale for simpler comparison
            if len(frame1.shape) == 3:
                gray1 = np.mean(frame1, axis=2)
                gray2 = np.mean(frame2, axis=2)
            else:
                gray1 = frame1
                gray2 = frame2

            # Calculate histogram difference
            hist1, _ = np.histogram(gray1.flatten(), bins=256, range=(0, 256))
            hist2, _ = np.histogram(gray2.flatten(), bins=256, range=(0, 256))

            # Normalize histograms
            hist1 = hist1 / hist1.sum()
            hist2 = hist2 / hist2.sum()

            # Calculate chi-square distance
            chi_square = np.sum((hist1 - hist2) ** 2 / (hist1 + hist2 + 1e-10))

            # Normalize to 0-100 scale (chi-square typically < 2 for similar frames)
            diff_magnitude = min(chi_square / 2.0 * 100, 100)

            return diff_magnitude

        except Exception as e:
            logger.error(f"Error calculating frame difference: {e}")
            return 0.0

    def _create_segments(
        self, scene_changes: list[tuple[float, float]]
    ) -> list[tuple[float, float, list[float]]]:
        """
        Group scene changes into segments.

        Args:
            scene_changes: List of (timestamp, change_magnitude) tuples

        Returns:
            List of (start_time, end_time, [change_magnitudes]) tuples
        """
        if not scene_changes:
            return []

        segments = []
        segment_start = 0.0
        segment_changes = []

        for i, (timestamp, magnitude) in enumerate(scene_changes):
            # Check if this is the start of a new segment
            if segment_changes and timestamp - segment_start > self.min_scene_duration:
                # End current segment
                segment_end = timestamp
                segments.append((segment_start, segment_end, segment_changes.copy()))

                # Start new segment
                segment_start = timestamp
                segment_changes = []

            segment_changes.append(magnitude)

        # Add final segment
        if segment_changes:
            final_end = scene_changes[-1][0] + self.min_scene_duration
            segments.append((segment_start, final_end, segment_changes))

        return segments

    def _score_segments(
        self, segments: list[tuple[float, float, list[float]]]
    ) -> list[SceneSegment]:
        """
        Score segments based on scene change activity.

        Args:
            segments: List of (start_time, end_time, [change_magnitudes]) tuples

        Returns:
            List of SceneSegment objects with scores
        """
        scored_segments = []

        for start_time, end_time, change_magnitudes in segments:
            if not change_magnitudes:
                continue

            # Calculate metrics
            change_count = len(change_magnitudes)
            avg_magnitude = np.mean(change_magnitudes)
            segment_duration = end_time - start_time

            # Calculate change frequency (changes per second)
            change_frequency = change_count / max(segment_duration, 1.0)

            # Score based on frequency and magnitude
            # Frequency score (0-50): More changes = higher score
            frequency_score = min(change_frequency / 2.0 * 50, 50)

            # Magnitude score (0-50): Larger changes = higher score
            magnitude_score = min(avg_magnitude / 50.0 * 50, 50)

            # Combined score
            score = int(frequency_score + magnitude_score)
            score = max(0, min(100, score))  # Clamp to 0-100

            scored_segments.append(
                SceneSegment(
                    start_time=start_time,
                    end_time=end_time,
                    scene_score=score,
                    change_count=change_count,
                    avg_change_magnitude=avg_magnitude,
                )
            )

        return scored_segments
