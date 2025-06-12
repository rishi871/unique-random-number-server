# app/server.py
"""
FastAPI application server.
Defines the API endpoints and application lifecycle events.
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import JSONResponse

from . import persistence
from .generator import get_unique_random_number, NumberPoolExhaustedError

# Get a logger for this module
logger = logging.getLogger(__name__)

def setup_logging():
    """
    Configures centralized logging for the application.

    - Creates a 'logs' directory if it doesn't exist.
    - Sets up a rotating file handler to save logs to 'logs/server.log'.
      This prevents the log file from growing indefinitely.
    - Defines a standard log format for consistency.
    """
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Configure the root logger
    log_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    log_handler = RotatingFileHandler(
        os.path.join(log_dir, "server.log"),
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
    )
    log_handler.setFormatter(log_formatter)

    # Set the root logger to handle all logs from the app
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(log_handler)

    logger.info("Logging configured successfully.")

# Create the FastAPI app instance
app = FastAPI(
    title="Unique Random Number Server",
    description="A simple API to get a unique random number that persists across restarts.",
    version="1.0.0",
)


@app.on_event("startup")
def on_startup():
    """
    Application startup event handler.
    This is the ideal place to initialize logging and the database.
    """
    setup_logging()
    logger.info("Application starting up...")
    persistence.init_db()
    logger.info("Application startup complete.")


@app.get(
    "/random",
    tags=["Random Number"],
    summary="Get a unique random number",
    description="Returns a random integer that has never been returned before by this service.",
    response_description="A JSON object containing the unique number.",
)
def get_random_number(request: Request):
    """
    Endpoint to retrieve a unique random number.

    It calls the core generator logic and handles potential errors,
    mapping them to appropriate HTTP responses.
    """
    logger.info("Received request for /random from client %s", request.client.host)
    try:
        unique_number = get_unique_random_number()
        logger.info("Successfully generated unique number: %d", unique_number)
        return {"number": unique_number}
    except NumberPoolExhaustedError as e:
        # If the generator indicates that all numbers have been used,
        # return a 409 Conflict status code with a clear error message.
        logger.warning("Number pool exhausted. Cannot generate a new number.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except Exception as e:
        # Catch any other unexpected errors and return a generic 500 error.
        logger.error("An unexpected error occurred: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        )

# Health check endpoint for monitoring
@app.get(
    "/health",
    tags=["Monitoring"],
    summary="Health Check",
    response_description="Server status",
)
def health_check():
    """A simple health check endpoint."""
    return {"status": "ok"}