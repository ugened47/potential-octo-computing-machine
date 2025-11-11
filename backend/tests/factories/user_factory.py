"""User model factory for testing."""

import factory
from datetime import datetime, timedelta
from faker import Faker

from app.models.user import User

fake = Faker()


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating User instances in tests."""

    class Meta:
        model = User
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(lambda: fake.uuid4())
    email = factory.LazyFunction(lambda: fake.email())
    hashed_password = factory.LazyFunction(
        lambda: "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqHHfGHxoK"  # "password"
    )
    full_name = factory.LazyFunction(lambda: fake.name())
    is_active = True
    is_superuser = False
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)

    # OAuth fields
    oauth_provider = None
    oauth_id = None

    # Email verification
    email_verified = False
    email_verification_token = None
    email_verification_expires = None

    # Password reset
    password_reset_token = None
    password_reset_expires = None

    class Params:
        """Parameterized traits for different user states."""

        verified = factory.Trait(
            email_verified=True,
            email_verification_token=None,
            email_verification_expires=None,
        )

        superuser = factory.Trait(
            is_superuser=True,
            email_verified=True,
        )

        inactive = factory.Trait(
            is_active=False,
        )

        google_oauth = factory.Trait(
            oauth_provider="google",
            oauth_id=factory.LazyFunction(lambda: fake.uuid4()),
            email_verified=True,
        )

        with_verification_token = factory.Trait(
            email_verification_token=factory.LazyFunction(lambda: fake.uuid4()),
            email_verification_expires=factory.LazyFunction(
                lambda: datetime.utcnow() + timedelta(hours=24)
            ),
        )

        with_reset_token = factory.Trait(
            password_reset_token=factory.LazyFunction(lambda: fake.uuid4()),
            password_reset_expires=factory.LazyFunction(
                lambda: datetime.utcnow() + timedelta(hours=1)
            ),
        )
