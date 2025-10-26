# paypal_payout.py
"""
Secure PayPal payout module for JRAVIS using SecurityGuardV2
 - Creates persistent approval requests
 - Executes payouts only after approval
 - Logs every transaction
"""

import requests, json, uuid
from security_guard_v2 import SecurityGuardV2, iso_now  # import new guard

sg = SecurityGuardV2()


def payout_worker(recipient_email: str,
                  amount: float,
                  currency="USD",
                  note="Payout from JRAVIS"):
    """Actual PayPal Payouts API call (Sandbox first, Live later)."""
    client_id, client_secret = sg.get_paypal_creds()
    base = "https://api-m.paypal.com"
    # Use sandbox until tested, then switch to api-m.paypal.com

    # Get OAuth2 token
    r = requests.post(f"{base}/v1/oauth2/token",
                      auth=(client_id, client_secret),
                      data={"grant_type": "client_credentials"})
    r.raise_for_status()
    token = r.json()["access_token"]

    # Create payout
    payload = {
        "sender_batch_header": {
            "sender_batch_id": str(uuid.uuid4()),
            "email_subject": "You have a payout from JRAVIS"
        },
        "items": [{
            "recipient_type": "EMAIL",
            "amount": {
                "value": f"{amount:.2f}",
                "currency": currency
            },
            "receiver": recipient_email,
            "note": note
        }]
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    resp = requests.post(f"{base}/v1/payments/payouts",
                         headers=headers,
                         json=payload)

    # Log payout attempt
    entry = {
        "t": iso_now(),
        "recipient": recipient_email,
        "amount": amount,
        "currency": currency,
        "status_code": resp.status_code,
        "text": resp.text[:300]
    }
    with open("payout_log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    return {
        "ok": resp.status_code in (200, 201),
        "status": resp.status_code,
        "text": resp.text
    }


if __name__ == "__main__":
    # Create a secure approval-protected payout
    result = sg.require_and_run(fn=payout_worker,
                                args=("recipient@example.com", 5.00),
                                desc="Sandbox test payout",
                                amount=5.00,
                                currency="USD")
    print(result)
