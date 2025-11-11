"""Subtitle model factories for testing."""

import factory
from datetime import datetime
from faker import Faker

fake = Faker()


class SubtitleStyleFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating SubtitleStyle instances in tests."""

    class Meta:
        # model = SubtitleStyle  # Will be uncommented when model is created
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(lambda: fake.uuid4())

    # Style metadata
    name = factory.LazyFunction(lambda: fake.catch_phrase())
    description = factory.LazyFunction(lambda: fake.paragraph(nb_sentences=1))
    is_preset = False

    # Font settings
    font_family = factory.LazyFunction(
        lambda: fake.random_element([
            "Arial", "Helvetica", "Roboto", "Open Sans", "Montserrat",
            "Lato", "Poppins", "Inter", "Nunito"
        ])
    )
    font_size = factory.LazyFunction(lambda: fake.random_int(min=24, max=72))
    font_weight = factory.LazyFunction(
        lambda: fake.random_element(["normal", "bold", "400", "500", "600", "700", "800"])
    )
    font_style = factory.LazyFunction(lambda: fake.random_element(["normal", "italic"]))

    # Text color and effects
    text_color = factory.LazyFunction(
        lambda: fake.random_element(["#FFFFFF", "#000000", "#FFFF00", "#00FF00", "#FF0000"])
    )
    text_opacity = factory.LazyFunction(lambda: fake.random.uniform(0.8, 1.0))
    outline_color = factory.LazyFunction(
        lambda: fake.random_element(["#000000", "#FFFFFF", "#333333"])
    )
    outline_width = factory.LazyFunction(lambda: fake.random_int(min=0, max=4))
    shadow_color = factory.LazyFunction(lambda: fake.random_element(["#000000", "#333333"]))
    shadow_offset_x = factory.LazyFunction(lambda: fake.random_int(min=-3, max=3))
    shadow_offset_y = factory.LazyFunction(lambda: fake.random_int(min=-3, max=3))
    shadow_blur = factory.LazyFunction(lambda: fake.random_int(min=0, max=5))

    # Background settings
    background_color = factory.LazyFunction(
        lambda: fake.random_element(["#000000", "#FFFFFF", "transparent"])
    )
    background_opacity = factory.LazyFunction(lambda: fake.random.uniform(0.0, 0.8))
    background_padding = factory.LazyFunction(lambda: fake.random_int(min=5, max=20))
    background_radius = factory.LazyFunction(lambda: fake.random_int(min=0, max=10))

    # Position and alignment
    position = factory.LazyFunction(
        lambda: fake.random_element(["bottom", "top", "middle"])
    )
    alignment = factory.LazyFunction(
        lambda: fake.random_element(["center", "left", "right"])
    )
    margin_horizontal = factory.LazyFunction(lambda: fake.random_int(min=20, max=100))
    margin_vertical = factory.LazyFunction(lambda: fake.random_int(min=20, max=100))

    # Animation
    animation_type = factory.LazyFunction(
        lambda: fake.random_element(["none", "fade", "slide", "pop", "typewriter"])
    )
    animation_duration = factory.LazyFunction(lambda: fake.random.uniform(0.2, 1.0))

    # Advanced settings
    max_width = factory.LazyFunction(lambda: fake.random_int(min=60, max=90))
    line_height = factory.LazyFunction(lambda: fake.random.uniform(1.2, 1.8))
    letter_spacing = factory.LazyFunction(lambda: fake.random.uniform(-1.0, 2.0))
    text_transform = factory.LazyFunction(
        lambda: fake.random_element(["none", "uppercase", "lowercase", "capitalize"])
    )

    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)

    # Relationships
    user_id = factory.LazyFunction(lambda: fake.uuid4())

    class Params:
        """Parameterized traits for different subtitle styles."""

        preset = factory.Trait(
            is_preset=True,
            user_id=None,
        )

        minimal = factory.Trait(
            name="Minimal",
            font_family="Arial",
            font_size=36,
            font_weight="normal",
            text_color="#FFFFFF",
            outline_width=0,
            background_color="transparent",
            position="bottom",
            alignment="center",
            animation_type="none",
        )

        bold = factory.Trait(
            name="Bold",
            font_family="Montserrat",
            font_size=48,
            font_weight="bold",
            text_color="#FFFFFF",
            outline_color="#000000",
            outline_width=3,
            background_color="#000000",
            background_opacity=0.7,
            position="bottom",
            animation_type="pop",
        )

        gaming = factory.Trait(
            name="Gaming",
            font_family="Roboto",
            font_size=42,
            font_weight="700",
            text_color="#00FF00",
            outline_color="#000000",
            outline_width=2,
            text_transform="uppercase",
            animation_type="slide",
        )

        professional = factory.Trait(
            name="Professional",
            font_family="Inter",
            font_size=32,
            font_weight="500",
            text_color="#FFFFFF",
            background_color="#000000",
            background_opacity=0.8,
            background_padding=15,
            background_radius=5,
            position="bottom",
            alignment="center",
        )


class SubtitleTranslationFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating SubtitleTranslation instances in tests."""

    class Meta:
        # model = SubtitleTranslation  # Will be uncommented when model is created
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(lambda: fake.uuid4())

    # Translation metadata
    source_language = "en"
    target_language = factory.LazyFunction(
        lambda: fake.random_element(["es", "fr", "de", "ru", "zh", "ja", "ko", "pt", "it", "ar"])
    )

    # Translation content (JSON field - SRT format data)
    translated_content = factory.LazyFunction(
        lambda: {
            "subtitles": [
                {
                    "index": i,
                    "start": f"00:00:{i*5:02d},000",
                    "end": f"00:00:{i*5+3:02d},000",
                    "text": fake.sentence(nb_words=10),
                }
                for i in range(10)
            ]
        }
    )

    # Processing status
    status = factory.LazyFunction(
        lambda: fake.random_element(["pending", "processing", "completed", "failed"])
    )
    progress = factory.LazyFunction(lambda: fake.random_int(min=0, max=100))
    error_message = None

    # Translation service metadata
    translation_service = "google"
    cost = factory.LazyFunction(lambda: fake.random.uniform(0.01, 5.0))
    character_count = factory.LazyFunction(lambda: fake.random_int(min=100, max=5000))

    # Quality metrics
    confidence_score = factory.LazyFunction(lambda: fake.random.uniform(0.85, 0.99))

    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    completed_at = None

    # Relationships
    transcript_id = factory.LazyFunction(lambda: fake.uuid4())
    user_id = factory.LazyFunction(lambda: fake.uuid4())

    class Params:
        """Parameterized traits for different translation states."""

        pending = factory.Trait(
            status="pending",
            progress=0,
            translated_content=None,
            completed_at=None,
        )

        processing = factory.Trait(
            status="processing",
            progress=factory.LazyFunction(lambda: fake.random_int(min=1, max=99)),
            completed_at=None,
        )

        completed = factory.Trait(
            status="completed",
            progress=100,
            completed_at=factory.LazyFunction(datetime.utcnow),
        )

        failed = factory.Trait(
            status="failed",
            error_message=factory.LazyFunction(lambda: fake.sentence()),
            translated_content=None,
            completed_at=None,
        )

        spanish = factory.Trait(
            target_language="es",
        )

        french = factory.Trait(
            target_language="fr",
        )

        german = factory.Trait(
            target_language="de",
        )

        chinese = factory.Trait(
            target_language="zh",
        )

        japanese = factory.Trait(
            target_language="ja",
        )

        high_confidence = factory.Trait(
            confidence_score=factory.LazyFunction(lambda: fake.random.uniform(0.95, 0.99)),
        )

        low_cost = factory.Trait(
            cost=factory.LazyFunction(lambda: fake.random.uniform(0.01, 0.5)),
            character_count=factory.LazyFunction(lambda: fake.random_int(min=100, max=500)),
        )

        high_cost = factory.Trait(
            cost=factory.LazyFunction(lambda: fake.random.uniform(3.0, 10.0)),
            character_count=factory.LazyFunction(lambda: fake.random_int(min=5000, max=20000)),
        )
