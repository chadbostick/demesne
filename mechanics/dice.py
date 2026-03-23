import random


def roll(sides: int = 20) -> int:
    """Roll a single die with the given number of sides."""
    return random.randint(1, sides)
