# email_templates.py — Phase 1 FINAL
from dataclasses import dataclass
from typing import Optional

BOSS_EMAIL = "nrveeresh327@gmail.com"  # per your spec


@dataclass
class SupportPayload:
    platform: str
    boss_email: str
    paypal_email: str
    sandbox_ok: bool = True
    webhook_url: Optional[str] = None


API_TEMPLATE = """
Subject: API access + PayPal linking request — {platform}

Hello {platform} Support Team,

We are setting up automated workflows for our Phase 1 launch. Please enable and share details for:

1) API Access
   • Client credentials (client_id / client_secret) or personal token process
   • API base URL(s) and rate limits
   • Webhook/event subscriptions (order created, payment received, fulfillment, disputes)

2) PayPal Linking (Payouts/Payments)
   • Connect our merchant account to receive payouts: {paypal_email}
   • Let us know if we must complete KYC/verification or add callback URLs.

3) Technical Notes
   • We can start in sandbox/test mode if available: {sandbox_note}
   {webhook_line}

Please confirm next steps and any required forms/screenshots. CC: {boss_email}

Thanks,
Dhruvayu
Automation Engineer
""".strip()


def render_api_email(payload: SupportPayload) -> str:
    webhook_line = f"• Webhook callback URL we plan to use: {payload.webhook_url}" if payload.webhook_url else ""
    sandbox_note = "Yes" if payload.sandbox_ok else "No"
    return API_TEMPLATE.format(
        platform=payload.platform,
        paypal_email=payload.paypal_email,
        sandbox_note=sandbox_note,
        webhook_line=webhook_line,
        boss_email=payload.boss_email,
    )


BOSS_SUMMARY_SUBJECT = "Phase 1 — Logins done + Support outreach queued"


def render_boss_summary(sent_rows):
    lines = ["Hi Boss,", "", "Quick update from Dhruvayu (VA Bot):", ""]
    for r in sent_rows:
        lines.append(
            f"• {r['platform']}: login={r['login']}, to={r['to']} → status={r['status']}"
        )
    lines += ["", "Screenshots are in /data/screens", "— Dhruvayu"]
    return "\n".join(lines)
