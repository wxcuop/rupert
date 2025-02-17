import logging
from collections import defaultdict

class SymbolObserver:
    _symbol_observers = defaultdict(set)

    def __init__(self):
        self.symbol_set = set()
        self.key = id(self)
        SymbolObserver._symbol_observers[self.__class__].add(self)
        logging.debug("Adding Symbol observer")

    def __call__(self, sym):
        if sym in self.symbol_set:
            return  # send first time only
        self.symbol_set.add(sym)
        logging.debug(f"Inserting symbol = {sym}")
        self.symbol_added(sym)

    def symbol_added(self, sym):
        raise NotImplementedError("Derived classes must implement this method")

    def __del__(self):
        SymbolObserver._symbol_observers[self.__class__].discard(self)
        if not SymbolObserver._symbol_observers[self.__class__]:
            del SymbolObserver._symbol_observers[self.__class__]

# Example usage
class JDL_symbol_observer(SymbolObserver):
    def __init__(self):
        super().__init__()

    def symbol_added(self, sym):
        print(f"ID=1 symbol added {sym}")

# Example usage
if __name__ == "__main__":
    observer = JDL_symbol_observer()
    observer("AAPL")
    observer("GOOGL")
    observer("AAPL")  # Should not print again
