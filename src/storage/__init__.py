# Storage abstraction module
from .interface import StorageInterface
from .local import LocalStorage
from .factory import get_storage

__all__ = ["StorageInterface", "LocalStorage", "get_storage"]
