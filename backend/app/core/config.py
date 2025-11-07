"""Application configuration."""

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # Application
    app_name: str = "AI Video Editor"
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"]
    )

    # Database
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/videodb"
    )

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Security
    secret_key: str = Field(default="change-this-in-production")
    jwt_secret_key: str = Field(default="change-this-in-production")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=30)

    # AWS S3 / MinIO
    aws_access_key_id: str = Field(default="")
    aws_secret_access_key: str = Field(default="")
    aws_region: str = Field(default="us-east-1")
    s3_bucket: str = Field(default="video-editor-uploads")
    cloudfront_domain: str = Field(default="")
    minio_endpoint_url: str = Field(default="http://minio:9000")
    
    @property
    def s3_endpoint_url(self) -> str | None:
        """Get S3 endpoint URL based on environment.
        
        Returns:
            MinIO endpoint URL for development, None for production (uses AWS S3)
        """
        if self.environment == "development":
            return self.minio_endpoint_url
        return None

    # OpenAI
    openai_api_key: str = Field(default="")

    # File Upload
    max_upload_size_mb: int = Field(default=2048)  # 2GB
    allowed_video_formats: List[str] = Field(
        default=["mp4", "mov", "avi", "webm", "mkv"]
    )

    # Processing
    default_silence_threshold_db: int = Field(default=-40)
    default_min_silence_duration_ms: int = Field(default=1000)

    # Rate Limiting
    rate_limit_uploads_per_hour: int = Field(default=5)
    rate_limit_api_per_minute: int = Field(default=100)

    @property
    def max_upload_size_bytes(self) -> int:
        """Get max upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024


# Global settings instance
settings = Settings()
