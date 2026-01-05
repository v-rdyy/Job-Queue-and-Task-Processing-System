# Billing Examples

This directory contains sample datasets and demonstration scripts for the subscription billing workflow.

## Files

- `billing_dataset.json` - Sample billing data for 8 users
- `billing_examples.py` - Python script demonstrating billing job processing

## Quick Demo

1. Start the server:
```bash
cd jobqueue/src
python main.py
```

2. Run the demo script (in another terminal):
```bash
cd jobqueue/examples
python billing_examples.py
```

## Sample Dataset

The `billing_dataset.json` file contains 8 sample users with different subscription plans and purchase patterns:

- **user_001**: Prime plan with 3 purchases ($27.96 total)
- **user_002**: Basic plan with 1 purchase ($14.98 total)
- **user_003**: Premium plan, no purchases ($19.99 total)
- **user_004**: Prime plan with 4 purchases ($30.95 total)
- **user_005**: Basic plan, no purchases ($9.99 total)
- **user_006**: Prime plan with 2 purchases ($26.97 total)
- **user_007**: Premium plan with 1 purchase ($25.98 total)
- **user_008**: Basic plan with 2 purchases ($17.97 total)

**Total Monthly Revenue: $174.79**

## Manual API Examples

### Submit a billing job:

```bash
curl -X POST http://localhost:5001/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "task": "generate_monthly_bill",
    "payload": {
      "user_id": "user_001",
      "billing_period": "2026-01",
      "subscription_plan": "prime",
      "base_price": 14.99,
      "purchases": [
        {"item_id": "movie_001", "price": 3.99},
        {"item_id": "movie_002", "price": 5.99}
      ]
    },
    "client_job_id": "billing-user_001-2026-01"
  }'
```

### Check job status:

```bash
curl http://localhost:5001/jobs/{job_id}
```

### Expected result:

```json
{
  "user_id": "user_001",
  "billing_period": "2026-01",
  "subscription_plan": "prime",
  "subscription_charge": 14.99,
  "purchases_total": 9.98,
  "total_charge": 24.97
}
```

