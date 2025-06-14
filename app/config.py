# app/config.py
"""
Configuration settings and constants for the application.
"""
#import os
# The connection string for the SQLite database.
# 'sqlite:///./numbers.db' means a file named 'numbers.db' in the root project directory.
#DATABASE_URL: str = "sqlite:///./numbers.db"

# The range for random number generation (inclusive).
# Using a large range minimizes the probability of collisions, making the
# generation process more efficient, especially in the beginning.
#MIN_NUMBER: int = 1
#MAX_NUMBER: int = 1_000_000

# The total pool of available numbers.
# Calculated once to avoid re-calculation.
#TOTAL_NUMBERS_IN_POOL: int = MAX_NUMBER - MIN_NUMBER + 1


# --- Sharding Configuration ---
# Define the database shards. Each key is a unique shard identifier.
# The value contains the connection string and the number range it manages.
# For security and flexibility, connection strings are read from environment variables
# with sensible defaults for local development using Docker Compose.

from pydantic_settings import BaseSettings, SettingsConfigDict

# --- Define the Settings Class ---
# Pydantic will automatically read variables from environment variables or a .env file.
# It's case-insensitive, so DB_SHARD_0_URL in the .env file maps to db_shard_0_url here.
class Settings(BaseSettings):
    # Load settings from a .env file if it exists.
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    # Define the required database URLs. Pydantic handles validation.
    # We provide defaults that match our local docker-compose setup.
    DB_SHARD_0_URL: str = "postgresql+psycopg2://user:password@localhost:5432/numbers_db"
    DB_SHARD_1_URL: str = "postgresql+psycopg2://user:password@localhost:5433/numbers_db"
    
    # Define the number range for each shard.
    # In a more advanced setup, this could also be part of the environment configuration.
    DB_SHARD_0_RANGE_START: int = 1
    DB_SHARD_0_RANGE_END: int = 500_000
    
    DB_SHARD_1_RANGE_START: int = 500_001
    DB_SHARD_1_RANGE_END: int = 1_000_000


# --- Create a single, importable instance of the settings ---
settings = Settings()


# --- Reconstruct the SHARDS dictionary for the rest of the app ---
# This structure is convenient for our persistence and generator layers,
# and by building it here, we minimize changes needed in other files.
SHARDS = {
    "shard_0": {
        "url": settings.DB_SHARD_0_URL,
        "range_start": settings.DB_SHARD_0_RANGE_START,
        "range_end": settings.DB_SHARD_0_RANGE_END,
    },
    "shard_1": {
        "url": settings.DB_SHARD_1_URL,
        "range_start": settings.DB_SHARD_1_RANGE_START,
        "range_end": settings.DB_SHARD_1_RANGE_END,
    },
}

# Also reconstruct the convenient helper variables
SHARD_NAMES = list(SHARDS.keys())
TOTAL_NUMBERS_IN_POOL = (
    (settings.DB_SHARD_0_RANGE_END - settings.DB_SHARD_0_RANGE_START + 1) +
    (settings.DB_SHARD_1_RANGE_END - settings.DB_SHARD_1_RANGE_START + 1)
)