# app/generator.py
"""
Core logic for generating a unique random number from a sharded data source.
"""
import random
import logging

from . import persistence
from .config import SHARDS, SHARD_NAMES, TOTAL_NUMBERS_IN_POOL

logger = logging.getLogger(__name__)

class NumberPoolExhaustedError(Exception):
    """Custom exception for when no more unique numbers are available."""
    pass


def get_unique_random_number() -> int:
    """
    Generates a unique random number by selecting a shard and then generating
    a number within that shard's defined range.
    """
    logger.debug("Starting number generation process.")
    if persistence.get_total_used_count() >= TOTAL_NUMBERS_IN_POOL:
        logger.warning("Number pool is exhausted based on count check.")
        raise NumberPoolExhaustedError("All available numbers have been used.")

    max_attempts = len(SHARD_NAMES) * 10
    for attempt in range(max_attempts):
        selected_shard_id = random.choice(SHARD_NAMES)
        shard_config = SHARDS[selected_shard_id]
        
        candidate = random.randint(
            shard_config["range_start"],
            shard_config["range_end"]
        )

        logger.debug(
            "Attempt %d: Trying number %d on shard %s",
            attempt + 1, candidate, selected_shard_id
        )

        if persistence.add_used_number(candidate, shard_id=selected_shard_id):
            logger.debug("Successfully claimed number %d.", candidate)
            return candidate
        else:
            # This new log is very useful for seeing why a loop is continuing
            logger.debug("Collision for number %d on shard %s. Retrying...", candidate, selected_shard_id)
            
    logger.error("Failed to generate a unique number after %d attempts.", max_attempts)
    raise NumberPoolExhaustedError("Could not find an available number slot after multiple attempts.")