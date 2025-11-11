"""Subtitle translation service using Google Cloud Translation API."""

import os
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subtitle import (
    SubtitleTranslation,
    TranslationQuality,
    TranslationStatus,
)
from app.models.transcript import Transcript


# Language data with ISO 639-1 codes
SUPPORTED_LANGUAGES = [
    {"code": "en", "name": "English", "native_name": "English", "rtl": False},
    {"code": "es", "name": "Spanish", "native_name": "Español", "rtl": False},
    {"code": "fr", "name": "French", "native_name": "Français", "rtl": False},
    {"code": "de", "name": "German", "native_name": "Deutsch", "rtl": False},
    {"code": "pt", "name": "Portuguese", "native_name": "Português", "rtl": False},
    {"code": "ru", "name": "Russian", "native_name": "Русский", "rtl": False},
    {"code": "zh", "name": "Chinese", "native_name": "中文", "rtl": False},
    {"code": "ja", "name": "Japanese", "native_name": "日本語", "rtl": False},
    {"code": "ko", "name": "Korean", "native_name": "한국어", "rtl": False},
    {"code": "ar", "name": "Arabic", "native_name": "العربية", "rtl": True},
    {"code": "it", "name": "Italian", "native_name": "Italiano", "rtl": False},
    {"code": "nl", "name": "Dutch", "native_name": "Nederlands", "rtl": False},
    {"code": "pl", "name": "Polish", "native_name": "Polski", "rtl": False},
    {"code": "tr", "name": "Turkish", "native_name": "Türkçe", "rtl": False},
    {"code": "hi", "name": "Hindi", "native_name": "हिन्दी", "rtl": False},
    {"code": "vi", "name": "Vietnamese", "native_name": "Tiếng Việt", "rtl": False},
    {"code": "th", "name": "Thai", "native_name": "ไทย", "rtl": False},
    {"code": "id", "name": "Indonesian", "native_name": "Bahasa Indonesia", "rtl": False},
]


