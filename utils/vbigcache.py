import logging
from typing import Dict, Type, TypeVar, Generic, Optional

T = TypeVar("T")


class VBigCache(Generic[T]):
    """
    A simple, type-safe cache that allows storing multiple distinct data types
    for a given string key.

    Each key in the cache holds a dictionary that maps types to their values.
    """

    def __init__(self, name: str):
        self.name = name
        self.cache: Dict[str, Dict[Type, object]] = {}

    def get_entry(self, key: str) -> Optional[Dict[Type, object]]:
        """
        Looks up an entry in the cache.

        :param key: The key to look up.
        :return: The dictionary containing type-based values or None if not found.
        """
        logging.debug(f"L@@KUP key: {key}")
        return self.cache.get(key)

    def get_or_create_entry(self, key: str) -> Dict[Type, object]:
        """
        Gets or creates an entry for a given key.

        :param key: The key for the cache entry.
        :return: The dictionary that stores type-based values.
        """
        if key not in self.cache:
            logging.debug(f"VBigCache Create-Entry *** for key: {key}")
            self.cache[key] = {}
        else:
            logging.debug(f"VBigCache Hit! for key: {key}")
        return self.cache[key]

    def get_value(self, key: str, type_: Type[T]) -> Optional[T]:
        """
        Retrieves a value of a specific type from the cache.

        :param key: The key associated with the cache entry.
        :param type_: The expected type of the value.
        :return: The value if found, else None.
        """
        entry = self.get_entry(key)
        if entry is None or type_ not in entry:
            logging.debug(f"VBigCache Value Not found *** for type: {type_.__name__}")
            return None

        logging.debug(f"VBigCache Value Found for type: {type_.__name__}")
        return entry[type_]

    def set_value(self, key: str, type_: Type[T], value: T) -> Optional[T]:
        """
        Sets a new value for a given type within an entry.

        :param key: The key associated with the cache entry.
        :param type_: The type of the value being stored.
        :param value: The value to store.
        :return: The previous value if it existed, otherwise None.
        """
        entry = self.get_or_create_entry(key)
        old_value = entry.get(type_)
        entry[type_] = value

        logging.debug(f"VBigCache Value Set *** for type: {type_.__name__}")
        return old_value

    def __repr__(self):
        return f"VBigCache(name={self.name}, size={len(self.cache)})"


# Example Usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    # Define example classes
    class PositionEntry:
        pass

    class MarketDataEntry:
        pass

    # Create cache instance
    vbig_cache = VBigCache("JISU_VBIG_CACHE")

    # Use the cache
    entry_key = "client:account:symbol"
    new_entry = PositionEntry()

    old_value = vbig_cache.set_value(entry_key, PositionEntry, new_entry)
    retrieved_value = vbig_cache.get_value(entry_key, PositionEntry)

    print("Old Value:", old_value)
    print("Retrieved Value:", retrieved_value)
