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

def generate_monthly_bill(payload):
    required_fields = ["user_id", "billing_period", "subscription_plan", "base_price", "purchases"]
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"Missing required field: {field}")

    if not isinstance(payload["purchases"], list):
        raise ValueError("purchases must be a list")
    if not isinstance(payload["base_price"], (int, float)) or payload["base_price"] < 0:
        raise ValueError("base_price must be a non-negative number")

    purchases_total = 0.0
    for purchase in payload["purchases"]:
        if "price" not in purchase:
            raise ValueError("Each purchase must have a 'price' field")
        if not isinstance(purchase["price"], (int, float)) or purchase['price'] < 0:
            raise ValueError("Purchase price must be a non-negative number")
        purchases_total += purchase["price"]

    subscription_charge = payload["base_price"]
    total_charge = subscription_charge + purchases_total

    return {
        "user_id": payload["user_id"],
        "billing_period": payload["billing_period"],
        "subscription_plan": payload["subscription_plan"],
        "subscription_charge": subscription_charge,
        "purchases_total": round(purchases_total, 2),
        "total_charge": round(total_charge, 2)
    }

TASKS = {
    "sleep": sleep_task,
    "sum": sum_task,
    "fail": fail_task,
    "generate_monthly_bill": generate_monthly_bill
}