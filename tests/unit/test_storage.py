"""Unit tests for storage backends."""

import tempfile
from pathlib import Path

import pytest

from src.storage import LocalStorage, get_storage


class TestLocalStorage:
    """Tests for LocalStorage backend."""

    @pytest.fixture
    def storage(self, tmp_path):
        """Create a LocalStorage instance with temp directory."""
        return LocalStorage(base_path=str(tmp_path))

    def test_save_and_load(self, storage):
        """Test saving and loading data."""
        data = b"Hello, World!"
        path = "test/file.txt"
        
        storage.save(data, path)
        loaded = storage.load(path)
        
        assert loaded == data

    def test_save_creates_directories(self, storage):
        """Test that save creates parent directories."""
        data = b"test"
        path = "deep/nested/path/file.txt"
        
        storage.save(data, path)
        
        assert storage.exists(path)

    def test_load_nonexistent_raises(self, storage):
        """Test that loading nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            storage.load("nonexistent.txt")

    def test_exists(self, storage):
        """Test exists method."""
        path = "test.txt"
        
        assert not storage.exists(path)
        storage.save(b"data", path)
        assert storage.exists(path)

    def test_delete(self, storage):
        """Test delete method."""
        path = "to_delete.txt"
        storage.save(b"data", path)
        
        assert storage.exists(path)
        result = storage.delete(path)
        assert result is True
        assert not storage.exists(path)

    def test_delete_nonexistent(self, storage):
        """Test deleting nonexistent file returns False."""
        result = storage.delete("nonexistent.txt")
        assert result is False

    def test_list(self, storage):
        """Test listing files."""
        storage.save(b"1", "dir1/file1.txt")
        storage.save(b"2", "dir1/file2.txt")
        storage.save(b"3", "dir2/file3.txt")
        
        all_files = list(storage.list())
        assert len(all_files) == 3
        
        dir1_files = list(storage.list("dir1"))
        assert len(dir1_files) == 2

    def test_get_metadata(self, storage):
        """Test getting file metadata."""
        data = b"test data"
        path = "meta_test.txt"
        storage.save(data, path)
        
        meta = storage.get_metadata(path)
        
        assert meta["size"] == len(data)
        assert "created" in meta
        assert "modified" in meta
        assert meta["is_dir"] is False

    def test_get_url(self, storage):
        """Test getting file URL."""
        path = "url_test.txt"
        storage.save(b"data", path)
        
        url = storage.get_url(path)
        
        assert url.startswith("file://")
        assert path in url


class TestStorageFactory:
    """Tests for storage factory function."""

    def test_get_local_storage(self, tmp_path):
        """Test creating local storage."""
        storage = get_storage(backend="local", local_path=str(tmp_path))
        assert isinstance(storage, LocalStorage)

    def test_get_nas_storage(self, tmp_path):
        """Test creating NAS storage (uses LocalStorage)."""
        storage = get_storage(backend="nas", nas_path=str(tmp_path))
        assert isinstance(storage, LocalStorage)

    def test_nas_without_path_raises(self):
        """Test that NAS without path raises ValueError."""
        with pytest.raises(ValueError, match="nas_path required"):
            get_storage(backend="nas")

    def test_s3_without_bucket_raises(self):
        """Test that S3 without bucket raises ValueError."""
        with pytest.raises(ValueError, match="s3_bucket required"):
            get_storage(backend="s3")

    def test_invalid_backend_raises(self):
        """Test that invalid backend raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported storage backend"):
            get_storage(backend="invalid")
