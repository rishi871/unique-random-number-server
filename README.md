# Unique Random Number Server

A production-ready, highly scalable HTTP server built with Python, FastAPI, and PostgreSQL. It serves unique random numbers and is designed for high-throughput, distributed environments.

The service guarantees that the same number will never be returned twice, even across server restarts and multiple running instances, by leveraging a sharded PostgreSQL backend.

## Features

-   **Guaranteed Uniqueness**: Every request to `/random` gets a new number that has never been seen before.
-   **Horizontal Scalability**: Built on a **sharded database architecture** to distribute write load, allowing the system to scale beyond a single database server.
-   **High Performance**: Built with FastAPI and Uvicorn for asynchronous, non-blocking I/O.
-   **Persistent & Resilient**: State is persisted in a robust PostgreSQL database cluster.
-   **Dynamic Configuration**: Uses Pydantic settings to manage configuration via environment variables or `.env` files, allowing easy deployment to any environment.
-   **Dockerized Environments**: Includes `docker-compose.yml` files for both development and isolated testing database clusters.
-   **Production-Ready Logging**: Implements rotating file-based logging for easy monitoring.
-   **Tested**: Includes a full integration test suite using `pytest` that runs against a real database cluster.

## Project Structure

The project follows a clean, modular structure to separate concerns.

```
unique-random-number-server/
├── README.md
├── requirements.txt
├── .gitignore
├── docker-compose.yml          # Defines the sharded database for local dev
├── docker-compose.test.yml     # Defines an isolated database cluster for testing
├── .env.example                # Template for environment variables
├── app/
│   ├── __init__.py
│   ├── server.py               # FastAPI app, routes, and startup logic
│   ├── generator.py            # Shard routing and number generation logic
│   ├── persistence.py          # Shard-aware database interaction layer
│   └── config.py               # Dynamic settings management via Pydantic
├── logs/                       # Log files are stored here (created automatically)
└── tests/
    └── test_random.py          # Integration tests for the API
```

## Setup and Installation

### Prerequisites

-   Python 3.10+
-   Docker and Docker Compose

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd unique-random-number-server
```

### 2. Configure Your Environment

The application is configured using environment variables. For local development, you can use a `.env` file.

Copy the example file to create your local configuration:
```bash
cp .env.example .env
```
The default values in this file are pre-configured to work with the local Docker Compose setup. No changes are needed to run locally.

### 3. Start the Database Backend

This command will start two separate PostgreSQL database containers for development.

```bash
docker-compose up -d
```
The databases will be accessible on your host machine at `localhost:5432` (shard 0) and `localhost:5433` (shard 1).

### 4. Set Up the Python Environment

Create and activate a virtual environment to keep dependencies isolated.

```bash
# Create the environment
python3 -m venv venv

# Activate it (macOS/Linux)
source venv/bin/activate

# Activate it (Windows)
.\venv\Scripts\activate
```

### 5. Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Running the Application

With the databases running via Docker and the Python environment set up, you can now start the web server.

```bash
uvicorn app.server:app --reload
```
The server will be running at `http://127.0.0.1:8000`.

### Stopping the Development Environment
To stop the application and the databases cleanly, first stop the Uvicorn server (`Ctrl+C`), then run:
```bash
docker-compose down
```

## Testing the Application

The project includes an integration test suite that runs against a real, containerized PostgreSQL database cluster, ensuring that tests are accurate and reliable. The test environment is completely isolated from the development environment.

### 1. Start the Test Databases

From the project's root directory, run the following command. This will start a dedicated set of PostgreSQL containers defined in `docker-compose.test.yml` on different ports (`5435`, `5436`).

```bash
docker-compose -f docker-compose.test.yml up -d
```

### 2. Run the Test Suite

Make sure your virtual environment is activated, then run `pytest`.

```bash
pytest
```

The test suite will automatically connect to the dedicated test databases. A fixture ensures that all database tables are cleared after each test function, guaranteeing test isolation.

### 3. Stop the Test Databases

Once you are finished testing, you can shut down the test database containers.

```bash
docker-compose -f docker-compose.test.yml down
```

## Usage

Send a GET request to the `/random` endpoint to receive a unique number.

### Using `curl`
```bash
curl http://127.0.0.1:8000/random
```
**Example Response:**
```json
{
  "number": 874109
}
```
You can also view the interactive API documentation (provided by FastAPI) by navigating to `http://127.0.0.1:8000/docs` in your browser.

## Configuration for Remote Databases

This application is designed to connect to any PostgreSQL database. To use a remote or managed database (e.g., AWS RDS, Google Cloud SQL), simply **do not use a `.env` file**. Instead, set the environment variables directly in your deployment environment.

**Example for a cloud deployment:**
```bash
# Set the environment variables before starting the application
export DB_SHARD_0_URL="postgresql+psycopg2://user:secret@prod-db-1.example.com:5432/numbers"
export DB_SHARD_1_URL="postgresql+psycopg2://user:secret@prod-db-2.example.com:5432/numbers"

# Run the server in production mode
uvicorn app.server:app --host 0.0.0.0 --port 8000
```

## Architectural Design and Scalability

The service is built on a **Range-Based Sharding** model to achieve horizontal scalability.

-   **Data Partitioning**: The total pool of numbers is divided into ranges. Each range is assigned to an independent PostgreSQL database instance, known as a "shard".
-   **Routing Logic**: When a request for a number is received, the application's generator randomly selects a shard and attempts to generate a unique number within that shard's assigned range.
-   **Benefits**:
    -   **Write Throughput**: The write load is distributed across multiple databases, dramatically increasing the number of concurrent requests the system can handle.
    -   **Fault Isolation**: If one database shard becomes unavailable, the other shards can continue to operate.