class SubtitleTranslationService:
    """Service for subtitle translation operations."""

    def __init__(self, db: AsyncSession):
        """Initialize subtitle translation service."""
        self.db = db
        self.google_api_key = os.getenv("GOOGLE_TRANSLATE_API_KEY")

    async def translate_subtitles(
        self, video_id: UUID, source_lang: str, target_lang: str
    ) -> SubtitleTranslation:
        """Translate all subtitle segments to target language."""
        # Get transcript
        result = await self.db.execute(
            select(Transcript).where(Transcript.video_id == video_id)
        )
        transcript = result.scalar_one_or_none()
        if not transcript:
            raise ValueError(f"Transcript for video {video_id} not found")

        # Check if translation already exists
        result = await self.db.execute(
            select(SubtitleTranslation).where(
                SubtitleTranslation.video_id == video_id,
                SubtitleTranslation.target_language == target_lang,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        # Create translation record
        translation = SubtitleTranslation(
            video_id=video_id,
            source_language=source_lang,
            target_language=target_lang,
            status=TranslationStatus.PROCESSING,
        )
        self.db.add(translation)
        await self.db.commit()
        await self.db.refresh(translation)

        try:
            # Get transcript segments
            segments_to_translate = self._extract_segments_from_transcript(transcript)

            # Batch translate
            translated_segments = await self.translate_batch(
                [seg["original_text"] for seg in segments_to_translate],
                source_lang,
                target_lang,
            )

            # Combine with timing info
            final_segments = []
            total_chars = 0
            total_words = 0

            for i, orig_seg in enumerate(segments_to_translate):
                translated_text = translated_segments[i]["translated_text"]
                confidence = translated_segments[i].get("confidence", 0.9)

                final_segments.append({
                    "start_time": orig_seg["start_time"],
                    "end_time": orig_seg["end_time"],
                    "original_text": orig_seg["original_text"],
                    "translated_text": translated_text,
                    "confidence": confidence,
                })

                total_chars += len(translated_text)
                total_words += len(translated_text.split())

            # Update translation record
            translation.segments = {"segments": final_segments}
            translation.character_count = total_chars
            translation.word_count = total_words
            translation.status = TranslationStatus.COMPLETED

        except Exception as e:
            translation.status = TranslationStatus.FAILED
            translation.error_message = str(e)

        await self.db.commit()
        await self.db.refresh(translation)
        return translation

    async def translate_batch(
        self, texts: list[str], source_lang: str, target_lang: str
    ) -> list[dict[str, Any]]:
        """Translate multiple text segments in batch."""
        if not self.google_api_key:
            # Fallback: mock translation for development
            return self._mock_translate_batch(texts, target_lang)

        # TODO: Implement actual Google Translate API integration
        # For now, using mock translation
        return self._mock_translate_batch(texts, target_lang)

    def _mock_translate_batch(
        self, texts: list[str], target_lang: str
    ) -> list[dict[str, Any]]:
        """Mock translation for development (returns text with language prefix)."""
        results = []
        for text in texts:
            results.append({
                "translated_text": f"[{target_lang.upper()}] {text}",
                "confidence": 0.95,
            })
        return results

    async def detect_language(self, text: str) -> str:
        """Auto-detect source language."""
        if not self.google_api_key:
            # Default to English for development
            return "en"

        # TODO: Implement actual language detection
        # For now, return English as default
        return "en"

    def get_supported_languages(self) -> list[dict[str, Any]]:
        """Return list of supported languages."""
        return SUPPORTED_LANGUAGES

    def estimate_translation_cost(self, character_count: int) -> float:
        """Calculate estimated cost based on Google Translate pricing."""
        # Google Translate pricing: ~$20 per 1M characters
        cost_per_million = 20.0
        cost = (character_count / 1_000_000) * cost_per_million
        return round(cost, 4)

    def validate_translation_quality(
        self, original: str, translated: str, target_lang: str
    ) -> float:
        """Basic quality check for translation."""
        # Simple heuristics
        if not translated or len(translated) == 0:
            return 0.0

        # Length ratio check (translated text should be somewhat similar in length)
        length_ratio = len(translated) / max(len(original), 1)
        if length_ratio < 0.3 or length_ratio > 3.0:
            # Translation is suspiciously short or long
            return 0.5

        # Check if special characters are preserved
        # (This is a simple check - production would be more sophisticated)
        return 0.85  # Default reasonable quality score

    async def create_manual_translation(
        self, video_id: UUID, target_lang: str, segments: list[dict[str, Any]]
    ) -> SubtitleTranslation:
        """Create manual/professional translation."""
        # Validate segment structure
        for seg in segments:
            required_fields = ["start_time", "end_time", "translated_text"]
            if not all(field in seg for field in required_fields):
                raise ValueError(f"Invalid segment structure: {seg}")

        # Calculate statistics
        total_chars = sum(len(seg["translated_text"]) for seg in segments)
        total_words = sum(len(seg["translated_text"].split()) for seg in segments)

        # Create translation record
        translation = SubtitleTranslation(
            video_id=video_id,
            source_language="unknown",  # User didn't specify
            target_language=target_lang,
            translation_service="manual",
            translation_quality=TranslationQuality.PROFESSIONAL,
            segments={"segments": segments},
            character_count=total_chars,
            word_count=total_words,
            status=TranslationStatus.COMPLETED,
        )
        self.db.add(translation)
        await self.db.commit()
        await self.db.refresh(translation)
        return translation

    def _extract_segments_from_transcript(
        self, transcript: Transcript
    ) -> list[dict[str, Any]]:
        """Extract segments from transcript for translation."""
        # Use word timestamps to create segments
        word_data = transcript.word_timestamps.get("words", [])

        if not word_data:
            # Fallback: split full text into sentences
            sentences = transcript.full_text.split(". ")
            return [
                {
                    "start_time": i * 5.0,
                    "end_time": (i + 1) * 5.0,
                    "original_text": sentence.strip(),
                }
                for i, sentence in enumerate(sentences)
                if sentence.strip()
            ]

        # Group words into segments (7 words per segment by default)
        segments = []
        words_per_segment = 7
        current_words = []
        current_start = None

        for word_info in word_data:
            word = word_info.get("word", "")
            start = word_info.get("start", 0.0)
            end = word_info.get("end", 0.0)

            if current_start is None:
                current_start = start

            current_words.append(word)

            if len(current_words) >= words_per_segment:
                segments.append({
                    "start_time": current_start,
                    "end_time": end,
                    "original_text": " ".join(current_words),
                })
                current_words = []
                current_start = None

        # Add remaining words
        if current_words and current_start is not None:
            last_end = word_data[-1].get("end", current_start + 1.0)
            segments.append({
                "start_time": current_start,
                "end_time": last_end,
                "original_text": " ".join(current_words),
            })

        return segments
