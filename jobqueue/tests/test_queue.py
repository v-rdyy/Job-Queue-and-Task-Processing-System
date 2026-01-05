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

    def test_successful_billing(self):
        payload = {
            "user_id": "user_123",
            "billing_period": "2026-01",
            "subscription_plan": "prime",
            "base_price": 14.99,
            "purchases": [
                {"item_id": "movie_001", "price": 3.99},
                {"item_id": "movie_002", "price": 5.99}
            ]
        }
        
        job_id = self.job_store.create_job("generate_monthly_bill", payload)
        self.job_queue.enqueue(job_id)
        
        time.sleep(0.5)
        
        job = self.job_store.get_job(job_id)
        self.assertEqual(job["status"], "success")
        
        result = job["result"]
        self.assertEqual(result["user_id"], "user_123")
        self.assertEqual(result["subscription_charge"], 14.99)
        self.assertEqual(result["purchases_total"], 9.98)
        self.assertEqual(result["total_charge"], 24.97)

    def test_billing_retry_on_invalid_payload(self):
        payload = {
            "user_id": "user_123",
            "billing_period": "2026-01"
        }
        
        job_id = self.job_store.create_job("generate_monthly_bill", payload, max_retries=2)
        self.job_queue.enqueue(job_id)
        
        time.sleep(1)
        
        job = self.job_store.get_job(job_id)
        self.assertGreater(job["attempts"], 0)
        self.assertIsNotNone(job["error"])

    def test_idempotent_billing_job(self):
        payload = {
            "user_id": "user_123",
            "billing_period": "2026-01",
            "subscription_plan": "prime",
            "base_price": 14.99,
            "purchases": []
        }
        
        client_job_id = "billing-user_123-2026-01"
        
        job_id1 = self.job_store.create_job("generate_monthly_bill", payload, client_job_id=client_job_id)
        self.job_queue.enqueue(job_id1)
        time.sleep(0.5)
        
        job_id2 = self.job_store.create_job("generate_monthly_bill", payload, client_job_id=client_job_id)
        
        self.assertEqual(job_id1, job_id2)
        
        job = self.job_store.get_job(job_id1)
        self.assertEqual(job["status"], "success")

if __name__ == "__main__":
    unittest.main()