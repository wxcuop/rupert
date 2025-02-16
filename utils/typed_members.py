from typing import Optional


class TypedMember:
    """Descriptor for a typed member with getter and setter."""

    def __init__(self, name, type_):
        self._name = f"_{name}"
        self._type = type_

    def __get__(self, instance, owner):
        return getattr(instance, self._name, None)

    def __set__(self, instance, value):
        if not isinstance(value, self._type):
            raise TypeError(f"Expected {self._type.__name__}, got {type(value).__name__}")
        setattr(instance, self._name, value)


class ReadOnlyTypedMember(TypedMember):
    """Read-only typed member descriptor."""

    def __set__(self, instance, value):
        raise AttributeError("Cannot modify a read-only attribute")


class BoolMember:
    """Descriptor for a boolean member with getter and setter."""

    def __init__(self, name):
        self._name = f"_{name}"

    def __get__(self, instance, owner):
        return getattr(instance, self._name, False)

    def __set__(self, instance, value):
        if not isinstance(value, bool):
            raise TypeError(f"Expected bool, got {type(value).__name__}")
        setattr(instance, self._name, value)


class ReadOnlyBoolMember(BoolMember):
    """Read-only boolean member descriptor."""

    def __set__(self, instance, value):
        raise AttributeError("Cannot modify a read-only attribute")


class ExampleClass:
    """Example usage of the typed member macros."""

    int_member = TypedMember("int_member", int)
    readonly_str = ReadOnlyTypedMember("readonly_str", str)
    is_active = BoolMember("is_active")

    def __init__(self, int_member: int, readonly_str: str, is_active: bool):
        self.int_member = int_member
        self._readonly_str = readonly_str  # Set directly to enforce read-only
        self.is_active = is_active


# Example usage
obj = ExampleClass(10, "test", True)
print(obj.int_member)  # 10
print(obj.is_active)  # True
print(obj.readonly_str)  # "test"

obj.int_member = 20  # Works fine
obj.is_active = False  # Works fine

try:
    obj.readonly_str = "new_value"  # Raises AttributeError
except AttributeError as e:
    print(e)
