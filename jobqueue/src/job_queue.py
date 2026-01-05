from queue import Queue

class JobQueue:
    def __init__(self):
        self._queue = Queue()
    
    def enqueue(self, job):
        self._queue.put(job)

    def dequeue(self):
        return self._queue.get()