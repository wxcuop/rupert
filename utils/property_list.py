from typing import Any, Dict, Set
from threading import Lock
import threading

class PropertyList:
    def __init__(self):
        self._properties: Dict[str, Any] = {}
        self._locks: Dict[str, Lock] = {}

    def register_property(self, name: str, value: Any):
        """Registers a property with a given name."""
        self._properties[name] = value
        self._locks[name] = Lock()

    def set_property(self, name: str, value: Any) -> bool:
        """Sets a property if it exists, returns True if successful, False otherwise."""
        if name not in self._properties:
            return False
        self._properties[name] = value
        return True

    def set_property_atomic(self, name: str, value: Any) -> bool:
        """Atomically sets a property if it exists, returns True if successful, False otherwise."""
        if name not in self._properties:
            return False
        with self._locks[name]:
            self._properties[name] = value
        return True

    def get_property(self, name: str) -> str:
        """Gets a property as a string. Returns an empty string if not found."""
        if name not in self._properties:
            return ""
        return str(self._properties[name])

    def get_properties(self) -> Set[str]:
        """Returns a set of all registered property names."""
        return set(self._properties.keys())
