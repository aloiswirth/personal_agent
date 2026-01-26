"""Local filesystem storage backend."""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Iterator

from .interface import StorageInterface


class LocalStorage(StorageInterface):
    """Local filesystem storage implementation."""

    def __init__(self, base_path: str = "./data"):
        """Initialize local storage.
        
        Args:
            base_path: Base directory for all storage operations
        """
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _full_path(self, path: str) -> Path:
        """Get full path from relative path."""
        return self.base_path / path

    def save(self, data: bytes, path: str) -> str:
        """Save binary data to local filesystem."""
        full_path = self._full_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(data)
        return str(full_path)

    def save_file(self, file: BinaryIO, path: str) -> str:
        """Save file object to local filesystem."""
        full_path = self._full_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "wb") as f:
            shutil.copyfileobj(file, f)
        return str(full_path)

    def load(self, path: str) -> bytes:
        """Load binary data from local filesystem."""
        full_path = self._full_path(path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return full_path.read_bytes()

    def load_stream(self, path: str) -> BinaryIO:
        """Load data as stream from local filesystem."""
        full_path = self._full_path(path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return open(full_path, "rb")

    def delete(self, path: str) -> bool:
        """Delete file from local filesystem."""
        full_path = self._full_path(path)
        if full_path.exists():
            if full_path.is_dir():
                shutil.rmtree(full_path)
            else:
                full_path.unlink()
            return True
        return False

    def exists(self, path: str) -> bool:
        """Check if path exists in local filesystem."""
        return self._full_path(path).exists()

    def list(self, prefix: str = "") -> Iterator[str]:
        """List all files with given prefix."""
        search_path = self._full_path(prefix) if prefix else self.base_path
        
        if not search_path.exists():
            return
        
        if search_path.is_file():
            yield prefix
            return
        
        for item in search_path.rglob("*"):
            if item.is_file():
                yield str(item.relative_to(self.base_path))

    def get_url(self, path: str) -> str:
        """Get file:// URL for local file."""
        full_path = self._full_path(path)
        return f"file://{full_path}"

    def get_metadata(self, path: str) -> dict:
        """Get file metadata."""
        full_path = self._full_path(path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        stat = full_path.stat()
        return {
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "is_dir": full_path.is_dir(),
            "path": str(full_path),
        }
