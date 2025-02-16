class ManyToOneMap:
    def __init__(self, config=None):
        """
        Initializes the mapping. Optionally loads from a configuration.
        :param config: A dictionary where keys map to comma-separated value strings.
        """
        self.map = {}
        if config:
            self.init(config)
    
    def init(self, config):
        """
        Load map from configuration, which is a dictionary where:
        - Keys map to comma-separated value strings (e.g., 'KEY1': 'VALUE1,VALUE2,VALUE3')
        """
        for key, values in config.items():
            for value in values.split(','):
                self.map[value.strip()] = key
    
    def get(self, value):
        """
        Lookup value. Assumes value exists, raises KeyError if not found.
        :param value: The value to lookup.
        :return: The corresponding key.
        """
        return self.map[value]
    
    def has_key(self, value):
        """
        Returns True if there is a mapping for this value.
        :param value: The value to check.
        :return: Boolean indicating existence.
        """
        return value in self.map
    
    def is_empty(self):
        """
        Checks if the map is empty.
        :return: True if empty, False otherwise.
        """
        return not bool(self.map)

# Example usage:
if __name__ == "__main__":
    config = {
        "KEY1": "VALUE1, VALUE2, VALUE3",
        "KEY2": "VALUE4, VALUE5"
    }
    
    mapping = ManyToOneMap(config)
    print(mapping.get("VALUE1"))  # Output: KEY1
    print(mapping.has_key("VALUE3"))  # Output: True
    print(mapping.is_empty())  # Output: False
