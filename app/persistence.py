# app/persistence.py
"""
Handles all sharded database interactions for persisting used numbers using SQLAlchemy Core.
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
from sqlalchemy.exc import IntegrityError, OperationalError

from .config import SHARDS

logger = logging.getLogger(__name__)

# --- Shard-Aware Engine Management ---
shard_engines = {
    shard_id: create_engine(config["url"])
    for shard_id, config in SHARDS.items()
}

metadata = MetaData()

used_numbers_table = Table(
    "used_numbers",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("number", Integer, nullable=False),
    UniqueConstraint("number", name="uq_number"),
)

async def init_db() -> None:
    """Initializes ALL configured database shards."""
    logger.info("Initializing all database shards...")
    for shard_id, engine in shard_engines.items():
        try:
            logger.info("Initializing shard: %s", shard_id)
            metadata.create_all(engine)
            logger.info("Shard %s initialized successfully.", shard_id)
        except OperationalError as e:
            logger.critical(
                "Failed to connect to shard %s. Check DB connection string and ensure it is running. Error: %s",
                shard_id, e
            )

def add_used_number(number: int, shard_id: str) -> bool:
    """Adds a number to a SPECIFIC database shard."""
    logger.debug("Attempting to INSERT number %d into used_numbers on shard %s", number, shard_id)
    try:
        engine = shard_engines[shard_id]
        with engine.connect() as connection:
            statement = used_numbers_table.insert().values(number=number)
            connection.execute(statement)
            connection.commit()
            return True
    except IntegrityError:
        logger.warning("Duplicate number %d on shard %s. This is expected under load.", number, shard_id)
        return False
    except KeyError:
        logger.error("Attempted to write to a non-existent shard: %s", shard_id)
        raise

def get_used_count_for_shard(shard_id: str) -> int:
    """Counts how many numbers have been used in a specific shard."""
    try:
        engine = shard_engines[shard_id]
        with engine.connect() as connection:
            statement = select(func.count()).select_from(used_numbers_table)
            count = connection.execute(statement).scalar_one_or_none()
            return count or 0
    except Exception as e:
        logger.error("Could not retrieve count from shard %s: %s", shard_id, e)
        return 0

def get_total_used_count() -> int:
    """Calculates the total number of used items by summing counts across all shards."""
    logger.debug("Calculating total used count across all shards.")
    total = 0
    for shard_id in SHARDS:
        total += get_used_count_for_shard(shard_id)
    logger.debug("Total used count is %d", total)
    return total