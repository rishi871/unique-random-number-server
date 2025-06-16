# tests/test_random.py
"""
A simple and effective integration test suite for the sharded random number server.
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.sql import text
from app import generator

# --- CRITICAL: Set environment variables BEFORE importing the app ---
# This forces the app to use our test databases.
os.environ["DB_SHARD_0_URL"] = "postgresql+psycopg2://user:password@localhost:5435/numbers_db"
os.environ["DB_SHARD_1_URL"] = "postgresql+psycopg2://user:password@localhost:5436/numbers_db"

# Now, we can safely import the app and its components
from app.server import app
from app import config
from app.persistence import shard_engines, used_numbers_table

# --- The Simple, All-in-One Test Fixture ---

@pytest.fixture(scope="function")
def client():
    """
    A fixture that handles the entire test lifecycle simply:
    1. SETUP: Creates a new TestClient, which runs the app's `on_startup` event
       to create the database tables.
    2. YIELD: Passes the client to the test function to be used.
    3. TEARDOWN: Cleans the database tables after the test is complete.
    
    This runs fresh for every single test, guaranteeing perfect isolation.
    """
    # 1. SETUP: Instantiating the client runs the startup event.
    with TestClient(app) as test_client:
        # 2. YIELD: The test runs here.
        yield test_client

    # 3. TEARDOWN: This code runs after each test is finished.
    for engine in shard_engines.values():
        with engine.connect() as connection:
            # TRUNCATE is a fast way to delete all rows and reset the table.
            connection.execute(text(f"TRUNCATE TABLE {used_numbers_table.name} RESTART IDENTITY;"))
            connection.commit()

# --- Your Core Tests ---
# Each test now just needs to ask for the `client` fixture.

def test_health_check(client: TestClient):
    """Tests if the /health endpoint is working."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_random_number_success(client: TestClient):
    """Tests the successful retrieval of a random number."""
    response = client.get("/random")
    assert response.status_code == 200
    data = response.json()
    assert "number" in data
    assert isinstance(data["number"], int)


def test_get_multiple_unique_numbers(client: TestClient):
    """Tests that 10 consecutive calls return unique numbers."""
    number_of_calls = 10  # A smaller number for a faster test
    generated_numbers = set()

    for _ in range(number_of_calls):
        response = client.get("/random")
        assert response.status_code == 200
        number = response.json()["number"]
        assert number not in generated_numbers
        generated_numbers.add(number)

    assert len(generated_numbers) == number_of_calls


def test_pool_exhausted_error(client: TestClient, monkeypatch):
    """Tests that a 409 Conflict is returned when the pool is exhausted."""
    # Define a tiny shard configuration just for this test
    tiny_shards_config = {
        "shard_0": {
            "url": os.getenv("DB_SHARD_0_URL"),
            "range_start": 1,
            "range_end": 2, # Only two numbers possible
        }
    }
    tiny_shard_names = list(tiny_shards_config.keys())
    tiny_pool_size = 2
    
    # Patch the variables directly inside the 'generator' module
    monkeypatch.setattr(generator, "SHARDS", tiny_shards_config)
    monkeypatch.setattr(generator, "SHARD_NAMES", tiny_shard_names)
    monkeypatch.setattr(generator, "TOTAL_NUMBERS_IN_POOL", tiny_pool_size)
    
    # Generate the only two possible numbers
    assert client.get("/random").status_code == 200
    assert client.get("/random").status_code == 200

    # The next call should fail
    response = client.get("/random")
    assert response.status_code == 409
    
    # --- THE FIX ---
    # Update the assertion to match the actual error message returned by the pre-check.
    assert "All available numbers have been used." in response.json()["detail"]