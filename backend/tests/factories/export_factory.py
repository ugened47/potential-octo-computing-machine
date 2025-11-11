"""Export model factory for testing."""

import factory
from datetime import datetime
from faker import Faker

fake = Faker()


# Note: Export model doesn't exist yet, so we define expected fields based on spec
class ExportFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Export instances in tests."""

    class Meta:
        # model = Export  # Will be uncommented when model is created
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(lambda: fake.uuid4())

    # Export configuration
    resolution = factory.LazyFunction(
        lambda: fake.random_element(["720p", "1080p", "1440p", "2160p"])
    )
    format = factory.LazyFunction(lambda: fake.random_element(["mp4", "mov", "webm"]))
    quality = factory.LazyFunction(lambda: fake.random_element(["high", "medium", "low"]))
    export_type = factory.LazyFunction(
        lambda: fake.random_element(["full", "clips", "merged_clips"])
    )

    # Segments to export (JSON field)
    segments = factory.LazyFunction(
        lambda: [
            {
                "start": fake.random.uniform(0, 100),
                "end": fake.random.uniform(101, 200),
            }
            for _ in range(fake.random_int(min=1, max=5))
        ]
    )

    # Processing status
    status = factory.LazyFunction(
        lambda: fake.random_element(["pending", "processing", "completed", "failed"])
    )
    progress = factory.LazyFunction(lambda: fake.random_int(min=0, max=100))
    error_message = None

    # Output
    output_url = factory.LazyFunction(
        lambda: f"https://d123456.cloudfront.net/exports/{fake.uuid4()}.mp4"
    )
    file_size = factory.LazyFunction(lambda: fake.random_int(min=5000000, max=500000000))

    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    completed_at = None

    # Relationships
    video_id = factory.LazyFunction(lambda: fake.uuid4())
    user_id = factory.LazyFunction(lambda: fake.uuid4())

    class Params:
        """Parameterized traits for different export states."""

        pending = factory.Trait(
            status="pending",
            progress=0,
            output_url=None,
            file_size=None,
            completed_at=None,
        )

        processing = factory.Trait(
            status="processing",
            progress=factory.LazyFunction(lambda: fake.random_int(min=1, max=99)),
            output_url=None,
            file_size=None,
            completed_at=None,
        )

        completed = factory.Trait(
            status="completed",
            progress=100,
            completed_at=factory.LazyFunction(datetime.utcnow),
        )

        failed = factory.Trait(
            status="failed",
            progress=factory.LazyFunction(lambda: fake.random_int(min=0, max=99)),
            error_message=factory.LazyFunction(lambda: fake.sentence()),
            output_url=None,
            file_size=None,
            completed_at=None,
        )

        hd = factory.Trait(
            resolution="1080p",
            quality="high",
            format="mp4",
        )

        uhd = factory.Trait(
            resolution="2160p",
            quality="high",
            format="mp4",
        )

        web_optimized = factory.Trait(
            resolution="720p",
            quality="medium",
            format="webm",
        )

        individual_clips = factory.Trait(
            export_type="clips",
        )

        merged_clips = factory.Trait(
            export_type="merged_clips",
        )
