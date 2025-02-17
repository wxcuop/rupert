import random
import itertools
import math

class UniqueGenerator:
    def __init__(self, n=5):
        self.n = n
        self.counter = itertools.cycle(range(1, int(math.pow(10, n + 1))))

    def rotating_counter(self):
        return next(self.counter)

# Global random number generator
rng = random.Random()
six = lambda: rng.randint(1, 999999)

# Example usage
generator = UniqueGenerator()
print(six())  # Random number between 1 and 999999
print(generator.rotating_counter())  # Incrementing counter with reset behavior
