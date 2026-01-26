"""Storage interface - abstract base class for all storage backends."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Iterator


class StorageInterface(ABC):
    """Abstract interface for storage backends.
    
    All storage implementations (local, NAS, S3, etc.) must implement this interface.
    This allows seamless switching between storage backends.
    """

    @abstractmethod
    def save(self, data: bytes, path: str) -> str:
        """Save binary data to the specified path.
        
        Args:
            data: Binary data to save
            path: Relative path within the storage (e.g., "recordings/2024/audio.mp3")
            
        Returns:
            Full path/URI where data was saved
        """
        pass

    @abstractmethod
    def save_file(self, file: BinaryIO, path: str) -> str:
        """Save a file object to the specified path.
        
        Args:
            file: File-like object to save
            path: Relative path within the storage
            
        Returns:
            Full path/URI where file was saved
        """
        pass

    @abstractmethod
    def load(self, path: str) -> bytes:
        """Load binary data from the specified path.
        
        Args:
            path: Relative path within the storage
            
        Returns:
            Binary data
            
        Raises:
            FileNotFoundError: If path does not exist
        """
        pass

    @abstractmethod
    def load_stream(self, path: str) -> BinaryIO:
        """Load data as a stream (for large files).
        
        Args:
            path: Relative path within the storage
            
        Returns:
            File-like object for streaming
        """
        pass

    @abstractmethod
    def delete(self, path: str) -> bool:
        """Delete data at the specified path.
        
        Args:
            path: Relative path within the storage
            
        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if path exists.
        
        Args:
            path: Relative path within the storage
            
        Returns:
            True if exists, False otherwise
        """
        pass

    @abstractmethod
    def list(self, prefix: str = "") -> Iterator[str]:
        """List all paths with the given prefix.
        
        Args:
            prefix: Path prefix to filter by (e.g., "recordings/2024/")
            
        Yields:
            Relative paths matching the prefix
        """
        pass

    @abstractmethod
    def get_url(self, path: str) -> str:
        """Get a URL/URI for the stored data.
        
        Args:
            path: Relative path within the storage
            
        Returns:
            URL or file path that can be used to access the data
        """
        pass

    @abstractmethod
    def get_metadata(self, path: str) -> dict:
        """Get metadata for stored data.
        
        Args:
            path: Relative path within the storage
            
        Returns:
            Dict with metadata (size, created, modified, etc.)
        """
        pass
