from queue import Queue

class JobQueue:
    def __init__(self):
        self._queue = Queue()
    
    def enqueue(self, job_id):
        self._queue.put(job_id)

    def dequeue(self):
        return self._queue.get()