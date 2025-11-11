"""Tests for asset API endpoints."""

from io import BytesIO
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app


@pytest.fixture
def client(db_session: AsyncSession) -> TestClient:
    """Create a test client with database session override."""
    from app.api.deps import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user."""
    from app.models.user import User

    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def other_user(db_session: AsyncSession):
    """Create another test user for authorization tests."""
    from app.models.user import User

    user = User(
        email="other@example.com",
        hashed_password="hashed_password",
        full_name="Other User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Create auth headers for test user."""
    from app.api.deps import get_current_user

    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
async def test_asset(db_session: AsyncSession, test_user):
    """Create a test asset."""
    from app.models.asset import Asset

    asset = Asset(
        user_id=test_user.id,
        asset_type="image",
        name="Test Image",
        file_url="https://s3.amazonaws.com/bucket/test-image.png",
        file_size=1024 * 100,  # 100 KB
        mime_type="image/png",
        width=1920,
        height=1080,
        tags=["test", "sample"],
    )
    db_session.add(asset)
    await db_session.commit()
    await db_session.refresh(asset)
    return asset


@pytest.mark.asyncio
async def test_post_assets_upload_image(
    client: TestClient, test_user, auth_headers: dict
):
    """Test POST /api/assets uploads image asset."""
    with patch("app.services.s3.S3Service.upload_file") as mock_upload:
        mock_upload.return_value = "https://s3.amazonaws.com/bucket/assets/image.png"

        # Create fake image file
        file_content = b"fake image content"
        files = {"file": ("test-image.png", BytesIO(file_content), "image/png")}
        data = {
            "asset_type": "image",
            "name": "My Image",
            "tags": "logo,branding",
        }

        response = client.post(
            "/api/assets",
            files=files,
            data=data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        json_data = response.json()
        assert json_data["asset_type"] == "image"
        assert json_data["name"] == "My Image"
        assert "logo" in json_data["tags"]
        assert "branding" in json_data["tags"]
        assert "file_url" in json_data


@pytest.mark.asyncio
async def test_post_assets_upload_audio(
    client: TestClient, test_user, auth_headers: dict
):
    """Test POST /api/assets uploads audio asset."""
    with patch("app.services.s3.S3Service.upload_file") as mock_upload:
        mock_upload.return_value = "https://s3.amazonaws.com/bucket/assets/audio.mp3"

        file_content = b"fake audio content"
        files = {"file": ("background-music.mp3", BytesIO(file_content), "audio/mpeg")}
        data = {
            "asset_type": "audio",
            "name": "Background Music",
            "tags": "music,background",
        }

        response = client.post(
            "/api/assets",
            files=files,
            data=data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        json_data = response.json()
        assert json_data["asset_type"] == "audio"
        assert json_data["name"] == "Background Music"


@pytest.mark.asyncio
async def test_post_assets_generates_thumbnail(
    client: TestClient, test_user, auth_headers: dict
):
    """Test POST /api/assets generates thumbnail for images."""
    with patch("app.services.s3.S3Service.upload_file") as mock_upload, \
         patch("app.services.asset_service.AssetService.generate_thumbnail") as mock_thumbnail:
        mock_upload.return_value = "https://s3.amazonaws.com/bucket/assets/image.png"
        mock_thumbnail.return_value = "https://s3.amazonaws.com/bucket/assets/thumbnails/image_thumb.png"

        file_content = b"fake image content"
        files = {"file": ("image.png", BytesIO(file_content), "image/png")}
        data = {
            "asset_type": "image",
            "name": "Image with Thumbnail",
        }

        response = client.post(
            "/api/assets",
            files=files,
            data=data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        json_data = response.json()
        assert json_data["thumbnail_url"] is not None


@pytest.mark.asyncio
async def test_post_assets_validation_errors(
    client: TestClient, auth_headers: dict
):
    """Test POST /api/assets with validation errors."""
    # Missing file
    response = client.post(
        "/api/assets",
        data={"asset_type": "image", "name": "No File"},
        headers=auth_headers,
    )
    assert response.status_code == 422

    # Invalid file type
    with patch("app.services.s3.S3Service.upload_file"):
        file_content = b"fake content"
        files = {"file": ("script.exe", BytesIO(file_content), "application/x-msdownload")}
        data = {"asset_type": "image", "name": "Invalid File"}

        response = client.post(
            "/api/assets",
            files=files,
            data=data,
            headers=auth_headers,
        )
        assert response.status_code == 400  # Invalid file type


@pytest.mark.asyncio
async def test_get_assets_lists_user_assets(
    client: TestClient, test_user, auth_headers: dict, db_session: AsyncSession
):
    """Test GET /api/assets lists user's assets."""
    from app.models.asset import Asset

    # Create multiple assets
    for i in range(5):
        asset = Asset(
            user_id=test_user.id,
            asset_type="image" if i % 2 == 0 else "audio",
            name=f"Asset {i}",
            file_url=f"https://s3.amazonaws.com/bucket/asset-{i}.png",
            file_size=1024 * (i + 1),
            mime_type="image/png" if i % 2 == 0 else "audio/mp3",
        )
        db_session.add(asset)
    await db_session.commit()

    response = client.get("/api/assets", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "assets" in data
    assert len(data["assets"]) >= 5
    assert "total" in data


@pytest.mark.asyncio
async def test_get_assets_with_type_filter(
    client: TestClient, test_user, auth_headers: dict, db_session: AsyncSession
):
    """Test GET /api/assets with asset_type filter."""
    from app.models.asset import Asset

    # Create assets of different types
    for asset_type in ["image", "audio", "font"]:
        for i in range(2):
            asset = Asset(
                user_id=test_user.id,
                asset_type=asset_type,
                name=f"{asset_type} Asset {i}",
                file_url=f"https://s3.amazonaws.com/bucket/{asset_type}-{i}",
                file_size=1024,
                mime_type=f"{asset_type}/test",
            )
            db_session.add(asset)
    await db_session.commit()

    # Filter by asset type
    response = client.get("/api/assets?asset_type=image", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert all(asset["asset_type"] == "image" for asset in data["assets"])


@pytest.mark.asyncio
async def test_get_assets_with_tag_filter(
    client: TestClient, test_user, auth_headers: dict, db_session: AsyncSession
):
    """Test GET /api/assets with tags filter."""
    from app.models.asset import Asset

    # Create assets with different tags
    asset1 = Asset(
        user_id=test_user.id,
        asset_type="image",
        name="Logo",
        file_url="https://s3.amazonaws.com/bucket/logo.png",
        file_size=1024,
        mime_type="image/png",
        tags=["logo", "branding"],
    )
    asset2 = Asset(
        user_id=test_user.id,
        asset_type="image",
        name="Background",
        file_url="https://s3.amazonaws.com/bucket/bg.png",
        file_size=1024,
        mime_type="image/png",
        tags=["background", "texture"],
    )
    db_session.add_all([asset1, asset2])
    await db_session.commit()

    # Filter by tag
    response = client.get("/api/assets?tags=logo", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["assets"]) >= 1
    assert any("logo" in asset["tags"] for asset in data["assets"])


@pytest.mark.asyncio
async def test_get_assets_with_pagination(
    client: TestClient, test_user, auth_headers: dict, db_session: AsyncSession
):
    """Test GET /api/assets with pagination."""
    from app.models.asset import Asset

    # Create 10 assets
    for i in range(10):
        asset = Asset(
            user_id=test_user.id,
            asset_type="image",
            name=f"Asset {i}",
            file_url=f"https://s3.amazonaws.com/bucket/asset-{i}.png",
            file_size=1024,
            mime_type="image/png",
        )
        db_session.add(asset)
    await db_session.commit()

    # Test pagination
    response = client.get("/api/assets?limit=5&offset=0", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["assets"]) == 5

    response = client.get("/api/assets?limit=5&offset=5", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["assets"]) == 5


@pytest.mark.asyncio
async def test_get_asset_returns_asset_details(
    client: TestClient, test_user, auth_headers: dict, test_asset
):
    """Test GET /api/assets/{id} returns asset details with presigned URL."""
    with patch("app.services.s3.S3Service.generate_presigned_url") as mock_presigned:
        mock_presigned.return_value = ("https://presigned-url.com", "s3-key")

        response = client.get(f"/api/assets/{test_asset.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_asset.id)
        assert data["name"] == "Test Image"
        assert data["asset_type"] == "image"


@pytest.mark.asyncio
async def test_get_asset_not_found(client: TestClient, auth_headers: dict):
    """Test GET /api/assets/{id} returns 404 for non-existent asset."""
    fake_id = uuid4()
    response = client.get(f"/api/assets/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_patch_asset_updates_metadata(
    client: TestClient, test_user, auth_headers: dict, test_asset
):
    """Test PATCH /api/assets/{id} updates asset metadata."""
    response = client.patch(
        f"/api/assets/{test_asset.id}",
        json={
            "name": "Updated Asset Name",
            "tags": ["updated", "new-tag"],
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Asset Name"
    assert "updated" in data["tags"]
    assert "new-tag" in data["tags"]


@pytest.mark.asyncio
async def test_delete_asset_deletes_asset_and_files(
    client: TestClient, test_user, auth_headers: dict, test_asset, db_session: AsyncSession
):
    """Test DELETE /api/assets/{id} deletes asset and S3 files."""
    asset_id = test_asset.id

    with patch("app.services.s3.S3Service.delete_object") as mock_delete:
        response = client.delete(f"/api/assets/{asset_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify S3 delete was called
        assert mock_delete.called

    # Verify asset was deleted from database
    from sqlmodel import select
    from app.models.asset import Asset

    result = await db_session.execute(select(Asset).where(Asset.id == asset_id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_get_assets_search(
    client: TestClient, test_user, auth_headers: dict, db_session: AsyncSession
):
    """Test GET /api/assets/search searches assets by name."""
    from app.models.asset import Asset

    # Create assets with different names
    assets = [
        Asset(
            user_id=test_user.id,
            asset_type="image",
            name="Company Logo",
            file_url="https://s3.amazonaws.com/bucket/logo.png",
            file_size=1024,
            mime_type="image/png",
        ),
        Asset(
            user_id=test_user.id,
            asset_type="image",
            name="Background Image",
            file_url="https://s3.amazonaws.com/bucket/bg.png",
            file_size=1024,
            mime_type="image/png",
        ),
        Asset(
            user_id=test_user.id,
            asset_type="audio",
            name="Logo Jingle",
            file_url="https://s3.amazonaws.com/bucket/jingle.mp3",
            file_size=1024,
            mime_type="audio/mp3",
        ),
    ]
    db_session.add_all(assets)
    await db_session.commit()

    # Search for "logo"
    response = client.get("/api/assets/search?q=logo", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["assets"]) >= 2
    assert all("logo" in asset["name"].lower() for asset in data["assets"])


@pytest.mark.asyncio
async def test_get_assets_increments_usage_count(
    client: TestClient, test_user, auth_headers: dict, test_asset, db_session: AsyncSession
):
    """Test using an asset increments its usage_count."""
    from app.models.project import Project, Track, TrackItem

    # Create project and track
    project = Project(
        user_id=test_user.id,
        name="Test Project",
        width=1920,
        height=1080,
        frame_rate=30.0,
        duration_seconds=60.0,
        status="draft",
    )
    db_session.add(project)
    await db_session.commit()

    track = Track(
        project_id=project.id,
        track_type="image",
        name="Image Track",
        z_index=0,
    )
    db_session.add(track)
    await db_session.commit()

    # Add track item using the asset
    item = TrackItem(
        track_id=track.id,
        item_type="image",
        source_type="asset",
        source_id=test_asset.id,
        start_time=0.0,
        end_time=10.0,
        duration=10.0,
    )
    db_session.add(item)
    await db_session.commit()

    # Verify usage count was incremented
    await db_session.refresh(test_asset)
    assert test_asset.usage_count == 1


@pytest.mark.asyncio
async def test_authorization_users_can_only_access_own_assets(
    client: TestClient,
    test_user,
    other_user,
    auth_headers: dict,
    db_session: AsyncSession,
):
    """Test authorization - users can only access their own assets."""
    from app.models.asset import Asset

    # Create asset for other user
    other_asset = Asset(
        user_id=other_user.id,
        asset_type="image",
        name="Other User's Asset",
        file_url="https://s3.amazonaws.com/bucket/other.png",
        file_size=1024,
        mime_type="image/png",
    )
    db_session.add(other_asset)
    await db_session.commit()
    await db_session.refresh(other_asset)

    # Try to access other user's asset
    response = client.get(f"/api/assets/{other_asset.id}", headers=auth_headers)
    assert response.status_code == 403

    # Try to update other user's asset
    response = client.patch(
        f"/api/assets/{other_asset.id}",
        json={"name": "Hacked Asset"},
        headers=auth_headers,
    )
    assert response.status_code == 403

    # Try to delete other user's asset
    response = client.delete(f"/api/assets/{other_asset.id}", headers=auth_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_assets_with_public_assets(
    client: TestClient, test_user, auth_headers: dict, db_session: AsyncSession
):
    """Test GET /api/assets includes public assets."""
    from app.models.asset import Asset

    # Create private asset
    private_asset = Asset(
        user_id=test_user.id,
        asset_type="image",
        name="Private Asset",
        file_url="https://s3.amazonaws.com/bucket/private.png",
        file_size=1024,
        mime_type="image/png",
        is_public=False,
    )

    # Create public asset (system asset)
    public_asset = Asset(
        user_id=test_user.id,  # Could be admin/system user
        asset_type="font",
        name="Arial Font",
        file_url="https://s3.amazonaws.com/bucket/arial.ttf",
        file_size=1024,
        mime_type="font/ttf",
        is_public=True,
    )

    db_session.add_all([private_asset, public_asset])
    await db_session.commit()

    response = client.get("/api/assets", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    # Should include both private and public assets
    assert len(data["assets"]) >= 2
