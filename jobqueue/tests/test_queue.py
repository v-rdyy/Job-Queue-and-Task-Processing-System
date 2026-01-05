import unittest
import time
import sys
sys.path.insert(0, 'src')

from job_store import JobStore
from job_queue import JobQueue
from tasks import TASKS
from worker import Worker

class TestJobQueue(unittest.TestCase):
    def setUp(self):
        self.job_store = JobStore()
        self.job_queue = JobQueue()
        self.tasks = TASKS
        self.worker = Worker(self.job_queue, self.job_store, self.tasks)
        self.worker.start()
        time.sleep(0.1)

    def tearDown(self):
        self.worker.stop()
        dummy_job_id = self.job_store.create_job("sum", {"numbers": [0]})
        self.job_queue.enqueue(dummy_job_id)
        self.worker.join(timeout=2)

    def test_successful_job(self):
        job_id = self.job_store.create_job("sum", {"numbers": [1, 2, 3]})
        self.job_queue.enqueue(job_id)

        time.sleep(0.5)

        job = self.job_store.get_job(job_id)
        self.assertEqual(job["status"], "success")
        self.assertEqual(job["result"], "Sum is 6")
        self.assertEqual(job["attempts"], 0)

    def test_retry_logic(self):
        job_id = self.job_store.create_job("fail", {}, max_retries=3)
        self.job_queue.enqueue(job_id)

        time.sleep(2)

        job = self.job_store.get_job(job_id)
        self.assertGreater(job["attempts"], 0)
        self.assertEqual(job["attempts"], job["max_retries"])
        self.assertEqual(job["status"], "failed")
        self.assertIsNotNone(job["error"])

    def test_permanent_failure(self):
        job_id = self.job_store.create_job("fail", {}, max_retries=1)
        self.job_queue.enqueue(job_id)

        time.sleep(1)

        job = self.job_store.get_job(job_id)
        self.assertEqual(job["status"], "failed")
        self.assertEqual(job["attempts"], job["max_retries"])
        self.assertIsNotNone(job["error"])

if __name__ == "__main__":
    unittest.main()