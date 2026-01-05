# Job Queue and Subscription Billing Processing System

A production-style backend job queue and task processing system built in Python. Features asynchronous job processing, retry logic, idempotent APIs, graceful shutdown, timeouts, and structured logging. Includes a real-world subscription billing workflow demonstration.

## Project Overview

This system demonstrates core backend engineering concepts: asynchronous job processing, thread-safe state management, failure handling, and system design. The architecture models how large platforms handle internal job processing workflows, with a concrete subscription billing use case.

**Key Components:**
- Thread-safe job store and queue
- Background worker pool for asynchronous processing
- REST API for job submission and status queries
- Automatic retry logic with configurable attempts
- Idempotent job submission (prevents duplicates)
- Graceful shutdown and timeout handling

## Architecture Overview

```
Client (HTTP)
    ↓
REST API (Flask)
    ↓
Job Store (Thread-safe State) ←→ Job Queue (FIFO)
    ↓                              ↓
Worker Pool (Background Threads)
    ↓
Task Registry
    ↓
Task Execution
```

**Component Responsibilities:**
- **JobStore**: Thread-safe in-memory storage for job state
- **JobQueue**: FIFO queue for pending jobs
- **Worker Pool**: Background threads that process jobs asynchronously
- **Task Registry**: Catalog of executable task functions
- **REST API**: HTTP interface for job submission and status queries

## Core Features

- **Asynchronous Processing**: Jobs processed in background worker threads
- **Thread-Safe**: All shared state protected with locks
- **Retry Logic**: Automatic retry with configurable max attempts
- **Idempotency**: Optional `client_job_id` prevents duplicate job submissions
- **Graceful Shutdown**: Workers finish current jobs before exiting
- **Timeouts**: Jobs can be killed if they exceed timeout limit
- **Structured Logging**: Professional logging with job context
- **REST API**: HTTP endpoints for job submission and status queries

## API Endpoints

### POST /jobs

Submit a new job for processing.

**Request:**
```json
{
  "task": "generate_monthly_bill",
  "payload": {
    "user_id": "user_123",
    "billing_period": "2026-01",
    "subscription_plan": "prime",
    "base_price": 14.99,
    "purchases": [
      {"item_id": "movie_001", "price": 3.99}
    ]
  },
  "max_retries": 3,
  "client_job_id": "billing-user_123-2026-01",
  "timeout": 30
}
```

**Response:**
```json
{
  "job_id": "abc-123-def",
  "status": "pending"
}
```

### GET /jobs/{job_id}

Get job status and results.

**Response:**
```json
{
  "job_id": "abc-123-def",
  "status": "success",
  "task_name": "generate_monthly_bill",
  "attempts": 1,
  "max_retries": 3,
  "result": {
    "user_id": "user_123",
    "billing_period": "2026-01",
    "subscription_plan": "prime",
    "subscription_charge": 14.99,
    "purchases_total": 3.99,
    "total_charge": 18.98
  },
  "error": null,
  "created_at": "2026-01-05 10:00:00",
  "updated_at": "2026-01-05 10:00:05"
}
```

## Real-World Workflow: Subscription Billing

This system models a real-world internal backend workflow used by large platforms for monthly subscription billing and usage aggregation.

### Billing Workflow

Each billing cycle, the system processes jobs that:
- Compute a user's monthly subscription charge
- Add any one-off purchases during the billing period
- Return a structured billing summary

This mirrors how large platforms handle billing internally:
- Jobs run asynchronously
- Failures are retried automatically
- Idempotency prevents double billing
- Timeouts protect system stability

### Example: Generate Monthly Bill

**Submit billing job:**
```bash
curl -X POST http://localhost:5001/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "task": "generate_monthly_bill",
    "payload": {
      "user_id": "user_123",
      "billing_period": "2026-01",
      "subscription_plan": "prime",
      "base_price": 14.99,
      "purchases": [
        {"item_id": "movie_001", "price": 3.99},
        {"item_id": "movie_002", "price": 5.99}
      ]
    },
    "client_job_id": "billing-user_123-2026-01",
    "max_retries": 3
  }'
```

**Result:**
```json
{
  "user_id": "user_123",
  "billing_period": "2026-01",
  "subscription_plan": "prime",
  "subscription_charge": 14.99,
  "purchases_total": 9.98,
  "total_charge": 24.97
}
```

### Why Retries and Idempotency Matter

