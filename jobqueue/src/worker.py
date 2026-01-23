import threading
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

logger = logging.getLogger(__name__)


class Worker(threading.Thread):
    def __init__(self, job_queue, job_store, tasks):
        super().__init__()
        self.job_queue = job_queue
        self.job_store = job_store
        self.tasks = tasks
        self.running = True

    def run(self):
        while self.running:
            job_id = self.job_queue.dequeue()
            job = self.job_store.get_job(job_id)

            self.job_store.update_job_status(job_id, "running")
            logger.info(f"Job {job_id} started - task: {job['task_name']}")

            try:
                task_name = job["task_name"]
                task_func = self.tasks[task_name]

                payload = job["payload"]
                timeout = job.get("timeout")

                if timeout:
                    executor = ThreadPoolExecutor(max_workers=1)
                    future = executor.submit(task_func, payload)

                    try:
                        result = future.result(timeout=timeout)
                        executor.shutdown(wait=True)
                    except FutureTimeoutError:
                        executor.shutdown(wait=False)
                        raise TimeoutError(f"Job exceeded timeout of {timeout} seconds")
                else:
                    result = task_func(payload)

                self.job_store.update_job_status(job_id, "success", result=result)
                logger.info(f"Job {job_id} completed successfully - result: {result}")

            except Exception as e:
                error_message = str(e)

                self.job_store.increment_attempts(job_id)

                job = self.job_store.get_job(job_id)

                if job["attempts"] < job["max_retries"]:
                    self.job_store.update_job_status(job_id, "pending")
                    self.job_queue.enqueue(job_id)
                    logger.warning(f"Job {job_id} will be retried (attempt {job['attempts']}/{job['max_retries']})")
                else:
                    self.job_store.update_job_status(job_id, "failed", error=error_message)
                    logger.error(f"Job {job_id} permanently failed after {job['attempts']} attempts")

    def stop(self):
        self.running = False