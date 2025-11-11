"""Seed data for social media templates."""

from uuid import uuid4

from app.models import PlatformType, SocialMediaTemplate, StylePreset


def get_caption_style(preset: StylePreset) -> dict:
    """Get caption style configuration for a preset."""
    styles = {
        StylePreset.MINIMAL: {
            "font_family": "Arial, sans-serif",
            "font_size": 4,  # % of video height
            "font_weight": "normal",
            "text_color": "#FFFFFF",
            "background_color": "rgba(0, 0, 0, 0)",
            "stroke_color": "#000000",
            "stroke_width": 2,
            "position": "bottom",
            "y_offset": 15,  # % from position
            "alignment": "center",
            "animation": "fade",
            "max_chars_per_line": 35,
            "max_lines": 2,
        },
        StylePreset.BOLD: {
            "font_family": "Arial Black, sans-serif",
            "font_size": 6,
            "font_weight": "extra-bold",
            "text_color": "#FFFFFF",
            "background_color": "rgba(255, 215, 0, 0.9)",
            "stroke_color": "#000000",
            "stroke_width": 3,
            "position": "bottom",
            "y_offset": 15,
            "alignment": "center",
            "animation": "pop",
            "max_chars_per_line": 30,
            "max_lines": 2,
        },
        StylePreset.GAMING: {
            "font_family": "Impact, sans-serif",
            "font_size": 7,
            "font_weight": "bold",
            "text_color": "#00FFFF",
            "background_color": "rgba(255, 0, 255, 0.3)",
            "stroke_color": "#FF00FF",
            "stroke_width": 4,
            "position": "center",
            "y_offset": 0,
            "alignment": "center",
            "animation": "word-by-word",
            "max_chars_per_line": 25,
            "max_lines": 2,
        },
        StylePreset.PODCAST: {
            "font_family": "Georgia, serif",
            "font_size": 5,
            "font_weight": "normal",
            "text_color": "#FFFFFF",
            "background_color": "rgba(0, 0, 0, 0.7)",
            "stroke_color": "#000000",
            "stroke_width": 0,
            "position": "center",
            "y_offset": 0,
            "alignment": "center",
            "animation": "fade",
            "max_chars_per_line": 40,
            "max_lines": 3,
        },
        StylePreset.VLOG: {
            "font_family": "Comfortaa, sans-serif",
            "font_size": 5,
            "font_weight": "normal",
            "text_color": "#FFD700",
            "background_color": "rgba(0, 0, 0, 0.5)",
            "stroke_color": "#FFFFFF",
            "stroke_width": 2,
            "position": "bottom",
            "y_offset": 15,
            "alignment": "center",
            "animation": "slide",
            "max_chars_per_line": 35,
            "max_lines": 2,
        },
        StylePreset.PROFESSIONAL: {
            "font_family": "Helvetica, sans-serif",
            "font_size": 4,
            "font_weight": "normal",
            "text_color": "#000000",
            "background_color": "rgba(255, 255, 255, 0.9)",
            "stroke_color": "#000000",
            "stroke_width": 0,
            "position": "bottom",
            "y_offset": 10,
            "alignment": "center",
            "animation": "fade",
            "max_chars_per_line": 40,
            "max_lines": 2,
        },
        StylePreset.TRENDY: {
            "font_family": "Montserrat, sans-serif",
            "font_size": 6,
            "font_weight": "bold",
            "text_color": "#FFFFFF",
            "background_color": "rgba(0, 0, 0, 0.6)",
            "stroke_color": "#FFD700",
            "stroke_width": 3,
            "position": "bottom",
            "y_offset": 15,
            "alignment": "center",
            "animation": "word-by-word",
            "max_chars_per_line": 30,
            "max_lines": 2,
        },
    }
    return styles.get(preset, styles[StylePreset.MINIMAL])


