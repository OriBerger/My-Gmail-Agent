# Fix Pub/Sub Push Configuration

## The Problem
The `gcloud pubsub subscriptions modify` command doesn't exist. We need to recreate the subscription with push configuration.

## Solution: Recreate Subscription with Push Endpoint

### Step 1: Delete existing subscription
```bash
gcloud pubsub subscriptions delete gmail-notifications-sub \
    --project=project-adccce59-2a50-4dce-87f
```

### Step 2: Create new push subscription
```bash
gcloud pubsub subscriptions create gmail-notifications-sub \
    --topic=gmail-notifications \
    --push-endpoint=https://my-gmail-agent.onrender.com/webhook/gmail \
    --project=project-adccce59-2a50-4dce-87f
```

### Step 3: Verify the subscription
```bash
gcloud pubsub subscriptions describe gmail-notifications-sub \
    --project=project-adccce59-2a50-4dce-87f
```

## Alternative: Use Google Cloud Console UI

1. Go to [Google Cloud Console - Pub/Sub](https://console.cloud.google.com/cloudpubsub/subscription)
2. Find `gmail-notifications-sub` subscription
3. Click on it
4. Click "EDIT" 
5. Change "Delivery type" from "Pull" to "Push"
6. Set "Endpoint URL" to: `https://my-gmail-agent.onrender.com/webhook/gmail`
7. Click "UPDATE"

## Verification

Test that the webhook receives data:
```bash
curl -X POST https://my-gmail-agent.onrender.com/webhook/gmail \
  -H "Content-Type: application/json" \
  -d '{"message":{"data":"eyJ0ZXN0IjoidGVzdCJ9","messageId":"test123"}}'
```

Should return: `{"status": "success", "message": "Webhook received"}`