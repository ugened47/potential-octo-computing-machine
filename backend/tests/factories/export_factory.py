"""Export model factory for testing."""

import factory
from datetime import datetime
from faker import Faker

from app.models import Export

fake = Faker()


class ExportFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Export instances in tests."""

    class Meta:
        model = Export
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(lambda: fake.uuid4())

    # Export configuration
    resolution = factory.LazyFunction(
        lambda: fake.random_element(["720p", "1080p", "4k"])
    )
    format = factory.LazyFunction(lambda: fake.random_element(["mp4", "mov", "webm"]))
    quality_preset = factory.LazyFunction(lambda: fake.random_element(["high", "medium", "low"]))
    export_type = factory.LazyFunction(
        lambda: fake.random_element(["single", "combined", "clips"])
    )

    # Segments to export (JSON field)
    segment_selections = factory.LazyFunction(
        lambda: [
            {
                "start_time": fake.random.uniform(0, 100),
                "end_time": fake.random.uniform(101, 200),
                "clip_id": None,
            }
            for _ in range(fake.random_int(min=1, max=5))
        ]
    )

    # Processing status
    status = factory.LazyFunction(
        lambda: fake.random_element(["pending", "processing", "completed", "failed", "cancelled"])
    )
    progress_percentage = factory.LazyFunction(lambda: fake.random_int(min=0, max=100))
    error_message = None

    # Output
    output_s3_key = factory.LazyFunction(
        lambda: f"exports/{fake.uuid4()}/{fake.uuid4()}.mp4"
    )
    output_url = factory.LazyFunction(
        lambda: f"https://d123456.cloudfront.net/exports/{fake.uuid4()}.mp4"
    )
    file_size_bytes = factory.LazyFunction(lambda: fake.random_int(min=5000000, max=500000000))
    total_duration_seconds = factory.LazyFunction(lambda: fake.random_int(min=10, max=3600))

    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    started_at = None
    completed_at = None

    # Relationships
    video_id = factory.LazyFunction(lambda: fake.uuid4())
    user_id = factory.LazyFunction(lambda: fake.uuid4())

    class Params:
        """Parameterized traits for different export states."""

        pending = factory.Trait(
            status="pending",
            progress_percentage=0,
            output_url=None,
            output_s3_key=None,
            file_size_bytes=None,
            started_at=None,
            completed_at=None,
        )

        processing = factory.Trait(
            status="processing",
            progress_percentage=factory.LazyFunction(lambda: fake.random_int(min=1, max=99)),
            output_url=None,
            output_s3_key=None,
            file_size_bytes=None,
            started_at=factory.LazyFunction(datetime.utcnow),
            completed_at=None,
        )

        completed = factory.Trait(
            status="completed",
            progress_percentage=100,
            started_at=factory.LazyFunction(datetime.utcnow),
            completed_at=factory.LazyFunction(datetime.utcnow),
        )

        failed = factory.Trait(
            status="failed",
            progress_percentage=factory.LazyFunction(lambda: fake.random_int(min=0, max=99)),
            error_message=factory.LazyFunction(lambda: fake.sentence()),
            output_url=None,
            output_s3_key=None,
            file_size_bytes=None,
            started_at=factory.LazyFunction(datetime.utcnow),
            completed_at=None,
        )

        hd = factory.Trait(
            resolution="1080p",
            quality_preset="high",
            format="mp4",
        )

        uhd = factory.Trait(
            resolution="4k",
            quality_preset="high",
            format="mp4",
        )

        web_optimized = factory.Trait(
            resolution="720p",
            quality_preset="medium",
            format="webm",
        )

        individual_clips = factory.Trait(
            export_type="clips",
        )

        combined_clips = factory.Trait(
            export_type="combined",
        )
