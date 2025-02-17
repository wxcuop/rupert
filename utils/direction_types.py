# Define constants and types
INVALID_FILE_OFF = -1
INVALID_LENGTH = -1

# Define enums
class TriState:
    NO = 0
    YES = 1
    MAYBE = 2

def negate(tri_state):
    if tri_state == TriState.NO:
        return TriState.YES
    elif tri_state == TriState.YES:
        return TriState.NO
    return TriState.MAYBE

class Direction:
    UNKNOWN = 0
    INCOMING = 1
    OUTGOING = 2
    NEUTRAL = 3

direction_names = ["UNKNOWN", "INCOMING", "OUTGOING", "NEUTRAL"]

def direction_to_str(direction):
    try:
        return direction_names[direction]
    except IndexError:
        return "UNKNOWN"

CACHE_LINE_SIZE = 64
