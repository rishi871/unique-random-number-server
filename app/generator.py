# app/generator.py
"""
Core logic for generating a unique random number.
"""
import random

from . import persistence
from .config import MIN_NUMBER, MAX_NUMBER, TOTAL_NUMBERS_IN_POOL


class NumberPoolExhaustedError(Exception):
    """Custom exception for when no more unique numbers are available."""
    pass


def get_unique_random_number() -> int:
    """
    Generates a random number that has not been returned before.

    This function employs a generate-and-test strategy. It generates a random
    number and attempts to insert it into the database. The database's UNIQUE
    constraint ensures that duplicates are rejected. If an insert fails due to
    a duplicate, the function simply tries again with a new random number.

    This approach is efficient when the pool of used numbers is small compared
    to the total pool size.

    Raises:
        NumberPoolExhaustedError: If all possible numbers in the configured
                                   range have been used.

    Returns:
        A unique integer.
    """
    # 1. Check if the pool of available numbers is exhausted.
    used_count = persistence.get_used_count()
    if used_count >= TOTAL_NUMBERS_IN_POOL:
        raise NumberPoolExhaustedError("All available numbers have been used.")

    # 2. Loop until a unique number is successfully added to the database.
    while True:
        # Generate a candidate number.
        candidate = random.randint(MIN_NUMBER, MAX_NUMBER)

        # Attempt to "claim" the number by adding it to the database.
        # The add_used_number function will return True on success
        # and False on failure (due to a duplicate).
        if persistence.add_used_number(candidate):
            # If successful, we have found and claimed a unique number.
            return candidate
        # If not successful, the loop continues and we try again.
        # This handles race conditions where two concurrent requests generate
        # the same number. Only the first one to write to the DB will succeed.