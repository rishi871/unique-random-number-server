# Unique Random Number Server

A simple but robust HTTP server built with Python and FastAPI that serves unique random numbers. The service guarantees that the same number will never be returned twice, even across server restarts, by persisting used numbers in a local SQLite database.

## Features

- **Unique Numbers**: Every request to `/random` gets a new number that has never been seen before.
- **Persistent**: Used numbers are stored in an SQLite database, so state is maintained after restarts.
- **Asynchronous**: Built with FastAPI for high performance.
- **Robust**: Handles race conditions where two requests might generate the same number simultaneously.
- **Tested**: Includes a suite of unit tests using `pytest`.
- **Well-Structured**: The code is organized into logical modules for clarity and maintainability.

## Project Structure

```
unique-random-number-server/
├── README.md
├── requirements.txt
├── .gitignore
├── app/
│   ├── __init__.py
│   ├── server.py           # FastAPI app, routes, and lifespan logic
│   ├── generator.py        # Core logic for generating unique numbers
│   ├── persistence.py      # SQLite database interaction layer
│   └── config.py           # Application constants (e.g., DB path, number range)
└── tests/
    └── test_random.py      # Unit tests for the API
```

## Setup and Installation

This project is compatible with **Python 3.8+** (including 3.12).

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd unique-random-number-server
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # For Unix/macOS
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the Server

To start the web server, run the following command from the project's root directory:

```bash
uvicorn app.server:app --reload
```

-   `uvicorn`: The ASGI server that runs the application.
-   `app.server:app`: Points to the `app` instance inside the `app/server.py` file.
-   `--reload`: Automatically reloads the server when you make code changes (for development).

The server will be running at `http://127.0.0.1:8000`.

## Usage

You can get a unique random number by sending a GET request to the `/random` endpoint.

### Using `curl`

```bash
curl http://127.0.0.1:8000/random
```

**Example Response:**

```json
{
  "number": 483102
}
```

Each time you call it, a new, unique number will be returned. The first time you run the server, it will create a `numbers.db` file in the root directory to store state.

You can also check the interactive API documentation provided by FastAPI at `http://127.0.0.1:8000/docs`.



## Design and Scalability Discussion

### Current Design

The current implementation uses a "generate-and-test" approach, relying on the database's unique constraint.

1.  A random number is generated within a pre-defined range (`1` to `1,000,000`).
2.  The application attempts to `INSERT` this number into an SQLite table that has a `UNIQUE` constraint on the number column.
3.  If the `INSERT` succeeds, the number is returned.
4.  If the `INSERT` fails due to the `UNIQUE` constraint (meaning the number has already been used), the process repeats until a new, unused number is found and successfully inserted.

**Pros:**
- Simple to implement.
- Stateless at the application level; all state is in the database.
- Race-condition safe due to the atomic nature of database writes and constraints.

**Cons:**
- **Performance Degradation**: As the pool of used numbers grows, the probability of generating a "collision" (a number that's already been used) increases. This leads to more retries and higher latency per request.

