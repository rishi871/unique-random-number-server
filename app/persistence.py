# app/persistence.py
"""
Handles all database interactions for persisting used numbers using SQLAlchemy Core.
"""
import logging
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    select,
    func,
    UniqueConstraint,
)
from sqlalchemy.exc import IntegrityError

from .config import DATABASE_URL

# Set up logging
logger = logging.getLogger(__name__)

# SQLAlchemy engine and metadata setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
metadata = MetaData()

# Define the table for storing used numbers
used_numbers = Table(
    "used_numbers",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("number", Integer, nullable=False),
    # This constraint is crucial for preventing duplicate numbers at the DB level.
    UniqueConstraint("number", name="uq_number"),
)


def init_db() -> None:
    """
    Initializes the database and creates the 'used_numbers' table if it doesn't exist.
    This function is safe to call on every application startup.
    """
    logger.info("Initializing database...")
    metadata.create_all(engine)
    logger.info("Database initialized successfully.")


def add_used_number(number: int) -> bool:
    """
    Adds a number to the database of used numbers.

    This function attempts to insert the number. If the number is already present,
    the database's UNIQUE constraint will raise an IntegrityError, which we catch.
    This mechanism is the core of our race-condition-safe number generation.

    Args:
        number: The integer number to add.

    Returns:
        True if the number was added successfully, False if it was a duplicate.
    """
    try:
        with engine.connect() as connection:
            statement = used_numbers.insert().values(number=number)
            connection.execute(statement)
            connection.commit()
            return True
    except IntegrityError:
        # This occurs if another request added the same number between
        # generation and insertion. This is expected under high load.
        logger.warning("Attempted to insert duplicate number: %d", number)
        return False


def get_used_count() -> int:
    """
    Counts how many numbers have been used so far.

    Returns:
        The total count of numbers in the 'used_numbers' table.
    """
    with engine.connect() as connection:
        statement = select(func.count()).select_from(used_numbers)
        count = connection.execute(statement).scalar_one_or_none()
        return count or 0