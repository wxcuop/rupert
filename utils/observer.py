import weakref
from typing import Callable, Dict, Any

class ObserverContainer:
    """
    A generic observer container that allows adding, removing,
    and invoking observer functions (callbacks).
    """
    def __init__(self):
        self._observers: Dict[int, Callable[..., Any]] = {}
        self._id_counter = 0

    def add_observer(self, callback: Callable[..., Any]) -> int:
        """
        Register an observer function and return its unique ID.
        """
        self._id_counter += 1
        self._observers[self._id_counter] = weakref.WeakMethod(callback) if hasattr(callback, '__self__') else callback
        return self._id_counter

    def remove_observer(self, observer_id: int) -> None:
        """
        Remove an observer by its unique ID.
        """
        self._observers.pop(observer_id, None)

    def invoke_observers(self, *args, **kwargs) -> None:
        """
        Call all registered observer functions with provided arguments.
        """
        for observer in list(self._observers.values()):
            if isinstance(observer, weakref.WeakMethod):
                func = observer()
                if func is not None:
                    func(*args, **kwargs)
            else:
                observer(*args, **kwargs)

    def clear_observers(self) -> None:
        """
        Remove all observers.
        """
        self._observers.clear()

# Example usage
if __name__ == "__main__":
    def sample_observer(msg: str):
        print(f"Observer received: {msg}")
    
    container = ObserverContainer()
    obs_id = container.add_observer(sample_observer)
    container.invoke_observers("Hello, Observer Pattern!")
    container.remove_observer(obs_id)
