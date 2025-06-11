# app/server.py
"""
FastAPI application server.
Defines the API endpoints and application lifecycle events.
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

from . import persistence
from .generator import get_unique_random_number, NumberPoolExhaustedError

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
    This is the ideal place to initialize our database connection and tables.
    """
    persistence.init_db()


@app.get(
    "/random",
    tags=["Random Number"],
    summary="Get a unique random number",
    description="Returns a random integer that has never been returned before by this service.",
    response_description="A JSON object containing the unique number.",
)
def get_random_number():
    """
    Endpoint to retrieve a unique random number.

    It calls the core generator logic and handles potential errors,
    mapping them to appropriate HTTP responses.
    """
    try:
        unique_number = get_unique_random_number()
        return {"number": unique_number}
    except NumberPoolExhaustedError:
        # If the generator indicates that all numbers have been used,
        # return a 409 Conflict status code with a clear error message.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Number pool exhausted. No more unique numbers can be generated.",
        )
    except Exception as e:
        # Catch any other unexpected errors and return a generic 500 error.
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