import requests
import time
import json
import os

API_BASE = "http://localhost:5001"

def load_billing_dataset():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(script_dir, "billing_dataset.json")
    
    with open(dataset_path, 'r') as f:
        data = json.load(f)
    
    return data

sample_billing_jobs = load_billing_dataset()

def submit_billing_job(user_data):
    client_job_id = f"billing-{user_data['user_id']}-{user_data['billing_period']}"
    
    payload = {
        "task": "generate_monthly_bill",
        "payload": user_data,
        "client_job_id": client_job_id,
        "max_retries": 3
    }
    
    response = requests.post(f"{API_BASE}/jobs", json=payload)
    return response.json()

def get_job_status(job_id):
    response = requests.get(f"{API_BASE}/jobs/{job_id}")
    return response.json()

def print_billing_summary(job_status):
    if job_status["status"] == "success":
        result = job_status["result"]
        print(f"\nBilling Summary for {result['user_id']}")
        print(f"   Period: {result['billing_period']}")
        print(f"   Plan: {result['subscription_plan']}")
        print(f"   Subscription: ${result['subscription_charge']:.2f}")
        print(f"   Purchases: ${result['purchases_total']:.2f}")
        print(f"   Total Charge: ${result['total_charge']:.2f}")
    else:
        print(f"\nJob {job_status['job_id']} failed: {job_status.get('error', 'Unknown error')}")

def main():
    print("=" * 60)
    print("Monthly Billing Job Processing Demo")
    print("=" * 60)
    
    print(f"\nSubmitting billing jobs for {len(sample_billing_jobs)} users...")
    job_ids = []
    
    for user_data in sample_billing_jobs:
        payload_data = {k: v for k, v in user_data.items() if k != "expected_total"}
        result = submit_billing_job(payload_data)
        job_id = result["job_id"]
        job_ids.append(job_id)
        print(f"   Submitted job for {user_data['user_id']}: {job_id}")
    
    print(f"\nWaiting for jobs to process...")
    time.sleep(2)
    
    print("\nBilling Results:")
    print("=" * 60)
    
    total_revenue = 0.0
    
    for job_id in job_ids:
        status = get_job_status(job_id)
        print_billing_summary(status)
        
        if status["status"] == "success":
            total_revenue += status["result"]["total_charge"]
    
    print("\n" + "=" * 60)
    print(f"Total Monthly Revenue: ${total_revenue:.2f}")
    print("=" * 60)
    
    print("\nTesting Idempotency:")
    first_user = {k: v for k, v in sample_billing_jobs[0].items() if k != "expected_total"}
    print("   Resubmitting job for user_001 with same client_job_id...")
    duplicate_result = submit_billing_job(first_user)
    print(f"   Returned job_id: {duplicate_result['job_id']}")
    print(f"   Original job_id: {job_ids[0]}")
    
    if duplicate_result['job_id'] == job_ids[0]:
        print("   Idempotency working! Same job returned (no duplicate billing)")
    else:
        print("   Different job created (idempotency failed)")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API server.")
        print("   Make sure the server is running: python main.py")
    except Exception as e:
        print(f"Error: {e}")

