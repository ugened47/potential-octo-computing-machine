"""Advanced Editor project model factories for testing."""

import factory
from datetime import datetime
from faker import Faker

fake = Faker()


class ProjectFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Project instances in tests."""

    class Meta:
        # model = Project  # Will be uncommented when model is created
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(lambda: fake.uuid4())

    # Project metadata
    name = factory.LazyFunction(lambda: fake.catch_phrase())
    description = factory.LazyFunction(lambda: fake.paragraph(nb_sentences=2))

    # Project settings (JSON field)
    settings = factory.LazyFunction(
        lambda: {
            "resolution": {"width": 1920, "height": 1080},
            "framerate": 30,
            "sample_rate": 48000,
            "duration": fake.random_int(min=60, max=3600),
            "background_color": "#000000",
        }
    )

    # Export settings
    export_format = "mp4"
    export_quality = "high"

    # Status
    status = factory.LazyFunction(
        lambda: fake.random_element(["draft", "in_progress", "rendering", "completed"])
    )

    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    last_edited_at = factory.LazyFunction(datetime.utcnow)

    # Relationships
    user_id = factory.LazyFunction(lambda: fake.uuid4())

    class Params:
        draft = factory.Trait(status="draft")
        in_progress = factory.Trait(status="in_progress")
        rendering = factory.Trait(status="rendering")
        completed = factory.Trait(status="completed")

        hd = factory.Trait(
            settings={
                "resolution": {"width": 1920, "height": 1080},
                "framerate": 30,
                "sample_rate": 48000,
            }
        )

        uhd = factory.Trait(
            settings={
                "resolution": {"width": 3840, "height": 2160},
                "framerate": 60,
                "sample_rate": 48000,
            }
        )

        vertical = factory.Trait(
            settings={
                "resolution": {"width": 1080, "height": 1920},
                "framerate": 30,
                "sample_rate": 48000,
            }
        )


class TrackFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Track instances in tests."""

    class Meta:
        # model = Track  # Will be uncommented when model is created
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(lambda: fake.uuid4())

    # Track metadata
    name = factory.LazyFunction(lambda: fake.word().capitalize())
    track_type = factory.LazyFunction(
        lambda: fake.random_element(["video", "audio", "image", "text"])
    )
    order = factory.LazyFunction(lambda: fake.random_int(min=0, max=10))

    # Track settings (JSON field)
    settings = factory.LazyFunction(
        lambda: {
            "locked": False,
            "visible": True,
            "muted": False,
            "solo": False,
            "opacity": 1.0,
            "volume": 1.0,
        }
    )

    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)

    # Relationships
    project_id = factory.LazyFunction(lambda: fake.uuid4())

    class Params:
        video_track = factory.Trait(track_type="video", name="Video Track")
        audio_track = factory.Trait(track_type="audio", name="Audio Track")
        image_track = factory.Trait(track_type="image", name="Image Track")
        text_track = factory.Trait(track_type="text", name="Text Track")

        locked = factory.Trait(
            settings=factory.LazyFunction(
                lambda: {
                    "locked": True,
                    "visible": True,
                    "muted": False,
                    "solo": False,
                    "opacity": 1.0,
                    "volume": 1.0,
                }
            )
        )

        muted = factory.Trait(
            settings=factory.LazyFunction(
                lambda: {
                    "locked": False,
                    "visible": True,
                    "muted": True,
                    "solo": False,
                    "opacity": 1.0,
                    "volume": 0.0,
                }
            )
        )


class TrackItemFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating TrackItem instances in tests."""

    class Meta:
        # model = TrackItem  # Will be uncommented when model is created
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(lambda: fake.uuid4())

    # Item timing
    start_time = factory.LazyFunction(lambda: fake.random.uniform(0, 600))
    end_time = factory.LazyAttribute(
        lambda obj: obj.start_time + fake.random.uniform(5, 60)
    )
    duration = factory.LazyAttribute(lambda obj: obj.end_time - obj.start_time)

    # Trim settings
    trim_start = 0.0
    trim_end = factory.LazyAttribute(lambda obj: obj.duration)

    # Transform properties (JSON field)
    transform = factory.LazyFunction(
        lambda: {
            "position": {"x": 0, "y": 0},
            "scale": {"x": 1.0, "y": 1.0},
            "rotation": 0,
            "opacity": 1.0,
        }
    )

    # Effects (JSON field - array of effect definitions)
    effects = factory.LazyFunction(lambda: [])

    # Audio settings
    volume = 1.0
    fade_in = 0.0
    fade_out = 0.0

    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)

    # Relationships
    track_id = factory.LazyFunction(lambda: fake.uuid4())
    asset_id = factory.LazyFunction(lambda: fake.uuid4())
    transition_in_id = None
    transition_out_id = None

    class Params:
        with_fade = factory.Trait(
            fade_in=1.0,
            fade_out=1.0,
        )

        scaled = factory.Trait(
            transform={
                "position": {"x": 100, "y": 50},
                "scale": {"x": 1.5, "y": 1.5},
                "rotation": 0,
                "opacity": 1.0,
            }
        )

        rotated = factory.Trait(
            transform=factory.LazyFunction(
                lambda: {
                    "position": {"x": 0, "y": 0},
                    "scale": {"x": 1.0, "y": 1.0},
                    "rotation": fake.random_int(min=-180, max=180),
                    "opacity": 1.0,
                }
            )
        )

        semi_transparent = factory.Trait(
            transform={
                "position": {"x": 0, "y": 0},
                "scale": {"x": 1.0, "y": 1.0},
                "rotation": 0,
                "opacity": 0.5,
            }
        )

        with_blur = factory.Trait(
            effects=[
                {"type": "blur", "amount": 5},
            ]
        )

        with_color_correction = factory.Trait(
            effects=[
                {
                    "type": "color_correction",
                    "brightness": 10,
                    "contrast": 5,
                    "saturation": 0,
                }
            ]
        )


class AssetFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Asset instances in tests."""

    class Meta:
        # model = Asset  # Will be uncommented when model is created
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(lambda: fake.uuid4())

    # Asset metadata
    name = factory.LazyFunction(lambda: fake.file_name())
    asset_type = factory.LazyFunction(
        lambda: fake.random_element(["video", "audio", "image", "font"])
    )
    mime_type = factory.LazyFunction(
        lambda: fake.random_element([
            "video/mp4", "audio/mp3", "audio/wav", "image/png",
            "image/jpeg", "font/ttf", "font/otf"
        ])
    )

    # File metadata
    file_size = factory.LazyFunction(lambda: fake.random_int(min=100000, max=100000000))
    duration = factory.LazyFunction(lambda: fake.random.uniform(1, 600))

    # Media-specific metadata (JSON field)
    metadata = factory.LazyFunction(
        lambda: {
            "width": fake.random_int(min=640, max=3840),
            "height": fake.random_int(min=480, max=2160),
            "format": "mp4",
            "codec": "h264",
            "bitrate": fake.random_int(min=1000, max=20000),
        }
    )

    # Storage
    s3_key = factory.LazyFunction(lambda: f"assets/{fake.uuid4()}")
    cloudfront_url = factory.LazyFunction(
        lambda: f"https://d123456.cloudfront.net/assets/{fake.uuid4()}.mp4"
    )
    thumbnail_url = factory.LazyFunction(
        lambda: f"https://d123456.cloudfront.net/thumbnails/{fake.uuid4()}.jpg"
    )

    # Tags for organization (JSON field)
    tags = factory.LazyFunction(
        lambda: [fake.word() for _ in range(fake.random_int(min=1, max=3))]
    )

    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)

    # Relationships
    user_id = factory.LazyFunction(lambda: fake.uuid4())
    source_video_id = None

    class Params:
        video = factory.Trait(
            asset_type="video",
            mime_type="video/mp4",
            metadata={
                "width": 1920,
                "height": 1080,
                "format": "mp4",
                "codec": "h264",
                "bitrate": 8000,
                "framerate": 30,
            },
        )

        audio = factory.Trait(
            asset_type="audio",
            mime_type=factory.LazyFunction(lambda: fake.random_element(["audio/mp3", "audio/wav"])),
            metadata={
                "format": "mp3",
                "codec": "mp3",
                "bitrate": 320,
                "sample_rate": 48000,
                "channels": 2,
            },
        )

        image = factory.Trait(
            asset_type="image",
            mime_type=factory.LazyFunction(lambda: fake.random_element(["image/png", "image/jpeg"])),
            duration=None,
            metadata={
                "width": 1920,
                "height": 1080,
                "format": "png",
            },
        )

        font = factory.Trait(
            asset_type="font",
            mime_type=factory.LazyFunction(lambda: fake.random_element(["font/ttf", "font/otf"])),
            duration=None,
            thumbnail_url=None,
        )

        from_video = factory.Trait(
            source_video_id=factory.LazyFunction(lambda: fake.uuid4()),
        )
