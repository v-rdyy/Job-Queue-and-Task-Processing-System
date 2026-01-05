# Job Queue & Task Processing System

A production-ready backend job queue and task processing system built in Python. Features asynchronous job processing, retry logic, idempotent APIs, graceful shutdown, timeouts, and structured logging. Includes a real-world subscription billing workflow demonstration.

## Features

- **Asynchronous Processing**: Jobs processed in background worker threads
- **Thread-Safe**: All shared state protected with locks
- **Retry Logic**: Automatic retry with configurable max attempts
- **Idempotency**: Optional `client_job_id` prevents duplicate job submissions
- **Graceful Shutdown**: Workers finish current jobs before exiting
- **Timeouts**: Jobs can be killed if they exceed timeout limit
- **Structured Logging**: Professional logging with job context
- **REST API**: HTTP endpoints for job submission and status queries
- **Comprehensive Tests**: Unit tests covering success, retry, and failure scenarios

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

## Real-World Usage Example: Subscription Billing

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

**Example:**
```bash
# First submission
curl -X POST ... -d '{"task": "generate_monthly_bill", ..., "client_job_id": "billing-123"}'
# Returns: {"job_id": "abc", "status": "pending"}

# Duplicate submission (network retry, double-click, etc.)
curl -X POST ... -d '{"task": "generate_monthly_bill", ..., "client_job_id": "billing-123"}'
# Returns: {"job_id": "abc", "status": "success"}  # Same job, no duplicate!
```

## Available Tasks

- `sleep`: Sleep for N seconds
- `sum`: Sum an array of numbers
- `fail`: Always fails (for testing)
- `generate_monthly_bill`: Generate monthly subscription bill

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

## Load Testing

The system includes a load testing script to validate concurrency and throughput by submitting 200 to 1000 billing jobs concurrently and measuring completion time while varying the worker pool size.

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

Expected results:
- Higher throughput with more workers
- Lower average latency with more workers
- Same correctness (no missing jobs, all reach terminal states)

The load test reports:
- Total jobs submitted
- Success/failure counts
- Average and P95 latency
- Throughput (jobs per second)

## Architecture

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