**Retries:**
- Network issues during job submission
- Transient system errors
- Ensures billing jobs complete successfully

**Idempotency:**
- Prevents duplicate billing if same request sent twice
- Critical for financial operations
- Same `client_job_id` returns existing job result

## Load Testing and Validation

The system includes a load testing script to validate concurrency and worker scaling via local load testing.

### Running Load Tests

```bash
# Terminal 1: Start server (modify NUM_WORKERS in src/main.py to test different worker counts)
cd jobqueue/src
python main.py

# Terminal 2: Run load test
cd jobqueue/examples
python load_test_billing.py
```

### Configuration

Edit constants at the top of `load_test_billing.py`:
- `N_JOBS`: Number of jobs to submit (default: 200, try 1000)
- `SUBMISSION_CONCURRENCY`: Client threads submitting jobs (default: 10)
- `JOB_TIMEOUT`: Per-job timeout in seconds (default: 5)
- `MAX_RETRIES`: Retry attempts (default: 1)
- `GLOBAL_DEADLINE`: Maximum test duration (default: 60s)

### Validating Scaling

To validate worker scaling, run the same test 3 times with different worker counts in `src/main.py`:
- 1 worker
- 2 workers
- 4 workers

**Expected results:**
- Observed linear throughput improvements with increased worker count
- Lower average latency with more workers
- Same correctness (no missing jobs, all reach terminal states)

**Load test reports:**
- Total jobs submitted
- Success/failure counts
- Average and P95 latency
- Throughput (jobs per second)

**Note:** All load testing is performed locally. Results demonstrate system behavior under controlled conditions and validate concurrency patterns, not production capacity.

## Design Decisions and Trade-offs

### In-Memory Storage vs Database
- **Decision**: Dictionary-based in-memory storage
- **Why**: Simpler implementation, faster for learning, no external dependencies
- **Trade-off**: Jobs lost on restart (acceptable for this project's scope)

### Threading vs AsyncIO
- **Decision**: Use `threading.Thread` instead of `asyncio`
- **Why**: Simpler for learning, easier to understand, sufficient for this scale
- **Trade-off**: Thread overhead (acceptable for demonstration purposes)

### Single Queue vs Priority Queues
- **Decision**: Single FIFO queue
- **Why**: Simpler implementation, sufficient for core features
- **Trade-off**: No priority support (can be added later if needed)

### No Persistence by Design
- **Decision**: In-memory only, no database persistence
- **Why**: Focus on core job queue concepts, avoid complexity
- **Trade-off**: State not persisted across restarts (intentional for this project)

### No External Dependencies by Design
- **Decision**: No databases, message brokers, or external services
- **Why**: Pure Python implementation, easier to understand and deploy
- **Trade-off**: Limited scalability (acceptable for demonstration)

## Limitations and Future Work

**Current Limitations:**
- In-memory storage (jobs lost on restart)
- Single queue (no priority support)
- No distributed processing
- No job scheduling or cron logic
- No authentication or authorization

**Potential Future Enhancements:**
- Database persistence (PostgreSQL, Redis)
- Priority queues for job ordering
- Distributed worker pools
- Job scheduling and recurring tasks
- Authentication and API keys

**Note:** These limitations are intentional design choices to keep the project focused on core job queue concepts.

## Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```bash
# Start the server
cd jobqueue/src
python main.py
```

The API server will start on `http://localhost:5001`

## Testing

Run all tests:
```bash
cd jobqueue
python3 -m unittest tests.test_queue
```

Or run directly:
```bash
python3 tests/test_queue.py
```

Tests cover:
- Successful job execution
- Retry logic on failures
- Permanent failure after max retries
- Successful billing generation
- Billing retry on invalid payload
- Idempotent billing job submission

## Project Structure

```
jobqueue/
├── src/
│   ├── job_store.py      # Thread-safe job state management
│   ├── job_queue.py      # Thread-safe queue wrapper
│   ├── tasks.py          # Task registry (including billing)
│   ├── worker.py         # Worker thread logic
│   ├── api.py            # REST API endpoints
│   └── main.py           # Application bootstrap
├── tests/
│   └── test_queue.py     # Unit tests
├── examples/
│   ├── billing_examples.py    # Billing workflow demo script
│   ├── billing_dataset.json   # Sample billing data (8 users)
│   └── load_test_billing.py   # Load testing script
└── requirements.txt      # Dependencies
```

## License

MIT
