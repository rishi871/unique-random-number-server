# app/config.py
"""
Configuration settings and constants for the application.
"""
import os
# The connection string for the SQLite database.
# 'sqlite:///./numbers.db' means a file named 'numbers.db' in the root project directory.
DATABASE_URL: str = "sqlite:///./numbers.db"

# The range for random number generation (inclusive).
# Using a large range minimizes the probability of collisions, making the
# generation process more efficient, especially in the beginning.
MIN_NUMBER: int = 1
MAX_NUMBER: int = 1_000_000

# The total pool of available numbers.
# Calculated once to avoid re-calculation.
TOTAL_NUMBERS_IN_POOL: int = MAX_NUMBER - MIN_NUMBER + 1


# --- Sharding Configuration ---
# Define the database shards. Each key is a unique shard identifier.
# The value contains the connection string and the number range it manages.
# For security and flexibility, connection strings are read from environment variables
# with sensible defaults for local development using Docker Compose.

SHARDS = {
    "shard_0": {
        "url": os.getenv("DB_SHARD_0_URL", "postgresql+psycopg2://user:password@localhost:5434/numbers_db"),
        "range_start": 1,
        "range_end": 500_000,
    },
    "shard_1": {
        "url": os.getenv("DB_SHARD_1_URL", "postgresql+psycopg2://user:password@localhost:5433/numbers_db"),
        "range_start": 500_001,
        "range_end": 1_000_000,
    },
}

# A simple list of shard names for easy iteration and random selection.
SHARD_NAMES = list(SHARDS.keys())