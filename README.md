# ParentConnect AI v2.2

## 1. Import the agent (Dialogflow ES)
Settings > Export and Import > Restore from ZIP > upload `ParentConnectAI_v2_Final.zip` (agent.json is at its root).

## 2. Run the webhook
    pip install -r requirements.txt
    gunicorn webhook:app --bind 0.0.0.0:$PORT
Deploy anywhere with HTTPS (Cloud Run, Render, Railway...). Check `/health`.
Then in Dialogflow: Fulfillment > Webhook > Enabled, URL = https://YOUR-HOST/webhook

## 3. Optional env vars
PC_REQUIRE_VERIFICATION=1   require "verify me" + PIN before personal records
PC_DEMO_PIN=1234            change this
PC_CONFIDENCE_GATE=0.7

## 4. Before going live
Replace TRANSFER_NUMBERS in webhook.py with the school's real numbers.
If you do NOT deploy the webhook, set webhookUsed to false on the 53 intents (or just use the Optimized zip) to avoid slow failed calls.
