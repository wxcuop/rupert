import ctypes
import weakref

class Plugin:
    """
    Manage access to a type derived from a shared library.
    The library must expose two C functions:
    - create(): creates an object and returns a pointer
    - destroy(ptr): destroys the pointer returned by create()
    """
    def __init__(self, library_name: str):
        self.library_name = library_name
        self._load_library()
    
    def _load_library(self):
        try:
            self.lib = ctypes.CDLL(self.library_name)
        except OSError as e:
            raise RuntimeError(f"Failed to open library: {e}")
        
        # Load constructor and destructor
        self.constructor = self._get_function("create", restype=ctypes.c_void_p)
        self.destructor = self._get_function("destroy", argtypes=[ctypes.c_void_p])
    
    def _get_function(self, name, restype=None, argtypes=None):
        try:
            func = getattr(self.lib, name)
            if restype:
                func.restype = restype
            if argtypes:
                func.argtypes = argtypes
            return func
        except AttributeError:
            raise RuntimeError(f"Could not load symbol '{name}'")
    
    def create(self):
        """Create an instance from the shared library and return a managed pointer."""
        ptr = self.constructor()
        if not ptr:
            raise RuntimeError("Failed to create instance from shared library")
        return self._wrap_pointer(ptr)
    
    def _wrap_pointer(self, ptr):
        """Wrap the pointer in a Python object with automatic cleanup."""
        obj = ctypes.c_void_p(ptr)
        weakref.finalize(obj, self.destructor, ptr)
        return obj
