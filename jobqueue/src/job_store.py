import threading
import uuid
from datetime import date, datetime

class JobStore:
    def __init__(self):
        self._jobs = {}
        self._lock = threading.Lock()

    def create_job(self, task_name, payload, max_retries=3):
        job_id = str(uuid.uuid4())
        now = datetime.now()

        job = {
            "job_id": job_id,
            "task_name": task_name,
            "payload": payload,
            "status": "pending",
            "attempts": 0,
            "max_retries": max_retries,
            "result": None,
            "error": None,
            "created_at": now,
            "updated_at": now
        }

        with self._lock:
            self._jobs[job_id] = job

        return job_id
    
    def get_job(self, job_id):
        with self._lock:
            return self._jobs.get(job_id)

    def update_job_status(self, job_id, status, result=None, error=None):
        with self._lock:
            job = self._jobs.get(job_id)
            if job is not None:
                job["status"] = status
                job["updated_at"] = datetime.now()
                if result is not None:
                    job["result"] = result
                if error is not None:
                    job["error"] = error
                return True
            else:
                return False
    
    def increment_attempts(self, job_id):
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return False
            job["attempts"] += 1
            job["updated_at"] = datetime.now()
        return True

        
        