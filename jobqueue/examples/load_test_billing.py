import random
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

random.seed(42)

# Configuration constants
API_BASE = "http://localhost:5001"
N_JOBS = 1000
SUBMISSION_CONCURRENCY = 10
JOB_TIMEOUT = 5
MAX_RETRIES = 1
BILLING_PERIOD = "2026-01"
GLOBAL_DEADLINE = 60  # seconds

def generate_billing_payload(user_id, billing_period):
    plans = {
        "basic": 9.99,
        "prime": 14.99,
        "premium": 19.99
    }

    plan = random.choice(list(plans.keys()))
    base_price = plans[plan]

    num_purchases = random.randint(0,5)
    purchases = []
    for i in range(num_purchases):
        purchases.append({
            "item_id": f"item_{random.randint(100, 999)}",
            "price": round(random.uniform(2.99, 9.99), 2)
        })

    return {
        "user_id": user_id,
        "billing_period": billing_period,
        "subscription_plan": plan,
        "base_price": base_price,
        "purchases": purchases
    }

def submit_job(job_index, run_id):
    user_id = f"user_{job_index}"
    client_job_id = f"{run_id}:{user_id}:{BILLING_PERIOD}"

    payload = generate_billing_payload(user_id, BILLING_PERIOD)

    request_body = {
        "task": "generate_monthly_bill",
        "payload": payload,
        "client_job_id": client_job_id,
        "max_retries": MAX_RETRIES,
        "timeout": JOB_TIMEOUT
    }

    submit_time = time.time()
    response = requests.post(f"{API_BASE}/jobs", json=request_body)
    response.raise_for_status()

    result = response.json()
    return result["job_id"], submit_time

def submit_all_jobs(n_jobs, concurrency):
    run_id = f"loadtest_{int(time.time())}"
    job_data = []

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []
        for i in range(n_jobs):
            future = executor.submit(submit_job, i, run_id)
            futures.append(future)

        for future in as_completed(futures):
            try:
                job_id, submit_time = future.result()
                job_data.append((job_id,submit_time))
            except Exception as e:
                print(f"Submission error: {e}")
    
    return job_data

def get_job_status(job_id):
    response = requests.get(f"{API_BASE}/jobs/{job_id}")
    response.raise_for_status()
    return response.json()

def is_terminal(status):
    return status in ["success", "failed"]

def poll_until_complete(job_data, deadline):
    start_time = time.time()
    job_statuses = {}

    for job_id, submit_time in job_data:
        job_statuses[job_id] = {
            "status": "pending",
            "submit_time": submit_time,
            "completed_time": None
        }

    while time.time() - start_time < deadline:
        all_terminal = all(
            is_terminal(job_statuses[job_id]["status"])
            for job_id in job_statuses
        )
        if all_terminal:
            break
            
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {}
            for job_id, info in job_statuses.items():
                if not is_terminal(info["status"]):
                    future = executor.submit(get_job_status, job_id)
                    futures[future] = job_id

            for future in as_completed(futures):
                job_id = futures[future]
                try:
                    status_data = future.result()
                    current_status = status_data["status"]
                    job_statuses[job_id]["status"] = current_status

                    if is_terminal(current_status):
                        job_statuses[job_id]["completed_time"] = time.time()
                except Exception as e:
                    print(f"Polling error for {job_id}: {e}")
        
        time.sleep(0.3)
    
    return job_statuses

def compute_stats(job_statuses, wall_time):
    total_jobs = len(job_statuses)
    successes = sum(1 for info in job_statuses.values() if info["status"] == "success")
    failures = sum(1 for info in job_statuses.values() if info["status"] == "failed")

    latencies = []
    for job_id, info in job_statuses.items():
        if info["completed_time"] and info["submit_time"]:
            latency = info['completed_time'] - info["submit_time"]
            latencies.append(latency)

    avg_latency = sum(latencies) / len(latencies) if latencies else 0

    if latencies:
        sorted_latencies = sorted(latencies)
        p95_index = int(len(sorted_latencies) * 0.95)
        p95_latency = sorted_latencies[p95_index] if p95_index < len(sorted_latencies) else sorted_latencies[-1]
    else:
        p95_latency = 0

    throughput = total_jobs / wall_time if wall_time > 0 else 0

    return {
        "total_jobs": total_jobs,
        "successes": successes,
        "failures": failures,
        "avg_latency": avg_latency,
        "p95_latency": p95_latency,
        "throughput": throughput
    }
    
def print_summary(stats):
    """Print formatted summary statistics."""
    print("\n" + "=" * 60)
    print("LOAD TEST SUMMARY")
    print("=" * 60)
    print(f"Total Jobs:        {stats['total_jobs']}")
    print(f"Successes:         {stats['successes']}")
    print(f"Failures:          {stats['failures']}")
    print(f"Average Latency:   {stats['avg_latency']:.3f}s")
    print(f"P95 Latency:       {stats['p95_latency']:.3f}s")
    print(f"Throughput:        {stats['throughput']:.2f} jobs/sec")
    print("=" * 60)

def run_load_test(n_jobs, concurrency, deadline):
    print(f"\nStarting load test: {n_jobs} jobs, {concurrency} submission threads")
    print(f"Deadline: {deadline}s")

    submit_start = time.time()
    print("\nSubmitting jobs...")
    job_data = submit_all_jobs(n_jobs, concurrency)
    submit_time = time.time() - submit_start
    print(f"Submitted {len(job_data)} jobs in {submit_time:.2f}s")

    print("\nPolling for completion...")
    job_statuses = poll_until_complete(job_data, deadline)

    wall_time = time.time() - submit_start

    stats = compute_stats(job_statuses, wall_time)
    print_summary(stats)

    return stats

if __name__ == "__main__":
    run_load_test(N_JOBS, SUBMISSION_CONCURRENCY, GLOBAL_DEADLINE)