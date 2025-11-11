"""Transcript model factory for testing."""

import factory
from datetime import datetime
from faker import Faker

from app.models.transcript import Transcript, TranscriptStatus

fake = Faker()


def generate_word_timestamps() -> dict:
    """Generate realistic word-level timestamps for testing."""
    words = fake.sentence(nb_words=50).split()
    timestamps = []
    current_time = 0.0

    for i, word in enumerate(words):
        word_duration = fake.random.uniform(0.2, 0.8)
        timestamps.append({
            "word": word,
            "start": round(current_time, 3),
            "end": round(current_time + word_duration, 3),
            "confidence": fake.random.uniform(0.85, 0.99),
        })
        current_time += word_duration + fake.random.uniform(0.1, 0.3)  # Add pause

    return {
        "words": timestamps,
        "segments": [
            {
                "id": i,
                "start": timestamps[max(0, i * 10)]["start"],
                "end": timestamps[min(len(timestamps) - 1, (i + 1) * 10 - 1)]["end"],
                "text": " ".join([w["word"] for w in timestamps[i * 10:(i + 1) * 10]]),
            }
            for i in range((len(timestamps) + 9) // 10)
        ],
    }


class TranscriptFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Transcript instances in tests."""

    class Meta:
        model = Transcript
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(lambda: fake.uuid4())

    # Transcript content
    full_text = factory.LazyFunction(lambda: fake.text(max_nb_chars=2000))
    word_timestamps = factory.LazyFunction(generate_word_timestamps)

    # Metadata
    language = "en"
    status = TranscriptStatus.COMPLETED
    accuracy_score = factory.LazyFunction(lambda: fake.random.uniform(0.85, 0.99))

    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    completed_at = factory.LazyFunction(datetime.utcnow)

    # Relationships - video_id must be provided or use SubFactory
    video_id = factory.LazyFunction(lambda: fake.uuid4())

    class Params:
        """Parameterized traits for different transcript states."""

        processing = factory.Trait(
            status=TranscriptStatus.PROCESSING,
            full_text="",
            word_timestamps={},
            accuracy_score=None,
            completed_at=None,
        )

        failed = factory.Trait(
            status=TranscriptStatus.FAILED,
            full_text="",
            word_timestamps={},
            accuracy_score=None,
            completed_at=None,
        )

        spanish = factory.Trait(
            language="es",
            full_text=factory.LazyFunction(lambda: fake.text(max_nb_chars=2000, ext_word_list=None)),
        )

        russian = factory.Trait(
            language="ru",
        )

        german = factory.Trait(
            language="de",
        )

        french = factory.Trait(
            language="fr",
        )

        high_accuracy = factory.Trait(
            accuracy_score=factory.LazyFunction(lambda: fake.random.uniform(0.95, 0.99)),
        )

        low_accuracy = factory.Trait(
            accuracy_score=factory.LazyFunction(lambda: fake.random.uniform(0.70, 0.85)),
        )

        short = factory.Trait(
            full_text=factory.LazyFunction(lambda: fake.sentence(nb_words=50)),
        )

        long = factory.Trait(
            full_text=factory.LazyFunction(lambda: fake.text(max_nb_chars=10000)),
        )
