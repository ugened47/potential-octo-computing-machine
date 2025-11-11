"""Video model factory for testing."""

import factory
from datetime import datetime
from faker import Faker

from app.models.video import Video, VideoStatus

fake = Faker()


class VideoFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Video instances in tests."""

    class Meta:
        model = Video
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(lambda: fake.uuid4())
    title = factory.LazyFunction(lambda: fake.sentence(nb_words=4)[:-1])
    description = factory.LazyFunction(lambda: fake.paragraph(nb_sentences=3))

    # File metadata
    file_size = factory.LazyFunction(lambda: fake.random_int(min=1000000, max=2000000000))
    format = factory.LazyFunction(lambda: fake.random_element(["mp4", "mov", "avi", "webm", "mkv"]))
    duration = factory.LazyFunction(lambda: fake.random_int(min=60, max=3600))
    resolution = factory.LazyFunction(
        lambda: fake.random_element(["1920x1080", "1280x720", "3840x2160", "2560x1440"])
    )
    s3_key = factory.LazyFunction(lambda: f"videos/{fake.uuid4()}.mp4")
    cloudfront_url = factory.LazyFunction(
        lambda: f"https://d123456.cloudfront.net/videos/{fake.uuid4()}.mp4"
    )
    thumbnail_url = factory.LazyFunction(
        lambda: f"https://d123456.cloudfront.net/thumbnails/{fake.uuid4()}.jpg"
    )

    # Processing status
    status = VideoStatus.UPLOADED

    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)

    # Relationships - user_id must be provided or use SubFactory
    user_id = factory.LazyFunction(lambda: fake.uuid4())

    class Params:
        """Parameterized traits for different video states."""

        uploaded = factory.Trait(
            status=VideoStatus.UPLOADED,
            duration=None,
            resolution=None,
        )

        processing = factory.Trait(
            status=VideoStatus.PROCESSING,
        )

        completed = factory.Trait(
            status=VideoStatus.COMPLETED,
        )

        failed = factory.Trait(
            status=VideoStatus.FAILED,
            duration=None,
            resolution=None,
        )

        short = factory.Trait(
            duration=factory.LazyFunction(lambda: fake.random_int(min=30, max=300)),
            title=factory.LazyFunction(lambda: f"{fake.sentence(nb_words=3)[:-1]} - Short"),
        )

        long = factory.Trait(
            duration=factory.LazyFunction(lambda: fake.random_int(min=3600, max=7200)),
            title=factory.LazyFunction(lambda: f"{fake.sentence(nb_words=3)[:-1]} - Full Length"),
        )

        hd = factory.Trait(
            resolution="1920x1080",
            format="mp4",
        )

        uhd = factory.Trait(
            resolution="3840x2160",
            format="mp4",
        )
