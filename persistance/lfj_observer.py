from abc import ABC, abstractmethod

class LFJObserver(ABC):
    """
    Interface for subscribing to LFJ events
    """

    @abstractmethod
    def on_orderbook_update(self, pos):
        """
        Orderbook has been updated
        :param pos: Position of the orderbook data
        """
        pass

    @abstractmethod
    def on_vector_update(self, vec_num, idx):
        """
        Other vector has been updated (not orderbook)
        :param vec_num: Vector number that has been updated
        :param idx: Index in vector of new item
        """
        pass

    @abstractmethod
    def on_vector_created(self, vec):
        """
        A new vector has been created
        :param vec: Vector that has been created
        """
        pass

    @abstractmethod
    def on_stream_updated(self, size, char_ptr, another_size):
        """
        A stream has been updated
        """
        pass
