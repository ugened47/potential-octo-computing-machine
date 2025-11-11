"""Highlight model factory for testing."""

import factory
from datetime import datetime
from faker import Faker

fake = Faker()


class HighlightFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Highlight instances in tests."""

    class Meta:
        # model = Highlight  # Will be uncommented when model is created
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(lambda: fake.uuid4())

    # Highlight timing
    start_time = factory.LazyFunction(lambda: fake.random.uniform(0, 1800))
    end_time = factory.LazyAttribute(
        lambda obj: obj.start_time + fake.random.uniform(10, 60)
    )
    duration = factory.LazyAttribute(lambda obj: obj.end_time - obj.start_time)

    # Scoring components (0-100)
    audio_score = factory.LazyFunction(lambda: fake.random.uniform(0, 100))
    scene_score = factory.LazyFunction(lambda: fake.random.uniform(0, 100))
    speech_score = factory.LazyFunction(lambda: fake.random.uniform(0, 100))
    keyword_score = factory.LazyFunction(lambda: fake.random.uniform(0, 100))

    # Composite score (weighted average)
    total_score = factory.LazyAttribute(
        lambda obj: round(
            (obj.audio_score * 0.3 + obj.scene_score * 0.2 +
             obj.speech_score * 0.3 + obj.keyword_score * 0.2),
            2
        )
    )

    # Metadata
    title = factory.LazyFunction(lambda: fake.sentence(nb_words=4)[:-1])
    description = factory.LazyFunction(lambda: fake.paragraph(nb_sentences=2))
    keywords = factory.LazyFunction(
        lambda: [fake.word() for _ in range(fake.random_int(min=2, max=5))]
    )

    # Detection metadata
    detection_method = factory.LazyFunction(
        lambda: fake.random_element(["auto", "manual", "keyword"])
    )
    sensitivity = factory.LazyFunction(
        lambda: fake.random_element(["low", "medium", "high"])
    )

    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)

    # Relationships
    video_id = factory.LazyFunction(lambda: fake.uuid4())

    class Params:
        """Parameterized traits for different highlight types."""

        high_quality = factory.Trait(
            audio_score=factory.LazyFunction(lambda: fake.random.uniform(80, 100)),
            scene_score=factory.LazyFunction(lambda: fake.random.uniform(80, 100)),
            speech_score=factory.LazyFunction(lambda: fake.random.uniform(80, 100)),
            keyword_score=factory.LazyFunction(lambda: fake.random.uniform(80, 100)),
            sensitivity="high",
        )

        medium_quality = factory.Trait(
            audio_score=factory.LazyFunction(lambda: fake.random.uniform(50, 79)),
            scene_score=factory.LazyFunction(lambda: fake.random.uniform(50, 79)),
            speech_score=factory.LazyFunction(lambda: fake.random.uniform(50, 79)),
            keyword_score=factory.LazyFunction(lambda: fake.random.uniform(50, 79)),
            sensitivity="medium",
        )

        low_quality = factory.Trait(
            audio_score=factory.LazyFunction(lambda: fake.random.uniform(20, 49)),
            scene_score=factory.LazyFunction(lambda: fake.random.uniform(20, 49)),
            speech_score=factory.LazyFunction(lambda: fake.random.uniform(20, 49)),
            keyword_score=factory.LazyFunction(lambda: fake.random.uniform(20, 49)),
            sensitivity="low",
        )

        audio_driven = factory.Trait(
            audio_score=factory.LazyFunction(lambda: fake.random.uniform(85, 100)),
            scene_score=factory.LazyFunction(lambda: fake.random.uniform(40, 60)),
            speech_score=factory.LazyFunction(lambda: fake.random.uniform(40, 60)),
            keyword_score=factory.LazyFunction(lambda: fake.random.uniform(30, 50)),
            description="Highlight driven by audio energy and dynamics",
        )

        keyword_driven = factory.Trait(
            audio_score=factory.LazyFunction(lambda: fake.random.uniform(40, 60)),
            scene_score=factory.LazyFunction(lambda: fake.random.uniform(40, 60)),
            speech_score=factory.LazyFunction(lambda: fake.random.uniform(50, 70)),
            keyword_score=factory.LazyFunction(lambda: fake.random.uniform(85, 100)),
            keywords=["important", "key point", "highlight", "crucial"],
            detection_method="keyword",
        )

        scene_change = factory.Trait(
            audio_score=factory.LazyFunction(lambda: fake.random.uniform(40, 60)),
            scene_score=factory.LazyFunction(lambda: fake.random.uniform(85, 100)),
            speech_score=factory.LazyFunction(lambda: fake.random.uniform(50, 70)),
            keyword_score=factory.LazyFunction(lambda: fake.random.uniform(40, 60)),
            description="Highlight with significant scene changes",
        )

        manual = factory.Trait(
            detection_method="manual",
            total_score=100.0,
        )

        short = factory.Trait(
            duration=factory.LazyFunction(lambda: fake.random.uniform(5, 15)),
        )

        long = factory.Trait(
            duration=factory.LazyFunction(lambda: fake.random.uniform(60, 120)),
        )
