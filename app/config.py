# app/config.py
"""
Configuration settings and constants for the application.
"""

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