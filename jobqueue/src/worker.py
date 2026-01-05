import threading

import tasks

class Worker(threading.Thread):
    def __init__(self, job_queue, job_store, tasks):
        super().__init__()
        self.job_queue = job_queue
        self.job_store = job_store
        self.tasks = tasks

    def run(self):
        while True:
            job_id = self.job_queue.dequeue()
            job = self.job_store.get_job(job_id)

            self.job_store.update_job_status(job_id, "running")

            try:
                task_name = job["task_name"]
                task_func = self.tasks[task_name]

                payload = job["payload"]
                result = task_func(payload)

                self.job_store.update_job_status(job_id, "success", result=result)

            except Exception as e:
                error_message = str(e)

                self.job_store.increment_attempts(job_id)

                job = self.job_store.get_job(job_id)

                if job["attempts"] < job["max_retries"]:
                    self.job_store.update_job_status(job_id, "pending")
                    self.job_queue.enqueue(job_id)
                else:
                    self.job_store.update_job_status(job_id, "failed", error=error_message)
