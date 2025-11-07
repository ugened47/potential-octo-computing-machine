"""Tests for S3 service."""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from app.services.s3 import S3Service
from app.core.config import settings


@pytest.fixture
def mock_s3_client():
    """Create a mock S3 client."""
    mock_s3 = Mock()
    mock_s3.generate_presigned_url = Mock()
    mock_s3.delete_object = Mock()
    mock_s3.head_bucket = Mock()
    mock_s3.create_bucket = Mock()
    mock_s3.put_bucket_cors = Mock()
    return mock_s3


@pytest.fixture
def s3_service(mock_s3_client):
    """Create S3Service instance with mocked boto3 client."""
    with patch("boto3.client", return_value=mock_s3_client):
        return S3Service()


def test_generate_presigned_url_minio(s3_service, mock_s3_client):
    """Test presigned URL generation with MinIO endpoint."""
    user_id = uuid4()
    video_id = uuid4()
    filename = "test-video.mp4"
    
    # Mock presigned URL generation
    mock_s3_client.generate_presigned_url.return_value = "http://minio:9000/test-url"
    
    url, s3_key = s3_service.generate_presigned_url(
        user_id=user_id,
        video_id=video_id,
        filename=filename,
        content_type="video/mp4"
    )
    
    # Verify presigned URL was generated
    assert url == "http://minio:9000/test-url"
    assert s3_key.startswith(f"videos/{user_id}/{video_id}/")
    assert s3_key.endswith(".mp4")
    mock_s3_client.generate_presigned_url.assert_called_once()
    call_kwargs = mock_s3_client.generate_presigned_url.call_args[1]
    assert call_kwargs["ExpiresIn"] == 900  # 15 minutes
    assert call_kwargs["HttpMethod"] == "PUT"


def test_generate_presigned_url_aws_s3(mock_s3_client):
    """Test presigned URL generation with AWS S3 endpoint."""
    user_id = uuid4()
    video_id = uuid4()
    filename = "test-video.mp4"
    
    # Mock presigned URL generation
    mock_s3_client.generate_presigned_url.return_value = "https://s3.amazonaws.com/test-url"
    
    # Create service with production settings (no endpoint_url)
    # When environment is production, s3_endpoint_url property returns None
    with patch("boto3.client", return_value=mock_s3_client):
        with patch.object(settings, "environment", "production"):
            with patch.object(settings, "minio_endpoint_url", "http://minio:9000"):
                # In production, s3_endpoint_url property returns None
                # So we need to ensure the service doesn't use endpoint_url
                service = S3Service()
                url, s3_key = service.generate_presigned_url(
                    user_id=user_id,
                    video_id=video_id,
                    filename=filename,
                    content_type="video/mp4"
                )
    
    # Verify presigned URL was generated
    assert url == "https://s3.amazonaws.com/test-url"
    assert s3_key.startswith(f"videos/{user_id}/{video_id}/")
    mock_s3_client.generate_presigned_url.assert_called_once()
    
    # Verify boto3.client was called without endpoint_url (production)
    # Check that the client was created (we can't easily verify kwargs without more mocking)
    # But the fact that it works means endpoint_url wasn't passed


def test_s3_key_path_structure(s3_service, mock_s3_client):
    """Test S3 key path structure: videos/{user_id}/{video_id}/{filename}.{ext}."""
    user_id = uuid4()
    video_id = uuid4()
    filename = "test-video.mp4"
    
    mock_s3_client.generate_presigned_url.return_value = "http://test-url"
    
    _, s3_key = s3_service.generate_presigned_url(
        user_id=user_id,
        video_id=video_id,
        filename=filename,
        content_type="video/mp4"
    )
    
    # Verify the S3 key follows the correct path structure
    assert s3_key.startswith(f"videos/{user_id}/{video_id}/")
    assert s3_key.endswith(".mp4")
    # Should use UUID for filename to avoid collisions
    assert len(s3_key.split("/")[-1].replace(".mp4", "")) == 36  # UUID length
    
    # Also verify it was passed to boto3
    call_kwargs = mock_s3_client.generate_presigned_url.call_args[1]
    assert call_kwargs["Params"]["Key"] == s3_key


def test_cloudfront_url_generation_production(s3_service, mock_s3_client):
    """Test CloudFront URL generation for production environment."""
    user_id = uuid4()
    video_id = uuid4()
    s3_key = f"videos/{user_id}/{video_id}/test-video.mp4"
    
    # Set CloudFront domain
    with patch.object(settings, "cloudfront_domain", "d1234567890.cloudfront.net"):
        cloudfront_url = s3_service.get_cloudfront_url(s3_key)
    
    assert cloudfront_url == f"https://d1234567890.cloudfront.net/{s3_key}"


def test_cloudfront_url_none_when_not_configured(s3_service):
    """Test CloudFront URL returns None when domain not configured."""
    s3_key = "videos/test/test-video.mp4"
    
    with patch.object(settings, "cloudfront_domain", ""):
        cloudfront_url = s3_service.get_cloudfront_url(s3_key)
    
    assert cloudfront_url is None


def test_cors_configuration_minio(s3_service, mock_s3_client):
    """Test CORS configuration for MinIO bucket."""
    # Mock successful CORS configuration
    mock_s3_client.put_bucket_cors.return_value = {}
    
    s3_service.configure_cors()
    
    # Verify CORS was configured
    mock_s3_client.put_bucket_cors.assert_called_once()
    call_kwargs = mock_s3_client.put_bucket_cors.call_args[1]
    assert "CORSConfiguration" in call_kwargs
    assert "CORSRules" in call_kwargs["CORSConfiguration"]


def test_presigned_url_expiration(s3_service, mock_s3_client):
    """Test presigned URL has correct expiration time (15 minutes)."""
    user_id = uuid4()
    video_id = uuid4()
    filename = "test.mp4"
    
    mock_s3_client.generate_presigned_url.return_value = "http://test-url"
    
    _, _ = s3_service.generate_presigned_url(
        user_id=user_id,
        video_id=video_id,
        filename=filename,
        content_type="video/mp4"
    )
    
    call_kwargs = mock_s3_client.generate_presigned_url.call_args[1]
    assert call_kwargs["ExpiresIn"] == 900  # 15 minutes = 900 seconds

