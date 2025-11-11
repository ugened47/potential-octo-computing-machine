"""Collaboration model factories for testing."""

import factory
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()


class OrganizationFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Organization instances in tests."""

    class Meta:
        # model = Organization  # Will be uncommented when model is created
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(lambda: fake.uuid4())

    # Organization metadata
    name = factory.LazyFunction(lambda: fake.company())
    slug = factory.LazyFunction(lambda: fake.slug())
    description = factory.LazyFunction(lambda: fake.paragraph(nb_sentences=2))

    # Settings (JSON field)
    settings = factory.LazyFunction(
        lambda: {
            "default_permissions": "viewer",
            "allow_public_sharing": True,
            "require_approval": False,
            "max_members": 10,
        }
    )

    # Billing
    plan = factory.LazyFunction(lambda: fake.random_element(["free", "pro", "business", "enterprise"]))
    is_active = True

    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)

    # Relationships
    owner_id = factory.LazyFunction(lambda: fake.uuid4())

    class Params:
        free_plan = factory.Trait(plan="free")
        pro_plan = factory.Trait(plan="pro")
        business_plan = factory.Trait(plan="business")
        enterprise_plan = factory.Trait(plan="enterprise")
        inactive = factory.Trait(is_active=False)


class TeamMemberFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating TeamMember instances in tests."""

    class Meta:
        # model = TeamMember  # Will be uncommented when model is created
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(lambda: fake.uuid4())

    # Role and permissions
    role = factory.LazyFunction(lambda: fake.random_element(["owner", "admin", "editor", "viewer"]))
    permissions = factory.LazyFunction(
        lambda: ["view", "edit", "comment", "share", "delete", "manage_members"]
    )

    # Status
    status = factory.LazyFunction(lambda: fake.random_element(["active", "invited", "suspended"]))
    invitation_token = None
    invitation_expires = None

    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    joined_at = factory.LazyFunction(datetime.utcnow)

    # Relationships
    organization_id = factory.LazyFunction(lambda: fake.uuid4())
    user_id = factory.LazyFunction(lambda: fake.uuid4())

    class Params:
        owner = factory.Trait(role="owner", status="active")
        admin = factory.Trait(role="admin", status="active")
        editor = factory.Trait(role="editor", status="active", permissions=["view", "edit", "comment"])
        viewer = factory.Trait(role="viewer", status="active", permissions=["view", "comment"])
        invited = factory.Trait(
            status="invited",
            invitation_token=factory.LazyFunction(lambda: fake.uuid4()),
            invitation_expires=factory.LazyFunction(lambda: datetime.utcnow() + timedelta(days=7)),
            joined_at=None,
        )
        suspended = factory.Trait(status="suspended")


class VideoShareFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating VideoShare instances in tests."""

    class Meta:
        # model = VideoShare  # Will be uncommented when model is created
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(lambda: fake.uuid4())

    # Share type and permissions
    share_type = factory.LazyFunction(lambda: fake.random_element(["user", "team", "public_link"]))
    permission = factory.LazyFunction(lambda: fake.random_element(["viewer", "editor", "admin"]))

    # Public link settings
    public_token = None
    is_public = False
    requires_password = False
    password_hash = None
    expires_at = None
    max_views = None
    view_count = 0

    # Settings (JSON field)
    settings = factory.LazyFunction(
        lambda: {
            "allow_download": True,
            "allow_comments": True,
            "show_watermark": False,
        }
    )

    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    last_accessed_at = None

    # Relationships
    video_id = factory.LazyFunction(lambda: fake.uuid4())
    shared_by_user_id = factory.LazyFunction(lambda: fake.uuid4())
    shared_with_user_id = None
    shared_with_organization_id = None

    class Params:
        user_share = factory.Trait(
            share_type="user",
            shared_with_user_id=factory.LazyFunction(lambda: fake.uuid4()),
        )

        team_share = factory.Trait(
            share_type="team",
            shared_with_organization_id=factory.LazyFunction(lambda: fake.uuid4()),
        )

        public_link = factory.Trait(
            share_type="public_link",
            is_public=True,
            public_token=factory.LazyFunction(lambda: fake.uuid4()),
        )

        with_password = factory.Trait(
            requires_password=True,
            password_hash="$2b$12$hashed_password",
        )

        with_expiration = factory.Trait(
            expires_at=factory.LazyFunction(lambda: datetime.utcnow() + timedelta(days=7)),
        )

        limited_views = factory.Trait(
            max_views=100,
        )


class CommentFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Comment instances in tests."""

    class Meta:
        # model = Comment  # Will be uncommented when model is created
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(lambda: fake.uuid4())

    # Comment content
    content = factory.LazyFunction(lambda: fake.paragraph(nb_sentences=3))

    # Timeline position (optional - for timeline comments)
    timestamp = factory.LazyFunction(lambda: fake.random.uniform(0, 600))

    # Threading
    parent_comment_id = None

    # Mentions (JSON field - list of user IDs)
    mentions = factory.LazyFunction(lambda: [])

    # Reactions (JSON field)
    reactions = factory.LazyFunction(lambda: {})

    # Status
    is_resolved = False
    is_edited = False

    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    edited_at = None

    # Relationships
    video_id = factory.LazyFunction(lambda: fake.uuid4())
    user_id = factory.LazyFunction(lambda: fake.uuid4())

    class Params:
        timeline_comment = factory.Trait(
            timestamp=factory.LazyFunction(lambda: fake.random.uniform(0, 600)),
        )

        reply = factory.Trait(
            parent_comment_id=factory.LazyFunction(lambda: fake.uuid4()),
        )

        with_mentions = factory.Trait(
            mentions=factory.LazyFunction(lambda: [fake.uuid4() for _ in range(2)]),
        )

        with_reactions = factory.Trait(
            reactions={
                "thumbs_up": 5,
                "heart": 3,
                "laugh": 2,
            },
        )

        resolved = factory.Trait(is_resolved=True)

        edited = factory.Trait(
            is_edited=True,
            edited_at=factory.LazyFunction(datetime.utcnow),
        )


class VersionFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Version instances in tests."""

    class Meta:
        # model = Version  # Will be uncommented when model is created
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(lambda: fake.uuid4())

    # Version metadata
    version_number = factory.LazyFunction(lambda: fake.random_int(min=1, max=100))
    name = factory.LazyFunction(lambda: f"Version {fake.random_int(min=1, max=100)}")
    description = factory.LazyFunction(lambda: fake.sentence())

    # Snapshot data (JSON field - stores timeline state, segments, etc.)
    snapshot_data = factory.LazyFunction(
        lambda: {
            "segments": [
                {
                    "start": fake.random.uniform(0, 100),
                    "end": fake.random.uniform(101, 200),
                }
                for _ in range(3)
            ],
            "settings": {
                "silence_removed": True,
                "highlights_detected": True,
            },
            "metadata": {
                "duration": fake.random_int(min=60, max=600),
                "clips_count": fake.random_int(min=1, max=10),
            },
        }
    )

    # Version status
    is_current = False

    # S3 storage (if version has exported file)
    s3_key = factory.LazyFunction(lambda: f"versions/{fake.uuid4()}.mp4")
    file_size = factory.LazyFunction(lambda: fake.random_int(min=5000000, max=500000000))

    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)

    # Relationships
    video_id = factory.LazyFunction(lambda: fake.uuid4())
    created_by_user_id = factory.LazyFunction(lambda: fake.uuid4())

    class Params:
        current = factory.Trait(is_current=True)

        initial = factory.Trait(
            version_number=1,
            name="Initial Version",
            description="Original upload",
        )

        auto_saved = factory.Trait(
            name=factory.LazyFunction(lambda: f"Auto-save {fake.date_time()}"),
            description="Automatically saved version",
        )
