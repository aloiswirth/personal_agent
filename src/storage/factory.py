"""Storage factory - creates storage instances based on configuration."""

from typing import Optional

from .interface import StorageInterface
from .local import LocalStorage


def get_storage(
    backend: str = "local",
    local_path: str = "./data",
    nas_path: str = "",
    s3_bucket: str = "",
    s3_region: str = "eu-central-1",
    s3_endpoint: Optional[str] = None,
) -> StorageInterface:
    """Factory function to create storage backend.
    
    Args:
        backend: Storage backend type ("local", "nas", "s3")
        local_path: Path for local storage
        nas_path: Path for NAS storage (mounted filesystem)
        s3_bucket: S3 bucket name
        s3_region: S3 region
        s3_endpoint: Custom S3 endpoint (for MinIO, etc.)
        
    Returns:
        StorageInterface implementation
        
    Raises:
        ValueError: If backend is not supported
    """
    if backend == "local":
        return LocalStorage(base_path=local_path)
    
    elif backend == "nas":
        # NAS is just local storage with a different path (mounted filesystem)
        if not nas_path:
            raise ValueError("nas_path required for NAS storage")
        return LocalStorage(base_path=nas_path)
    
    elif backend == "s3":
        from .s3 import S3Storage
        if not s3_bucket:
            raise ValueError("s3_bucket required for S3 storage")
        return S3Storage(
            bucket=s3_bucket,
            region=s3_region,
            endpoint_url=s3_endpoint,
        )
    
    else:
        raise ValueError(f"Unsupported storage backend: {backend}")


def get_storage_from_settings() -> StorageInterface:
    """Create storage from application settings."""
    from src.config import get_settings
    
    settings = get_settings()
    return get_storage(
        backend=settings.storage_backend,
        local_path=settings.storage_local_path,
        nas_path=settings.storage_nas_path,
        s3_bucket=settings.storage_s3_bucket,
        s3_region=settings.storage_s3_region,
    )
