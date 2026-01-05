from job_store import JobStore
from job_queue import JobQueue
from tasks import TASKS
from worker import Worker
from api import app, init_api

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
    print(f"Worker {i+1} started")

if __name__ == '__main__':
    print("✅ Starting API server on http://localhost:5001")
    print("   POST /jobs - Submit a job")
    print("   GET /jobs/<job_id> - Get job status")
    app.run(debug=True, port=5001, host='0.0.0.0')