# tests/test_random.py
"""
Unit tests for the FastAPI /random endpoint.
"""
import os
import pytest
from fastapi.testclient import TestClient

# We need to set an env var BEFORE importing the app to use a test database
os.environ["TESTING"] = "True"
from app.server import app
from app.config import MIN_NUMBER, MAX_NUMBER

# Create a test client
client = TestClient(app)

# Path to the test database file
TEST_DB_PATH = "./test.db"

# Fixture to clean up the test database before and after tests
@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Before each test, delete the test DB if it exists to ensure a clean state
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    
    yield  # This is where the test runs

    # After each test, clean up the test DB again
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    
    # Unset the env var
    if "TESTING" in os.environ:
        del os.environ["TESTING"]

# Override the database URL for testing
# This is a bit of a hacky way, but for this small app it's fine.
# A better way would be using FastAPI's dependency injection override.
from app import config
config.DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

def test_get_random_number_success():
    """Test that the /random endpoint returns a valid number."""
    response = client.get("/random")
    assert response.status_code == 200
    data = response.json()
    assert "number" in data
    assert isinstance(data["number"], int)
    assert MIN_NUMBER <= data["number"] <= MAX_NUMBER

def test_get_multiple_unique_numbers():
    """Test that multiple calls to /random return unique numbers."""
    # We will call the endpoint 100 times and store the results.
    # The number of calls should be small enough to not be flaky or slow.
    num_calls = 100
    generated_numbers = set()

    for _ in range(num_calls):
        response = client.get("/random")
        assert response.status_code == 200
        number = response.json()["number"]
        assert number not in generated_numbers
        generated_numbers.add(number)

    # The set should contain 100 unique numbers.
    assert len(generated_numbers) == 100

def test_pool_exhausted_error():
    """
    Test that the server returns a 409 Conflict when the pool is exhausted.
    To do this, we'll temporarily shrink the number pool.
    """
    # Temporarily override config for this specific test
    original_min = config.MIN_NUMBER
    original_max = config.MAX_NUMBER
    config.MIN_NUMBER = 1
    config.MAX_NUMBER = 3
    config.TOTAL_NUMBERS_IN_POOL = 3

    # Generate all possible numbers
    for _ in range(3):
        response = client.get("/random")
        assert response.status_code == 200

    # The next call should fail
    response = client.get("/random")
    assert response.status_code == 409
    assert response.json()["detail"] == "Number pool exhausted. No more unique numbers can be generated."

    # Restore original config values to not affect other tests
    config.MIN_NUMBER = original_min
    config.MAX_NUMBER = original_max
    config.TOTAL_NUMBERS_IN_POOL = original_max - original_min + 1

def test_health_check():
    """Test the /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}