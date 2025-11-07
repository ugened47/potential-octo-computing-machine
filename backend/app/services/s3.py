"""S3 storage service for video uploads."""

from uuid import UUID, uuid4

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings


class S3Service:
    """Service for handling S3/MinIO storage operations."""

    def __init__(self):
        """Initialize S3 service with boto3 client."""
        client_kwargs = {
            "service_name": "s3",
            "aws_access_key_id": settings.aws_access_key_id,
            "aws_secret_access_key": settings.aws_secret_access_key,
            "region_name": settings.aws_region,
        }
        
        # Add endpoint URL for MinIO in development
        endpoint_url = settings.s3_endpoint_url
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url
        
        self.s3_client = boto3.client(**client_kwargs)
        self.bucket = settings.s3_bucket

    def generate_presigned_url(
        self,
        user_id: UUID,
        video_id: UUID,
        filename: str,
        content_type: str,
        expires_in: int = 900,  # 15 minutes
    ) -> tuple[str, str]:
        """Generate presigned URL for direct browser upload.

        Args:
            user_id: User ID
            video_id: Video ID
            filename: Original filename
            content_type: MIME type of the file
            expires_in: URL expiration time in seconds (default: 900 = 15 minutes)

        Returns:
            Tuple of (presigned_url, s3_key)
        """
        # Extract file extension
        file_ext = filename.split(".")[-1] if "." in filename else ""
        
        # Generate UUID filename to avoid collisions
        uuid_filename = f"{uuid4()}.{file_ext}" if file_ext else str(uuid4())
        
        # Build S3 key: videos/{user_id}/{video_id}/{uuid_filename}
        s3_key = f"videos/{user_id}/{video_id}/{uuid_filename}"
        
        try:
            presigned_url = self.s3_client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": self.bucket,
                    "Key": s3_key,
                    "ContentType": content_type,
                },
                ExpiresIn=expires_in,
                HttpMethod="PUT",
            )
            return presigned_url, s3_key
        except ClientError as e:
            raise ValueError(f"Failed to generate presigned URL: {str(e)}") from e

    def get_cloudfront_url(self, s3_key: str) -> str | None:
        """Generate CloudFront URL for video delivery in production.

        Args:
            s3_key: S3 object key

        Returns:
            CloudFront URL if domain is configured, None otherwise
        """
        if not settings.cloudfront_domain:
            return None
        
        # Ensure CloudFront domain doesn't have protocol
        domain = settings.cloudfront_domain.replace("https://", "").replace("http://", "")
        return f"https://{domain}/{s3_key}"

    def delete_object(self, s3_key: str) -> None:
        """Delete an object from S3/MinIO.

        Args:
            s3_key: S3 object key to delete

        Raises:
            ValueError: If deletion fails
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=s3_key)
        except ClientError as e:
            raise ValueError(f"Failed to delete object from S3: {str(e)}") from e

    def ensure_bucket_exists(self) -> None:
        """Ensure the S3 bucket exists, create if it doesn't.

        This is mainly useful for MinIO local development.
        """
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
        except ClientError:
            # Bucket doesn't exist, create it
            try:
                if settings.s3_endpoint_url:
                    # MinIO: create bucket
                    self.s3_client.create_bucket(Bucket=self.bucket)
                else:
                    # AWS S3: create bucket with location constraint
                    self.s3_client.create_bucket(
                        Bucket=self.bucket,
                        CreateBucketConfiguration={
                            "LocationConstraint": settings.aws_region
                        },
                    )
            except ClientError as e:
                raise ValueError(f"Failed to create bucket: {str(e)}") from e

    def configure_cors(self) -> None:
        """Configure CORS on the S3 bucket for direct browser uploads.

        This is mainly useful for MinIO local development.
        """
        cors_configuration = {
            "CORSRules": [
                {
                    "AllowedOrigins": settings.allowed_origins,
                    "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
                    "AllowedHeaders": ["*"],
                    "ExposeHeaders": ["ETag"],
                    "MaxAgeSeconds": 3000,
                }
            ]
        }
        
        try:
            self.s3_client.put_bucket_cors(
                Bucket=self.bucket, CORSConfiguration=cors_configuration
            )
        except ClientError as e:
            raise ValueError(f"Failed to configure CORS: {str(e)}") from e

    def upload_thumbnail(
        self,
        user_id: UUID,
        video_id: UUID,
        thumbnail_path: str,
    ) -> str:
        """Upload thumbnail image to S3.

        Args:
            user_id: User ID
            video_id: Video ID
            thumbnail_path: Local path to thumbnail image file

        Returns:
            S3 key of uploaded thumbnail

        Raises:
            ValueError: If upload fails
        """
        # Build S3 key: thumbnails/{user_id}/{video_id}/thumbnail.jpg
        s3_key = f"thumbnails/{user_id}/{video_id}/thumbnail.jpg"
        
        try:
            with open(thumbnail_path, "rb") as thumbnail_file:
                self.s3_client.upload_fileobj(
                    thumbnail_file,
                    self.bucket,
                    s3_key,
                    ExtraArgs={"ContentType": "image/jpeg"},
                )
            return s3_key
        except (ClientError, IOError) as e:
            raise ValueError(f"Failed to upload thumbnail: {str(e)}") from e

    def get_thumbnail_url(self, s3_key: str) -> str:
        """Get public URL for thumbnail.

        Args:
            s3_key: S3 key of thumbnail

        Returns:
            Public URL (CloudFront in production, presigned URL in dev)
        """
        if settings.cloudfront_domain:
            domain = settings.cloudfront_domain.replace("https://", "").replace("http://", "")
            return f"https://{domain}/{s3_key}"
        
        # Generate presigned URL for MinIO/local development
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": s3_key},
                ExpiresIn=3600 * 24 * 7,  # 7 days
            )
            return url
        except ClientError as e:
            raise ValueError(f"Failed to generate thumbnail URL: {str(e)}") from e

