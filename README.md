# Unique Random Number Server

A production-ready, highly scalable HTTP server built with Python, FastAPI, and PostgreSQL. It serves unique random numbers and is designed for high-throughput, distributed environments.

The service guarantees that the same number will never be returned twice, even across server restarts and multiple running instances, by leveraging a sharded PostgreSQL backend.

## Features

-   **Guaranteed Uniqueness**: Every request to `/random` gets a new number that has never been seen before.
-   **Horizontal Scalability**: Built on a **sharded database architecture** to distribute write load, allowing the system to scale beyond a single database server.
-   **High Performance**: Built with FastAPI and Uvicorn for asynchronous, non-blocking I/O.
-   **Persistent & Resilient**: State is persisted in a robust PostgreSQL database cluster. The design is resilient to single-shard failures.
-   **Dynamic Configuration**: Uses Pydantic settings to manage configuration via environment variables or `.env` files, allowing easy deployment to any environment (local, staging, production) without code changes.
-   **Dockerized Development Environment**: Includes a `docker-compose.yml` file to instantly set up the complete sharded database backend locally.
-   **Production-Ready Logging**: Implements centralized, rotating file-based logging for easy monitoring and debugging.

## Project Structure

The project follows a clean, modular structure to separate concerns.

```
unique-random-number-server/
├── README.md
├── requirements.txt
├── .gitignore
├── docker-compose.yml    # Defines the sharded database for local dev
├── .env.example          # Template for environment variables
├── app/
│   ├── __init__.py
│   ├── server.py           # FastAPI app, routes, and startup logic
│   ├── generator.py        # Shard routing and number generation logic
│   ├── persistence.py      # Shard-aware database interaction layer
│   └── config.py           # Dynamic settings management via Pydantic
└── logs/                   # Log files are stored here (created automatically)
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

This command will start two separate PostgreSQL database containers, acting as our two shards.

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
The server will be running at `http://127.0.0.1:8000`. It will automatically connect to the Dockerized databases defined in your `.env` file.

### Stopping the Environment
To stop the application and the databases cleanly, first stop the Uvicorn server (`Ctrl+C`), then run:
```bash
docker-compose down
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

-   **Data Partitioning**: The total pool of numbers (e.g., 1 to 1,000,000) is divided into ranges. Each range is assigned to an independent PostgreSQL database instance, known as a "shard".
-   **Routing Logic**: When a request for a number is received, the application's generator randomly selects a shard. It then generates a random number *only within that shard's assigned range* and attempts to insert it.
-   **Benefits**:
    -   **Write Throughput**: The write load is distributed across multiple databases, dramatically increasing the number of concurrent requests the system can handle.
    -   **Fault Isolation**: If one database shard becomes unavailable, the other shards can continue to operate, making the system more resilient.
    -   **Smaller Indexes**: Each database manages a smaller dataset, which can lead to faster index lookups and inserts.
-   **Future Scaling**: To scale further, one would simply add a new shard configuration to `app/config.py` and deploy a new database instance. The application logic is designed to accommodate this seamlessly.