"""S3-compatible cloud storage backend."""

import io
from datetime import datetime
from typing import BinaryIO, Iterator, Optional

from .interface import StorageInterface


class S3Storage(StorageInterface):
    """S3-compatible storage implementation (AWS S3, MinIO, etc.)."""

    def __init__(
        self,
        bucket: str,
        region: str = "eu-central-1",
        endpoint_url: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
    ):
        """Initialize S3 storage.
        
        Args:
            bucket: S3 bucket name
            region: AWS region
            endpoint_url: Custom endpoint for S3-compatible services (MinIO, etc.)
            access_key: AWS access key (uses env vars if not provided)
            secret_key: AWS secret key (uses env vars if not provided)
        """
        try:
            import boto3
            from botocore.config import Config
        except ImportError:
            raise ImportError("boto3 required for S3 storage: pip install boto3")

        self.bucket = bucket
        self.region = region

        config = Config(region_name=region)
        
        client_kwargs = {"config": config}
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url
        if access_key and secret_key:
            client_kwargs["aws_access_key_id"] = access_key
            client_kwargs["aws_secret_access_key"] = secret_key

        self.client = boto3.client("s3", **client_kwargs)
        self.resource = boto3.resource("s3", **client_kwargs)
        self.bucket_obj = self.resource.Bucket(bucket)

    def save(self, data: bytes, path: str) -> str:
        """Save binary data to S3."""
        self.client.put_object(Bucket=self.bucket, Key=path, Body=data)
        return f"s3://{self.bucket}/{path}"

    def save_file(self, file: BinaryIO, path: str) -> str:
        """Save file object to S3."""
        self.client.upload_fileobj(file, self.bucket, path)
        return f"s3://{self.bucket}/{path}"

    def load(self, path: str) -> bytes:
        """Load binary data from S3."""
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=path)
            return response["Body"].read()
        except self.client.exceptions.NoSuchKey:
            raise FileNotFoundError(f"File not found: {path}")

    def load_stream(self, path: str) -> BinaryIO:
        """Load data as stream from S3."""
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=path)
            return response["Body"]
        except self.client.exceptions.NoSuchKey:
            raise FileNotFoundError(f"File not found: {path}")

    def delete(self, path: str) -> bool:
        """Delete object from S3."""
        try:
            self.client.delete_object(Bucket=self.bucket, Key=path)
            return True
        except Exception:
            return False

    def exists(self, path: str) -> bool:
        """Check if object exists in S3."""
        try:
            self.client.head_object(Bucket=self.bucket, Key=path)
            return True
        except Exception:
            return False

    def list(self, prefix: str = "") -> Iterator[str]:
        """List all objects with given prefix."""
        paginator = self.client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                yield obj["Key"]

    def get_url(self, path: str, expires_in: int = 3600) -> str:
        """Get presigned URL for S3 object."""
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": path},
            ExpiresIn=expires_in,
        )

    def get_metadata(self, path: str) -> dict:
        """Get object metadata from S3."""
        try:
            response = self.client.head_object(Bucket=self.bucket, Key=path)
            return {
                "size": response["ContentLength"],
                "modified": response["LastModified"].isoformat(),
                "etag": response["ETag"],
                "content_type": response.get("ContentType", ""),
                "path": f"s3://{self.bucket}/{path}",
            }
        except Exception:
            raise FileNotFoundError(f"File not found: {path}")
