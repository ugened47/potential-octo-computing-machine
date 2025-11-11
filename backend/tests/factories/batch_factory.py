"""Batch processing model factories for testing."""

import factory
from datetime import datetime
from faker import Faker

fake = Faker()


class BatchJobFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating BatchJob instances in tests."""

    class Meta:
        # model = BatchJob  # Will be uncommented when model is created
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(lambda: fake.uuid4())

    # Job metadata
    name = factory.LazyFunction(lambda: f"Batch Job - {fake.job()}")
    description = factory.LazyFunction(lambda: fake.paragraph(nb_sentences=2))

    # Processing settings (JSON field)
    settings = factory.LazyFunction(
        lambda: {
            "transcribe": True,
            "remove_silence": True,
            "detect_highlights": True,
            "silence_threshold": -40,
            "highlight_sensitivity": "medium",
            "auto_export": False,
            "export_format": "mp4",
            "export_quality": "high",
        }
    )

    # Status and progress
    status = factory.LazyFunction(
        lambda: fake.random_element(["pending", "processing", "completed", "failed", "paused"])
    )
    total_videos = factory.LazyFunction(lambda: fake.random_int(min=2, max=20))
    completed_videos = factory.LazyFunction(lambda: fake.random_int(min=0, max=10))
    failed_videos = factory.LazyFunction(lambda: fake.random_int(min=0, max=3))
    progress = factory.LazyAttribute(
        lambda obj: round((obj.completed_videos / obj.total_videos * 100), 2)
        if obj.total_videos > 0 else 0
    )

    # Error tracking
    error_message = None

    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    started_at = None
    completed_at = None

    # Relationships
    user_id = factory.LazyFunction(lambda: fake.uuid4())

    class Params:
        """Parameterized traits for different batch job states."""

        pending = factory.Trait(
            status="pending",
            completed_videos=0,
            failed_videos=0,
            progress=0,
            started_at=None,
            completed_at=None,
        )

        processing = factory.Trait(
            status="processing",
            started_at=factory.LazyFunction(datetime.utcnow),
            completed_at=None,
        )

        completed = factory.Trait(
            status="completed",
            completed_videos=factory.LazyAttribute(lambda obj: obj.total_videos),
            failed_videos=0,
            progress=100.0,
            started_at=factory.LazyFunction(datetime.utcnow),
            completed_at=factory.LazyFunction(datetime.utcnow),
        )

        failed = factory.Trait(
            status="failed",
            error_message=factory.LazyFunction(lambda: fake.sentence()),
            completed_at=None,
        )

        paused = factory.Trait(
            status="paused",
        )

        small = factory.Trait(
            total_videos=factory.LazyFunction(lambda: fake.random_int(min=2, max=5)),
        )

        large = factory.Trait(
            total_videos=factory.LazyFunction(lambda: fake.random_int(min=20, max=100)),
        )

        with_failures = factory.Trait(
            failed_videos=factory.LazyFunction(lambda: fake.random_int(min=1, max=5)),
        )


class BatchVideoFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating BatchVideo instances in tests."""

    class Meta:
        # model = BatchVideo  # Will be uncommented when model is created
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(lambda: fake.uuid4())

    # Processing status
    status = factory.LazyFunction(
        lambda: fake.random_element(["pending", "processing", "completed", "failed"])
    )
    progress = factory.LazyFunction(lambda: fake.random_int(min=0, max=100))
    error_message = None

    # Processing steps
    upload_completed = False
    transcription_completed = False
    silence_removal_completed = False
    highlight_detection_completed = False
    export_completed = False

    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    started_at = None
    completed_at = None

    # Relationships
    batch_job_id = factory.LazyFunction(lambda: fake.uuid4())
    video_id = factory.LazyFunction(lambda: fake.uuid4())

    class Params:
        """Parameterized traits for different batch video states."""

        pending = factory.Trait(
            status="pending",
            progress=0,
            started_at=None,
            completed_at=None,
        )

        processing = factory.Trait(
            status="processing",
            upload_completed=True,
            started_at=factory.LazyFunction(datetime.utcnow),
        )

        completed = factory.Trait(
            status="completed",
            progress=100,
            upload_completed=True,
            transcription_completed=True,
            silence_removal_completed=True,
            highlight_detection_completed=True,
            export_completed=True,
            started_at=factory.LazyFunction(datetime.utcnow),
            completed_at=factory.LazyFunction(datetime.utcnow),
        )

        failed = factory.Trait(
            status="failed",
            error_message=factory.LazyFunction(lambda: fake.sentence()),
            completed_at=None,
        )

        transcribed = factory.Trait(
            upload_completed=True,
            transcription_completed=True,
            progress=40,
        )

        silence_removed = factory.Trait(
            upload_completed=True,
            transcription_completed=True,
            silence_removal_completed=True,
            progress=60,
        )

        highlights_detected = factory.Trait(
            upload_completed=True,
            transcription_completed=True,
            silence_removal_completed=True,
            highlight_detection_completed=True,
            progress=80,
        )
