from typing import Callable, List
from exb.base import Resource, Status  # Assuming these exist or need to be implemented


class SymbolMktDataSubscribers:
    """Manages subscribers for market data updates."""
    
    def __init__(self):
        self._subscribers: List[Callable[[str], None]] = []

    def subscribe(self, callback: Callable[[str], None]) -> None:
        """Registers a callback function to be notified of updates."""
        self._subscribers.append(callback)

    def notify(self, symbol: str) -> None:
        """Notifies all subscribers of a symbol update."""
        for subscriber in self._subscribers:
            subscriber(symbol)


class MDSymbolObserverResource(Resource):
    """Market Data Symbol Observer Resource."""
    
    def __init__(self):
        super().__init__()
        self.symbol_observe_mgr = SymbolMktDataSubscribers()

    def get_symbol_mktdata_subscribers(self) -> SymbolMktDataSubscribers:
        return self.symbol_observe_mgr

    def on_load(self) -> Status:
        return super().on_load()

    def on_initialize(self) -> Status:
        return super().on_initialize()

    def on_start(self) -> Status:
        return Status.SUCCESS
