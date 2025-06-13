# app/server.py
"""
FastAPI application server.
Defines the API endpoints and application lifecycle events.
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI, HTTPException, status, Request

from . import persistence
from .generator import get_unique_random_number, NumberPoolExhaustedError

logger = logging.getLogger(__name__)

def setup_logging():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    log_handler = RotatingFileHandler(
        os.path.join(log_dir, "server.log"), maxBytes=5 * 1024 * 1024, backupCount=3
    )
    log_handler.setFormatter(log_formatter)

    root_logger = logging.getLogger()
    if not root_logger.handlers:
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(log_handler)

app = FastAPI(
    title="Unique Random Number Server (Sharded)",
    description="A scalable API to get a unique random number using a sharded PostgreSQL backend.",
    version="2.0.0",
)

@app.on_event("startup")
async def on_startup():
    """
    Application startup event handler.
    By making this an async function, FastAPI will wait for it to complete
    before it starts accepting requests.
    """
    setup_logging()
    logger.info("Application starting up...")
    await persistence.init_db()
    logger.info("Application startup complete.Ready to accept requests.")

@app.get(
    "/random",
    tags=["Random Number"],
    summary="Get a unique random number",
    response_description="A JSON object containing the unique number.",
)
def get_random_number(request: Request):
    logger.info("Received request for /random from client %s", request.client.host)
    try:
        unique_number = get_unique_random_number()
        logger.info("Successfully generated unique number: %d", unique_number)
        return {"number": unique_number}
    except NumberPoolExhaustedError as e:
        logger.warning("Number pool exhausted. Cannot generate a new number: %s", e)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error("An unexpected error occurred: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        )

@app.get("/health", tags=["Monitoring"], summary="Health Check")
def health_check():
    return {"status": "ok"}