from job_store import JobStore
from job_queue import JobQueue
from tasks import TASKS
from worker import Worker
from api import app, init_api
import logging
import signal
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

job_store = JobStore()
job_queue = JobQueue()
tasks = TASKS

init_api(job_store, job_queue)

NUM_WORKERS = 2

workers = []
for i in range(NUM_WORKERS):
    worker = Worker(job_queue, job_store, tasks)
    worker.start()
    workers.append(worker)
    logger.info(f"Worker {i+1} started")

def signal_handler(sig, frame):
    logger.info("Shutting down gracefully...")
    logger.info("Waiting for workers to finish current jobs...")

    for worker in workers:
        worker.stop()

    for worker in workers:
        worker.join(timeout=5)

    logger.info("All workers stopped. Exiting.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
    logger.info("Starting API server on http://localhost:5001")
    logger.info("POST /jobs - Submit a job")
    logger.info("GET /jobs/<job_id> - Get job status")
    app.run(debug=True, port=5001, host='0.0.0.0')