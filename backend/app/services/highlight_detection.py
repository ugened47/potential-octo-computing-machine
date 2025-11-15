"""Highlight detection service for orchestrating video analysis."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.highlight import Highlight, HighlightStatus, HighlightType
from app.models.transcript import Transcript
from app.models.video import Video
from app.services.analysis import (
    AudioAnalysisService,
    CompositeScorer,
    KeywordAnalysisService,
    ScoreWeights,
    SegmentMerger,
    SpeechAnalysisService,
    VideoAnalysisService,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class HighlightDetectionService:
    """
    Service for orchestrating full highlight detection workflow.

    Coordinates audio, video, speech, and keyword analysis, calculates
    composite scores, and stores highlight records in the database.
    """

    def __init__(self):
        """Initialize highlight detection service."""
        self.audio_analyzer = AudioAnalysisService()
        self.video_analyzer = VideoAnalysisService()
        self.speech_analyzer = SpeechAnalysisService()
        self.keyword_analyzer = KeywordAnalysisService()
        self.segment_merger = SegmentMerger()

    async def detect_highlights(
        self,
        db: AsyncSession,
        video_id: str,
        video_path: str | Path,
        sensitivity: str = "medium",
        custom_keywords: list[str] | None = None,
        score_weights: dict | None = None,
    ) -> list[Highlight]:
        """
        Detect highlights in a video.

        Args:
            db: Database session
            video_id: Video ID
            video_path: Path to video file
            sensitivity: Detection sensitivity ('low', 'medium', 'high', 'max')
            custom_keywords: Optional custom keywords
            score_weights: Optional custom score weights

        Returns:
            List of detected Highlight objects
        """
        video_path = Path(video_path)

        try:
            # Get video from database
            result = await db.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()

            if not video:
                logger.error(f"Video not found: {video_id}")
                return []

            video_duration = video.duration or 0.0

            # Get transcript if available
            transcript_result = await db.execute(
                select(Transcript).where(Transcript.video_id == video_id)
            )
            transcript = transcript_result.scalar_one_or_none()

            word_timestamps = []
            if transcript and transcript.word_timestamps:
                # Extract word timestamps from transcript
                word_timestamps = self._extract_word_timestamps(
                    transcript.word_timestamps
                )

            # Run analysis components
            logger.info(f"Starting highlight detection for video {video_id}")

            # Audio analysis
            logger.info("Analyzing audio...")
            audio_segments = self.audio_analyzer.analyze_video(video_path)

            # Video analysis
            logger.info("Analyzing video...")
            video_segments = self.video_analyzer.analyze_video(video_path)

            # Speech analysis
            logger.info("Analyzing speech patterns...")
            speech_segments = []
            if word_timestamps:
                speech_segments = self.speech_analyzer.analyze_transcript(
                    word_timestamps
                )

            # Keyword analysis
            logger.info("Analyzing keywords...")
            keyword_segments = []
            if word_timestamps:
                keyword_segments = self.keyword_analyzer.analyze_transcript(
                    word_timestamps, custom_keywords
                )

            # Create composite scorer with custom weights if provided
            weights = ScoreWeights()
            if score_weights:
                weights = ScoreWeights(
                    audio_energy=score_weights.get("audio_energy", 0.35),
                    scene_change=score_weights.get("scene_change", 0.20),
                    speech_density=score_weights.get("speech_density", 0.25),
                    keyword=score_weights.get("keyword", 0.20),
                )

            scorer = CompositeScorer(weights)

            # Calculate composite scores
            logger.info("Calculating composite scores...")
            scored_segments = scorer.score_segments(
                audio_segments,
                video_segments,
                speech_segments,
                keyword_segments,
                video_duration,
            )

            # Merge and add padding
            logger.info("Merging segments...")
            merged_segments = self.segment_merger.merge_segments(
                scored_segments, video_duration
            )

            # Filter and rank based on sensitivity
            logger.info("Filtering and ranking highlights...")
            highlights = self._filter_and_rank_highlights(
                merged_segments, sensitivity, video_id
            )

            # Store highlights in database
            logger.info(f"Storing {len(highlights)} highlights in database...")
            await self._store_highlights(db, highlights)

            logger.info(
                f"Highlight detection complete for video {video_id}: {len(highlights)} highlights detected"
            )

            return highlights

        except Exception as e:
            logger.error(f"Error detecting highlights for video {video_id}: {e}")
            return []

    def _extract_word_timestamps(
        self, word_timestamps_data: dict
    ) -> list[dict[str, any]]:
        """
        Extract word timestamps from transcript data.

        Args:
            word_timestamps_data: Transcript word_timestamps dict

        Returns:
            List of word timestamp dicts
        """
        # Handle different possible formats
        if isinstance(word_timestamps_data, list):
            return word_timestamps_data

        if isinstance(word_timestamps_data, dict):
            words = word_timestamps_data.get("words", [])
            if isinstance(words, list):
                return words

        return []

    def _filter_and_rank_highlights(
        self, segments: list, sensitivity: str, video_id: str
    ) -> list[Highlight]:
        """
        Filter and rank highlights based on sensitivity.

        Args:
            segments: List of MergedSegment objects
            sensitivity: Detection sensitivity
            video_id: Video ID

        Returns:
            List of ranked Highlight objects
        """
        # Define sensitivity parameters
        sensitivity_config = {
            "low": {"top_n": 5, "threshold": 80},
            "medium": {"top_n": 10, "threshold": 70},
            "high": {"top_n": 15, "threshold": 60},
            "max": {"top_n": 20, "threshold": 50},
        }

        config = sensitivity_config.get(sensitivity, sensitivity_config["medium"])
        top_n = config["top_n"]
        threshold = config["threshold"]

        # Filter by threshold
        filtered = [s for s in segments if s.overall_score >= threshold]

        # Sort by overall score (descending)
        sorted_segments = sorted(
            filtered, key=lambda s: s.overall_score, reverse=True
        )

        # Take top N
        top_segments = sorted_segments[:top_n]

        # Convert to Highlight objects with ranks
        highlights = []
        for rank, segment in enumerate(top_segments, start=1):
            # Determine highlight type based on component scores
            highlight_type = self._determine_highlight_type(segment)

            highlight = Highlight(
                video_id=video_id,
                start_time=segment.start_time,
                end_time=segment.end_time,
                overall_score=segment.overall_score,
                audio_energy_score=segment.audio_energy_score,
                scene_change_score=segment.scene_change_score,
                speech_density_score=segment.speech_density_score,
                keyword_score=segment.keyword_score,
                detected_keywords=segment.detected_keywords,
                confidence_level=segment.confidence_level,
                duration_seconds=segment.duration_seconds,
                rank=rank,
                highlight_type=highlight_type,
                status=HighlightStatus.DETECTED,
                context_before_seconds=segment.context_before_seconds,
                context_after_seconds=segment.context_after_seconds,
            )

            highlights.append(highlight)

        return highlights

    def _determine_highlight_type(self, segment) -> HighlightType:
        """
        Determine highlight type based on component scores.

        Args:
            segment: MergedSegment object

        Returns:
            HighlightType enum value
        """
        # Find the dominant component
        scores = {
            "audio": segment.audio_energy_score,
            "scene": segment.scene_change_score,
            "speech": segment.speech_density_score,
            "keyword": segment.keyword_score,
        }

        max_component = max(scores, key=scores.get)

        # Map to highlight type
        type_mapping = {
            "audio": HighlightType.HIGH_ENERGY,
            "scene": HighlightType.SCENE_CHANGE,
            "keyword": HighlightType.KEYWORD_MATCH,
            "speech": HighlightType.KEY_MOMENT,
        }

        return type_mapping.get(max_component, HighlightType.KEY_MOMENT)

    async def _store_highlights(
        self, db: AsyncSession, highlights: list[Highlight]
    ) -> None:
        """
        Store highlights in database.

        Args:
            db: Database session
            highlights: List of Highlight objects
        """
        try:
            for highlight in highlights:
                db.add(highlight)

            await db.commit()

        except Exception as e:
            logger.error(f"Error storing highlights: {e}")
            await db.rollback()
            raise

    async def get_cached_highlights(
        self, db: AsyncSession, video_id: str
    ) -> list[Highlight] | None:
        """
        Get cached highlights for a video.

        Args:
            db: Database session
            video_id: Video ID

        Returns:
            List of Highlight objects or None if not cached
        """
        try:
            result = await db.execute(
                select(Highlight).where(Highlight.video_id == video_id)
            )
            highlights = result.scalars().all()

            if highlights:
                logger.info(
                    f"Found {len(highlights)} cached highlights for video {video_id}"
                )
                return list(highlights)

            return None

        except Exception as e:
            logger.error(f"Error getting cached highlights: {e}")
            return None

    async def clear_highlights(self, db: AsyncSession, video_id: str) -> None:
        """
        Clear all highlights for a video.

        Args:
            db: Database session
            video_id: Video ID
        """
        try:
            result = await db.execute(
                select(Highlight).where(Highlight.video_id == video_id)
            )
            highlights = result.scalars().all()

            for highlight in highlights:
                await db.delete(highlight)

            await db.commit()

            logger.info(f"Cleared {len(highlights)} highlights for video {video_id}")

        except Exception as e:
            logger.error(f"Error clearing highlights: {e}")
            await db.rollback()
            raise
