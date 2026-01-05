from flask import Flask, request, jsonify
from job_store import JobStore
from job_queue import JobQueue


job_store = None
job_queue = None

def init_api(store, queue):
    """Initialize API with shared instances."""
    global job_store, job_queue
    job_store = store
    job_queue = queue

app = Flask(__name__)

@app.route("/jobs", methods=['POST'])
def create_job():
    data = request.get_json()

    task = data.get("task")
    payload = data.get("payload", {})
    max_retries = data.get("max_retries", 3)

    if not task:
        return jsonify({"error": "task is required"}), 400

    job_id = job_store.create_job(task, payload, max_retries)
    job_queue.enqueue(job_id)

    return jsonify({"job_id": job_id, "status": "pending"}), 201

if __name__ == "__main__":
    app.run(debug=True, port=5000)

@app.route('/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    job = job_store.get_job(job_id)

    if job is None:
        return jsonify({"error": "Job not found"}), 404

    return jsonify({
        "job_id": job["job_id"],
        "status": job["status"],
        "task_name": job["task_name"],
        "attempts": job["attempts"],
        "max_retries": job["max_retries"],
        "result": job.get("result"),
        "error": job.get("error"),
        "created_at": str(job["created_at"]),
        "updated_at": str(job["updated_at"])
    }), 200