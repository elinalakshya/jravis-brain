"""
security_guard_v2.py
Persistent approval version for JRAVIS / VA Bot.

Adds:
 - Disk persistence (approvals.jsonl)
 - Reload on startup
 - CLI-friendly list/approve/deny commands
"""

import os, json, time, uuid, threading, smtplib
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Tuple
from token_manager import get_token

# ---------------- Configuration ----------------
APPROVAL_FILE = os.getenv("APPROVAL_FILE", "approvals.jsonl")
AUDIT_FILE = os.getenv("AUDIT_LOG_FILE", "security_audit.log")
LOCK_CODE = os.getenv("SYSTEM_LOCK_CODE")
AUTO_RESUME = os.getenv("AUTO_RESUME_ENABLED",
                        "true").lower() in ("1", "true", "yes")
TIMEOUT = int(os.getenv("APPROVAL_TIMEOUT_SECONDS", "600"))

# Optional alert config
ALERT_EMAIL_FROM = os.getenv("ALERT_EMAIL_FROM")
ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO")
SMTP_SERVER = os.getenv("ALERT_SMTP_SERVER")
SMTP_PORT = int(os.getenv("ALERT_SMTP_PORT") or 587)
SMTP_USER = os.getenv("ALERT_SMTP_USER")
SMTP_PASS = os.getenv("ALERT_SMTP_PASS")


# ---------------- Utility helpers ----------------
def iso_now():
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(path: str, data: dict):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


def send_email_alert(subj: str, body: str):
    if not (SMTP_SERVER and ALERT_EMAIL_TO and SMTP_USER and SMTP_PASS): return
    try:
        s = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        msg = f"From:{ALERT_EMAIL_FROM}\r\nTo:{ALERT_EMAIL_TO}\r\nSubject:{subj}\r\n\r\n{body}"
        s.sendmail(ALERT_EMAIL_FROM, [ALERT_EMAIL_TO], msg)
        s.quit()
    except Exception as e:
        append_jsonl(AUDIT_FILE, {
            "t": iso_now(),
            "type": "alert_fail",
            "err": str(e)
        })


# ---------------- Persistent store ----------------
def load_approvals() -> Dict[str, dict]:
    data = {}
    if os.path.isfile(APPROVAL_FILE):
        with open(APPROVAL_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line.strip())
                    data[rec["id"]] = rec
                except:
                    pass
    return data


def save_approval(record: dict):
    append_jsonl(APPROVAL_FILE, record)


# ---------------- Core Class ----------------
class SecurityGuardV2:

    def __init__(self):
        self.pending = load_approvals()
        append_jsonl(AUDIT_FILE, {
            "t": iso_now(),
            "type": "startup",
            "loaded": len(self.pending)
        })

    # ---- Approval Management ----
    def request(self, desc: str, meta=None, amount=None, currency=None) -> str:
        aid = uuid.uuid4().hex
        rec = {
            "id": aid,
            "desc": desc,
            "meta": meta or {},
            "status": "pending",
            "amount": amount,
            "currency": currency,
            "created": time.time()
        }
        self.pending[aid] = rec
        save_approval(rec)
        append_jsonl(AUDIT_FILE, {
            "t": iso_now(),
            "type": "req",
            "id": aid,
            "desc": desc
        })
        send_email_alert("Approval requested", f"{desc}\nID:{aid}")
        # start auto-resume watcher
        threading.Thread(target=self._auto_watch, args=(aid, ),
                         daemon=True).start()
        return aid

    def _auto_watch(self, aid: str):
        time.sleep(TIMEOUT)
        rec = self.pending.get(aid)
        if rec and rec.get("status") == "pending" and AUTO_RESUME:
            rec["status"] = "auto_approved"
            rec["auto_at"] = time.time()
            save_approval(rec)
            append_jsonl(AUDIT_FILE, {
                "t": iso_now(),
                "type": "auto_approved",
                "id": aid
            })
            send_email_alert("Auto-approved",
                             f"ID {aid} auto-approved after timeout.")

    def approve(self, aid: str, approver="Boss", lock=None) -> bool:
        rec = self.pending.get(aid)
        if not rec: return False
        if LOCK_CODE and lock != LOCK_CODE: return False
        rec["status"] = "approved"
        rec["approver"] = approver
        rec["approved_at"] = time.time()
        save_approval(rec)
        append_jsonl(AUDIT_FILE, {
            "t": iso_now(),
            "type": "approved",
            "id": aid,
            "by": approver
        })
        send_email_alert("Approved", f"{aid} approved by {approver}")
        return True

    def deny(self, aid: str, approver="Boss", reason=None):
        rec = self.pending.get(aid)
        if not rec: return False
        rec["status"] = "denied"
        rec["reason"] = reason
        rec["denied_at"] = time.time()
        save_approval(rec)
        append_jsonl(AUDIT_FILE, {
            "t": iso_now(),
            "type": "denied",
            "id": aid
        })
        send_email_alert("Denied", f"{aid} denied: {reason}")
        return True

    def list_pending(self) -> Dict[str, dict]:
        return {
            k: v
            for k, v in self.pending.items() if v.get("status") == "pending"
        }

    # ---- Protected Execution ----
    def require_and_run(self,
                        fn: Callable,
                        args: Tuple[Any] = (),
                        kwargs: Dict[str, Any] = {},
                        desc: str = "",
                        meta=None,
                        amount=None,
                        currency=None,
                        wait=False) -> dict:
        aid = self.request(desc, meta, amount, currency)
        if wait:
            start = time.time()
            while time.time() - start < TIMEOUT:
                st = self.pending.get(aid, {}).get("status")
                if st in ("approved", "auto_approved"): break
                if st == "denied": return {"ok": False, "reason": "denied"}
                time.sleep(2)
        st = self.pending.get(aid, {}).get("status")
        if st in ("approved", "auto_approved"):
            try:
                res = fn(*args, **kwargs)
                append_jsonl(AUDIT_FILE, {
                    "t": iso_now(),
                    "type": "exec",
                    "id": aid,
                    "ok": True
                })
                return {"ok": True, "result": res, "id": aid}
            except Exception as e:
                append_jsonl(AUDIT_FILE, {
                    "t": iso_now(),
                    "type": "exec_err",
                    "id": aid,
                    "err": str(e)
                })
                return {"ok": False, "error": str(e)}
        return {"ok": False, "reason": "waiting", "id": aid}

    # ---- Decrypt PayPal creds ----
    def get_paypal_creds(self) -> Tuple[str, str]:
        return get_token("paypal_client_id"), get_token("paypal_secret")


# ---------------- CLI helper ----------------
if __name__ == "__main__":
    sg = SecurityGuardV2()
    import sys
    if len(sys.argv) == 1:
        print(
            "Usage:\n  list   -> show pending\n  approve <id> <code>\n  deny <id> <reason>"
        )
    elif sys.argv[1] == "list":
        print(json.dumps(sg.list_pending(), indent=2))
    elif sys.argv[1] == "approve" and len(sys.argv) >= 4:
        ok = sg.approve(sys.argv[2], "CLI", lock=sys.argv[3])
        print("approved" if ok else "failed")
    elif sys.argv[1] == "deny" and len(sys.argv) >= 4:
        sg.deny(sys.argv[2], "CLI", sys.argv[3])
        print("denied")
