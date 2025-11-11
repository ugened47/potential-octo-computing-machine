"""Clip model factory for testing."""

import factory
from datetime import datetime
from faker import Faker

from app.models.clip import Clip, ClipStatus

fake = Faker()


class ClipFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Clip instances in tests."""

    class Meta:
        model = Clip
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(lambda: fake.uuid4())

    # Clip metadata
    title = factory.LazyFunction(lambda: fake.sentence(nb_words=4)[:-1])
    description = factory.LazyFunction(lambda: fake.paragraph(nb_sentences=2))
    keywords = factory.LazyFunction(
        lambda: [fake.word() for _ in range(fake.random_int(min=2, max=5))]
    )

    # Clip timing
    start_time = factory.LazyFunction(lambda: fake.random.uniform(0, 600))
    end_time = factory.LazyAttribute(
        lambda obj: obj.start_time + fake.random.uniform(5, 60)
    )
    duration = factory.LazyAttribute(lambda obj: obj.end_time - obj.start_time)

    # Storage
    clip_url = factory.LazyFunction(
        lambda: f"https://d123456.cloudfront.net/clips/{fake.uuid4()}.mp4"
    )
    status = ClipStatus.COMPLETED

    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)

    # Relationships - video_id must be provided or use SubFactory
    video_id = factory.LazyFunction(lambda: fake.uuid4())

    class Params:
        """Parameterized traits for different clip states."""

        processing = factory.Trait(
            status=ClipStatus.PROCESSING,
            clip_url=None,
        )

        failed = factory.Trait(
            status=ClipStatus.FAILED,
            clip_url=None,
        )

        short = factory.Trait(
            start_time=factory.LazyFunction(lambda: fake.random.uniform(0, 600)),
            end_time=factory.LazyAttribute(
                lambda obj: obj.start_time + fake.random.uniform(5, 15)
            ),
            title=factory.LazyFunction(lambda: f"{fake.sentence(nb_words=2)[:-1]} - Quick Clip"),
        )

        medium = factory.Trait(
            start_time=factory.LazyFunction(lambda: fake.random.uniform(0, 600)),
            end_time=factory.LazyAttribute(
                lambda obj: obj.start_time + fake.random.uniform(30, 60)
            ),
        )

        long = factory.Trait(
            start_time=factory.LazyFunction(lambda: fake.random.uniform(0, 600)),
            end_time=factory.LazyAttribute(
                lambda obj: obj.start_time + fake.random.uniform(120, 300)
            ),
            title=factory.LazyFunction(lambda: f"{fake.sentence(nb_words=3)[:-1]} - Extended"),
        )

        keyword_highlight = factory.Trait(
            keywords=["important", "key point", "highlight"],
            title="Keyword Highlight Clip",
        )

        silence_removed = factory.Trait(
            keywords=["silence removed", "cleaned"],
            description="Clip with silence automatically removed",
        )

        intro = factory.Trait(
            start_time=0.0,
            end_time=30.0,
            duration=30.0,
            title="Introduction",
            keywords=["intro", "beginning"],
        )

        outro = factory.Trait(
            title="Outro",
            keywords=["outro", "ending", "conclusion"],
        )
