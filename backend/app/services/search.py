"""Search service for transcript keyword search."""

from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.transcript import Transcript, TranscriptStatus


class SearchService:
    """Service for searching transcripts."""

    def __init__(self, db: AsyncSession):
        """Initialize search service.

        Args:
            db: Database session
        """
        self.db = db

    async def search_transcript(
        self,
        video_id: UUID,
        keywords: list[str],
        padding_seconds: float = 5.0,
    ) -> list[dict[str, Any]]:
        """Search transcript for keywords and return matching segments.

        Args:
            video_id: Video ID
            keywords: List of keywords to search for
            padding_seconds: Padding around matches in seconds (default: 5.0)

        Returns:
            List of matching segments with start_time, end_time, transcript_excerpt, etc.
        """
        # Get transcript
        result = await self.db.execute(
            select(Transcript).where(
                Transcript.video_id == video_id,
                Transcript.status == TranscriptStatus.COMPLETED,
            )
        )
        transcript = result.scalar_one_or_none()

        if not transcript:
            return []

        # Use PostgreSQL full-text search
        # Build search query with AND logic (all keywords must match)
        search_terms = " & ".join(keywords)

        # Use PostgreSQL ts_rank for relevance scoring
        query = text(
            """
            SELECT 
                word->>'start'::float as start_time,
                word->>'end'::float as end_time,
                word->>'word' as word_text
            FROM transcripts,
            jsonb_array_elements(word_timestamps->'words') as word
            WHERE 
                video_id = :video_id
                AND status = 'completed'
                AND to_tsvector('english', word->>'word') @@ to_tsquery('english', :search_query)
            ORDER BY word->>'start'::float
            """
        )

        # For multiple keywords, we need to match all of them
        # We'll do a simpler approach: search for each keyword and find intersections
        matches = []

        if not transcript.word_timestamps.get("words"):
            return []

        words = transcript.word_timestamps["words"]

        # Find words that match any keyword (case-insensitive)
        matching_word_indices = []
        for i, word_data in enumerate(words):
            word_text = word_data.get("word", "").lower()
            for keyword in keywords:
                if keyword.lower() in word_text:
                    matching_word_indices.append(i)
                    break

        if not matching_word_indices:
            return []

        # Group consecutive matches into segments
        segments = []
        current_segment_start = None
        current_segment_end = None
        current_segment_words = []

        for idx in matching_word_indices:
            word_data = words[idx]
            start_time = float(word_data.get("start", 0))
            end_time = float(word_data.get("end", 0))

            if current_segment_start is None:
                # Start new segment
                current_segment_start = start_time
                current_segment_end = end_time
                current_segment_words = [word_data]
            else:
                # Check if this word is close to current segment (within 2 seconds)
                if start_time - current_segment_end <= 2.0:
                    # Extend current segment
                    current_segment_end = end_time
                    current_segment_words.append(word_data)
                else:
                    # Start new segment
                    segments.append(
                        {
                            "start_time": max(0, current_segment_start - padding_seconds),
                            "end_time": current_segment_end + padding_seconds,
                            "words": current_segment_words,
                        }
                    )
                    current_segment_start = start_time
                    current_segment_end = end_time
                    current_segment_words = [word_data]

        # Add final segment
        if current_segment_start is not None:
            segments.append(
                {
                    "start_time": max(0, current_segment_start - padding_seconds),
                    "end_time": current_segment_end + padding_seconds,
                    "words": current_segment_words,
                }
            )

        # Build results with transcript excerpts
        results = []
        for i, segment in enumerate(segments):
            # Get context around segment
            segment_start = segment["start_time"]
            segment_end = segment["end_time"]

            # Find words in this segment
            segment_words = []
            context_before = []
            context_after = []

            for word_data in words:
                word_start = float(word_data.get("start", 0))
                word_end = float(word_data.get("end", 0))

                if word_start >= segment_start and word_end <= segment_end:
                    segment_words.append(word_data)
                elif word_start < segment_start and word_start >= segment_start - 2:
                    context_before.append(word_data)
                elif word_end > segment_end and word_end <= segment_end + 2:
                    context_after.append(word_data)

            # Build excerpt
            excerpt_words = context_before[-3:] + segment_words + context_after[:3]
            excerpt = " ".join(
                word.get("word", "") for word in excerpt_words if word.get("word")
            )

            # Count matched keywords
            matched_keywords = []
            for word_data in segment_words:
                word_text = word_data.get("word", "").lower()
                for keyword in keywords:
                    if keyword.lower() in word_text and keyword not in matched_keywords:
                        matched_keywords.append(keyword)

            # Calculate relevance score (simple: number of matched keywords)
            relevance_score = len(matched_keywords) / len(keywords) if keywords else 0

            results.append(
                {
                    "id": f"{video_id}_{i}",
                    "start_time": segment["start_time"],
                    "end_time": segment["end_time"],
                    "transcript_excerpt": excerpt,
                    "relevance_score": relevance_score,
                    "matched_keywords": matched_keywords,
                }
            )

        return results