SYSTEM_PRESETS = [
    {
        "id": uuid4(),
        "name": "YouTube Shorts",
        "description": "Optimized for YouTube Shorts - 60s max, 9:16 vertical format with bold captions",
        "platform": PlatformType.YOUTUBE_SHORTS,
        "aspect_ratio": "9:16",
        "max_duration_seconds": 60,
        "auto_captions": True,
        "caption_style": get_caption_style(StylePreset.BOLD),
        "style_preset": StylePreset.BOLD,
        "video_codec": "h264",
        "audio_codec": "aac",
        "bitrate": "8M",
        "is_system_preset": True,
        "user_id": None,
        "is_active": True,
        "usage_count": 0,
    },
    {
        "id": uuid4(),
        "name": "TikTok",
        "description": "Optimized for TikTok - 60s max, 9:16 vertical format with trendy animated captions",
        "platform": PlatformType.TIKTOK,
        "aspect_ratio": "9:16",
        "max_duration_seconds": 60,
        "auto_captions": True,
        "caption_style": get_caption_style(StylePreset.TRENDY),
        "style_preset": StylePreset.TRENDY,
        "video_codec": "h264",
        "audio_codec": "aac",
        "bitrate": "8M",
        "is_system_preset": True,
        "user_id": None,
        "is_active": True,
        "usage_count": 0,
    },
    {
        "id": uuid4(),
        "name": "Instagram Reels",
        "description": "Optimized for Instagram Reels - 90s max, 9:16 vertical format with clean captions",
        "platform": PlatformType.INSTAGRAM_REELS,
        "aspect_ratio": "9:16",
        "max_duration_seconds": 90,
        "auto_captions": True,
        "caption_style": get_caption_style(StylePreset.VLOG),
        "style_preset": StylePreset.VLOG,
        "video_codec": "h264",
        "audio_codec": "aac",
        "bitrate": "8M",
        "is_system_preset": True,
        "user_id": None,
        "is_active": True,
        "usage_count": 0,
    },
    {
        "id": uuid4(),
        "name": "Twitter/X Video",
        "description": "Optimized for Twitter/X - 140s max, flexible aspect ratio with minimal captions",
        "platform": PlatformType.TWITTER,
        "aspect_ratio": "16:9",
        "max_duration_seconds": 140,
        "auto_captions": True,
        "caption_style": get_caption_style(StylePreset.MINIMAL),
        "style_preset": StylePreset.MINIMAL,
        "video_codec": "h264",
        "audio_codec": "aac",
        "bitrate": "5M",
        "is_system_preset": True,
        "user_id": None,
        "is_active": True,
        "usage_count": 0,
    },
    {
        "id": uuid4(),
        "name": "Twitter/X Square",
        "description": "Optimized for Twitter/X - 140s max, 1:1 square format with minimal captions",
        "platform": PlatformType.TWITTER,
        "aspect_ratio": "1:1",
        "max_duration_seconds": 140,
        "auto_captions": True,
        "caption_style": get_caption_style(StylePreset.MINIMAL),
        "style_preset": StylePreset.MINIMAL,
        "video_codec": "h264",
        "audio_codec": "aac",
        "bitrate": "5M",
        "is_system_preset": True,
        "user_id": None,
        "is_active": True,
        "usage_count": 0,
    },
    {
        "id": uuid4(),
        "name": "LinkedIn Video",
        "description": "Optimized for LinkedIn - 600s max, 1:1 square format with professional captions",
        "platform": PlatformType.LINKEDIN,
        "aspect_ratio": "1:1",
        "max_duration_seconds": 600,
        "auto_captions": True,
        "caption_style": get_caption_style(StylePreset.PROFESSIONAL),
        "style_preset": StylePreset.PROFESSIONAL,
        "video_codec": "h264",
        "audio_codec": "aac",
        "bitrate": "5M",
        "is_system_preset": True,
        "user_id": None,
        "is_active": True,
        "usage_count": 0,
    },
]


async def seed_social_media_templates(db) -> None:
    """Seed system preset templates."""
    from sqlmodel import select

    # Check if system presets already exist
    result = await db.execute(
        select(SocialMediaTemplate).where(SocialMediaTemplate.is_system_preset == True)
    )
    existing = result.scalars().all()

    if existing:
        print(f"System presets already exist ({len(existing)} templates). Skipping seed.")
        return

    # Create system presets
    for preset_data in SYSTEM_PRESETS:
        template = SocialMediaTemplate(**preset_data)
        db.add(template)

    await db.commit()
    print(f"Seeded {len(SYSTEM_PRESETS)} system preset templates.")
