"""Social Media Template model factory for testing."""

import factory
from datetime import datetime
from faker import Faker

fake = Faker()


class SocialMediaTemplateFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating SocialMediaTemplate instances in tests."""

    class Meta:
        # model = SocialMediaTemplate  # Will be uncommented when model is created
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(lambda: fake.uuid4())

    # Template metadata
    name = factory.LazyFunction(lambda: fake.catch_phrase())
    description = factory.LazyFunction(lambda: fake.paragraph(nb_sentences=2))
    platform = factory.LazyFunction(
        lambda: fake.random_element([
            "youtube_shorts", "tiktok", "instagram_reels", "instagram_story",
            "twitter", "linkedin", "facebook", "custom"
        ])
    )
    is_preset = False

    # Video settings
    aspect_ratio = factory.LazyFunction(
        lambda: fake.random_element(["9:16", "16:9", "1:1", "4:5"])
    )
    resolution_width = factory.LazyAttribute(
        lambda obj: {
            "9:16": 1080,
            "16:9": 1920,
            "1:1": 1080,
            "4:5": 1080,
        }.get(obj.aspect_ratio, 1080)
    )
    resolution_height = factory.LazyAttribute(
        lambda obj: {
            "9:16": 1920,
            "16:9": 1080,
            "1:1": 1080,
            "4:5": 1350,
        }.get(obj.aspect_ratio, 1920)
    )

    # Duration constraints
    max_duration = factory.LazyFunction(
        lambda: fake.random_element([15, 30, 60, 90, 120, 180])
    )
    min_duration = factory.LazyFunction(lambda: fake.random_int(min=3, max=10))

    # Video transformation settings
    crop_strategy = factory.LazyFunction(
        lambda: fake.random_element(["center", "smart", "face_detection", "letterbox", "blur_background"])
    )
    scale_mode = factory.LazyFunction(
        lambda: fake.random_element(["fit", "fill", "stretch"])
    )

    # Audio settings
    audio_enabled = True
    audio_normalization = True
    background_music_enabled = False
    background_music_volume = factory.LazyFunction(lambda: fake.random.uniform(0.1, 0.3))

    # Caption/subtitle settings (JSON field)
    caption_settings = factory.LazyFunction(
        lambda: {
            "enabled": True,
            "style": fake.random_element([
                "minimal", "bold", "gaming", "podcast", "vlog", "professional", "trendy"
            ]),
            "font_size": fake.random_int(min=32, max=60),
            "position": "bottom",
            "animation": fake.random_element(["none", "fade", "pop", "slide"]),
            "word_highlight": True,
        }
    )

    # Platform-specific requirements (JSON field)
    platform_requirements = factory.LazyFunction(
        lambda: {
            "file_size_limit_mb": fake.random_int(min=100, max=500),
            "bitrate_kbps": fake.random_int(min=5000, max=15000),
            "framerate": fake.random_element([24, 30, 60]),
            "codec": "h264",
            "auto_captions": True,
        }
    )

    # Export settings
    export_format = "mp4"
    export_quality = factory.LazyFunction(
        lambda: fake.random_element(["high", "medium", "low"])
    )

    # Usage stats
    usage_count = factory.LazyFunction(lambda: fake.random_int(min=0, max=100))

    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)

    # Relationships
    user_id = factory.LazyFunction(lambda: fake.uuid4())

    class Params:
        """Parameterized traits for different template types."""

        preset = factory.Trait(
            is_preset=True,
            user_id=None,
        )

        youtube_shorts = factory.Trait(
            name="YouTube Shorts",
            platform="youtube_shorts",
            aspect_ratio="9:16",
            resolution_width=1080,
            resolution_height=1920,
            max_duration=60,
            min_duration=5,
            crop_strategy="center",
            caption_settings={
                "enabled": True,
                "style": "bold",
                "font_size": 48,
                "position": "center",
                "animation": "pop",
                "word_highlight": True,
            },
        )

        tiktok = factory.Trait(
            name="TikTok",
            platform="tiktok",
            aspect_ratio="9:16",
            resolution_width=1080,
            resolution_height=1920,
            max_duration=180,
            min_duration=3,
            crop_strategy="smart",
            caption_settings={
                "enabled": True,
                "style": "trendy",
                "font_size": 52,
                "position": "bottom",
                "animation": "pop",
                "word_highlight": True,
            },
        )

        instagram_reels = factory.Trait(
            name="Instagram Reels",
            platform="instagram_reels",
            aspect_ratio="9:16",
            resolution_width=1080,
            resolution_height=1920,
            max_duration=90,
            min_duration=3,
            crop_strategy="center",
            caption_settings={
                "enabled": True,
                "style": "minimal",
                "font_size": 44,
                "position": "bottom",
                "animation": "fade",
            },
        )

        instagram_story = factory.Trait(
            name="Instagram Story",
            platform="instagram_story",
            aspect_ratio="9:16",
            resolution_width=1080,
            resolution_height=1920,
            max_duration=15,
            min_duration=3,
            crop_strategy="face_detection",
        )

        twitter = factory.Trait(
            name="Twitter Video",
            platform="twitter",
            aspect_ratio="16:9",
            resolution_width=1280,
            resolution_height=720,
            max_duration=140,
            min_duration=5,
            crop_strategy="letterbox",
            caption_settings={
                "enabled": True,
                "style": "professional",
                "font_size": 36,
                "position": "bottom",
            },
        )

        linkedin = factory.Trait(
            name="LinkedIn Video",
            platform="linkedin",
            aspect_ratio="16:9",
            resolution_width=1920,
            resolution_height=1080,
            max_duration=600,
            min_duration=10,
            crop_strategy="letterbox",
            caption_settings={
                "enabled": True,
                "style": "professional",
                "font_size": 40,
                "position": "bottom",
                "animation": "none",
            },
        )

        square = factory.Trait(
            name="Square Post",
            aspect_ratio="1:1",
            resolution_width=1080,
            resolution_height=1080,
            crop_strategy="center",
        )

        vertical = factory.Trait(
            aspect_ratio="9:16",
            resolution_width=1080,
            resolution_height=1920,
        )

        horizontal = factory.Trait(
            aspect_ratio="16:9",
            resolution_width=1920,
            resolution_height=1080,
        )

        with_background_music = factory.Trait(
            background_music_enabled=True,
            background_music_volume=0.2,
        )

        no_captions = factory.Trait(
            caption_settings={
                "enabled": False,
            },
        )
