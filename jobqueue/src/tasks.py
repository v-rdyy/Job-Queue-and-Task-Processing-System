import time

def sleep_task(payload):
    seconds = payload["seconds"]
    time.sleep(seconds)
    return f"Slept for {seconds} seconds."

def sum_task(payload):
    total = sum(payload["numbers"])
    return f"Sum is {total}"

def fail_task(payload):
    raise Exception("This task always fails!")

TASKS = {
    "sleep": sleep_task,
    "sum": sum_task,
    "fail": fail_task
}

