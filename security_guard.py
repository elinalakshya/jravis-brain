"""
security_guard.py

Security guard for JRAVIS & VA Bot:
- Approval flow (manual + auto-resume)
- Audit logging (append-only)
- Alerts (SMTP or webhook)
- Key rotation helper (safe)
- Safe payout wrapper integration point

Usage:
    from security_guard import SecurityGuard

    sg = SecurityGuard()

    # protect an action (payout) with approval:
    sg.require_approval_and_execute(
        action_fn=payout_fn,
        action_args=(recipient_email, amount),
        action_kwargs={"currency":"USD"},
        description="Payout to vendor ABC for order #1234"
    )

Integrate with your existing payout_worker and token_manager.
"""

import os
import time
import uuid
import json
import smtplib
import threading
from datetime import datetime, timezone, timedelta
from typing import Callable, Any, Optional, Tuple, Dict

# import your token manager
from token_manager import get_token

# ---------- Configuration (tweakable via env) ----------
APPROVAL_TIMEOUT_SECONDS = int(os.getenv("APPROVAL_TIMEOUT_SECONDS",
                                         "600"))  # default 10 min
AUDIT_LOG_FILE = os.getenv("AUDIT_LOG_FILE", "security_audit.log")
ALERT_WEBHOOK = os.getenv("ALERT_WEBHOOK")  # optional: POST JSON alerts here
ALERT_EMAIL_FROM = os.getenv("ALERT_EMAIL_FROM")  # optional email alert sender
ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO")  # comma separated recipients
SMTP_SERVER = os.getenv("ALERT_SMTP_SERVER")
SMTP_PORT = int(os.getenv("ALERT_SMTP_PORT") or 587)
SMTP_USER = os.getenv("ALERT_SMTP_USER")
SMTP_PASS = os.getenv("ALERT_SMTP_PASS")
LOCK_CODE = os.getenv(
    "SYSTEM_LOCK_CODE") or None  # your master lock code (store securely!)
AUTO_RESUME_ENABLED = os.getenv("AUTO_RESUME_ENABLED",
                                "true").lower() in ("1", "true", "yes")


# ---------- Utilities ----------
def iso_now():
    return datetime.now(timezone.utc).isoformat()


def append_audit(entry: dict):
    """Append a JSON line to the audit log (append-only)."""
    entry_line = json.dumps(entry, ensure_ascii=False)
    with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry_line + "\n")


def send_alert(subject: str, body: str):
    """Send an alert: prefer webhook if configured, else fall back to SMTP email when available."""

    # non-blocking
    def _send():
        payload = {"time": iso_now(), "subject": subject, "body": body}
        # webhook if configured
        if ALERT_WEBHOOK:
            try:
                import requests
                requests.post(ALERT_WEBHOOK, json=payload, timeout=10)
            except Exception as e:
                # fallback to email below
                pass

        # fallback: SMTP if configured
        if SMTP_SERVER and SMTP_USER and SMTP_PASS and ALERT_EMAIL_TO:
            try:
                recipients = [
                    r.strip() for r in ALERT_EMAIL_TO.split(",") if r.strip()
                ]
                msg = f"From: {ALERT_EMAIL_FROM}\r\nTo: {', '.join(recipients)}\r\nSubject: {subject}\r\n\r\n{body}"
                s = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
                s.starttls()
                s.login(SMTP_USER, SMTP_PASS)
                s.sendmail(ALERT_EMAIL_FROM, recipients, msg)
                s.quit()
            except Exception as e:
                # last-resort: append to audit log
                append_audit({
                    "t": iso_now(),
                    "type": "alert_failure",
                    "error": str(e),
                    "subject": subject
                })

    threading.Thread(target=_send, daemon=True).start()


# ---------- SecurityGuard ----------
class SecurityGuard:

    def __init__(self):
        # simple in-memory pending approvals store (persist to file if you want)
        self.pending = {}  # id -> dict
        # ensure audit log exists
        if not os.path.exists(AUDIT_LOG_FILE):
            open(AUDIT_LOG_FILE, "a").close()

    # ---------- Approval flow ----------
    def request_approval(self,
                         description: str,
                         approve_callback_url: Optional[str] = None,
                         metadata: Optional[dict] = None,
                         amount: Optional[float] = None,
                         currency: Optional[str] = None) -> str:
        """
        Create an approval request and notify approver(s).
        Returns a unique approval_id.
        """
        approval_id = uuid.uuid4().hex
        created = time.time()
        entry = {
            "id": approval_id,
            "desc": description,
            "created": created,
            "status": "pending",
            "metadata": metadata or {},
            "amount": amount,
            "currency": currency,
        }
        self.pending[approval_id] = entry
        # audit
        append_audit({
            "t": iso_now(),
            "type": "approval_requested",
            "id": approval_id,
            "description": description,
            "amount": amount,
            "currency": currency
        })
        # send alert/notify
        subject = f"Approval requested: {description}"
        body = f"Approval ID: {approval_id}\nDescription: {description}\nAmount: {amount} {currency}\n\nTo approve: call the VA Bot or visit your admin endpoint.\nAuto-resume in {APPROVAL_TIMEOUT_SECONDS} seconds (if enabled)."
        send_alert(subject, body)
        return approval_id

    def approve(self,
                approval_id: str,
                approver_name: str = "unknown",
                lock_code: Optional[str] = None) -> bool:
        """Approve a pending request (must present lock_code if system configured)."""
        if approval_id not in self.pending:
            return False
        # if a lock code is configured, require it
        if LOCK_CODE:
            if not lock_code or lock_code != LOCK_CODE:
                append_audit({
                    "t": iso_now(),
                    "type": "approval_failed",
                    "id": approval_id,
                    "reason": "bad_lock_code",
                    "approver": approver_name
                })
                return False
        self.pending[approval_id]["status"] = "approved"
        self.pending[approval_id]["approved_by"] = approver_name
        self.pending[approval_id]["approved_at"] = time.time()
        append_audit({
            "t": iso_now(),
            "type": "approval_granted",
            "id": approval_id,
            "approver": approver_name
        })
        send_alert(
            f"Approval granted: {approval_id}",
            f"Approved by {approver_name} for {self.pending[approval_id]['desc']}"
        )
        return True

    def deny(self,
             approval_id: str,
             approver_name: str = "unknown",
             reason: Optional[str] = None):
        if approval_id not in self.pending:
            return False
        self.pending[approval_id]["status"] = "denied"
        self.pending[approval_id]["denied_by"] = approver_name
        self.pending[approval_id]["denied_at"] = time.time()
        self.pending[approval_id]["deny_reason"] = reason
        append_audit({
            "t": iso_now(),
            "type": "approval_denied",
            "id": approval_id,
            "approver": approver_name,
            "reason": reason
        })
        send_alert(f"Approval denied: {approval_id}",
                   f"Denied by {approver_name}. Reason: {reason}")
        return True

    def _auto_resume_watch(self, approval_id: str, action_fn: Callable,
                           action_args: Tuple[Any],
                           action_kwargs: Dict[str, Any], description: str):
        """Internal: wait APPROVAL_TIMEOUT_SECONDS, if still pending and auto-resume enabled, approve automatically."""
        time.sleep(APPROVAL_TIMEOUT_SECONDS)
        entry = self.pending.get(approval_id)
        if not entry:
            return
        if entry.get("status") == "pending" and AUTO_RESUME_ENABLED:
            # mark approved by system
            self.pending[approval_id]["status"] = "auto_approved"
            self.pending[approval_id]["approved_at"] = time.time()
            append_audit({
                "t": iso_now(),
                "type": "auto_approved",
                "id": approval_id,
                "description": description
            })
            send_alert(f"Auto-approved: {approval_id}",
                       f"Auto-approved after timeout for {description}")
            # execute action
            try:
                result = action_fn(*action_args, **action_kwargs)
                append_audit({
                    "t": iso_now(),
                    "type": "action_executed",
                    "id": approval_id,
                    "result": str(result)
                })
            except Exception as e:
                append_audit({
                    "t": iso_now(),
                    "type": "action_failed",
                    "id": approval_id,
                    "error": str(e)
                })
                send_alert(f"Action failed after auto-approve {approval_id}",
                           str(e))

    def require_approval_and_execute(self,
                                     action_fn: Callable,
                                     action_args: Tuple[Any] = (),
                                     action_kwargs: Dict[str, Any] = {},
                                     description: str = "",
                                     metadata: Optional[dict] = None,
                                     amount: Optional[float] = None,
                                     currency: Optional[str] = None,
                                     wait_for_approval: bool = False) -> dict:
        """
        Main public method:
        - creates approval request
        - notifies approver
        - can wait for manual approval or auto-resume after timeout
        - executes the action once approved
        Returns a dict with status/result
        """
        approval_id = self.request_approval(description=description,
                                            metadata=metadata,
                                            amount=amount,
                                            currency=currency)
        # start auto-resume watcher thread if enabled
        watcher_thread = threading.Thread(target=self._auto_resume_watch,
                                          args=(approval_id, action_fn,
                                                action_args, action_kwargs,
                                                description),
                                          daemon=True)
        watcher_thread.start()

        # optionally block until status changes (useful for synchronous flows)
        if wait_for_approval:
            start = time.time()
            while time.time() - start < (APPROVAL_TIMEOUT_SECONDS + 5):
                st = self.pending.get(approval_id, {}).get("status")
                if st and st in ("approved", "auto_approved"):
                    break
                if st == "denied":
                    return {"ok": False, "reason": "denied"}
                time.sleep(1)

        # if now approved, execute once (guard again)
        status = self.pending.get(approval_id, {}).get("status")
        if status in ("approved", "auto_approved"):
            try:
                result = action_fn(*action_args, **action_kwargs)
                append_audit({
                    "t": iso_now(),
                    "type": "action_executed",
                    "id": approval_id,
                    "description": description,
                    "result": str(result)
                })
                return {"ok": True, "id": approval_id, "result": result}
            except Exception as e:
                append_audit({
                    "t": iso_now(),
                    "type": "action_failed",
                    "id": approval_id,
                    "error": str(e)
                })
                send_alert(f"Action failed: {approval_id}", str(e))
                return {"ok": False, "error": str(e)}
        else:
            return {
                "ok": False,
                "reason": "not_approved_yet",
                "id": approval_id
            }

    # ---------- Key management helpers ----------
    def rotate_secret_key(self, new_key_bytes: bytes,
                          reencrypt_map: Dict[str, str]):
        """
        Replace secret.key safely.
        - new_key_bytes: raw bytes of new key
        - reencrypt_map: mapping of env var name -> plaintext value OR encrypted value? (we expect plaintext)
        Steps:
        1. Back up old secret.key to disk offsite (you must move it manually)
        2. Write new secret.key
        3. Re-encrypt tokens using token_manager.encrypt_token with new key (caller should re-run encryption commands)
        NOTE: This is a helper stub — prefer doing rotation manually with a verified process.
        """
        # audit
        append_audit({"t": iso_now(), "type": "rotation_started"})
        # write new key
        with open("secret.key", "wb") as f:
            f.write(new_key_bytes)
        append_audit({"t": iso_now(), "type": "rotation_written"})
        send_alert(
            "secret.key rotated",
            "secret.key has been replaced. Ensure you re-encrypt env tokens immediately."
        )
        return True

    # ---------- Helper: fetch paypal creds decrypted ----------
    def get_paypal_creds(self) -> Tuple[str, str]:
        """
        Return (client_id, secret) decrypted using token_manager.
        Expects environment to have PAYPAL_CLIENT_ID_ENC and PAYPAL_SECRET_ENC.
        """
        client_id = get_token(
            "paypal_client_id")  # expects PAYPAL_CLIENT_ID_ENC
        client_secret = get_token("paypal_secret")  # expects PAYPAL_SECRET_ENC
        return client_id, client_secret


# ---------- Example Integration: safe_payout wrapper ----------
def safe_payout_wrapper(security_guard: SecurityGuard,
                        payout_fn: Callable,
                        recipient_email: str,
                        amount: float,
                        currency: str = "USD",
                        note: str = ""):
    """
    Example: protects a payout function (payout_fn) which should accept (recipient, amount, currency, note)
    payout_fn can be your existing payout_worker.
    """
    description = f"Payout to {recipient_email} amount={amount} {currency}"
    # create a small metadata record
    metadata = {
        "recipient": recipient_email,
        "amount": amount,
        "currency": currency
    }
    return security_guard.require_approval_and_execute(
        action_fn=payout_fn,
        action_args=(recipient_email, amount),
        action_kwargs={
            "currency": currency,
            "note": note
        },
        description=description,
        metadata=metadata,
        amount=amount,
        currency=currency,
        wait_for_approval=False)


# ---------- End of module ----------
