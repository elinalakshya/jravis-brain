#!/usr/bin/env python3
"""
alerts.py (improved)
Tail a log file and email when keywords appear.

Main improvements over previous:
 - Suppress repeated "Skipping duplicate" console spam by printing only the first skip
   and a periodic suppressed-count summary per keyword.
 - Optional small grouping window (GROUP_WINDOW_SECS) to combine multiple keyword
   matches into a single short summary email if they occur within the window.
"""

import os, time, sys, smtplib, ssl, json, errno
from email.message import EmailMessage
from datetime import datetime, timezone, timedelta
from collections import deque, defaultdict

# --- Config from env ---
LOGFILE = os.getenv("LOGFILE", "va_daemon.log")
ALERT_KEYWORDS = [
    k.strip()
    for k in os.getenv("ALERT_KEYWORDS", "ERROR,EXCEPTION,CRITICAL").split(",")
    if k.strip()
]
ALERT_TO = [
    e.strip()
    for e in os.getenv("ALERT_TO", "nrveeresh327@gmail.com").split(",")
    if e.strip()
]
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
ALERT_FROM = os.getenv("ALERT_FROM", SMTP_USER or "va-bot@example.com")
SUBJECT_PREFIX = os.getenv("SUBJECT_PREFIX", "[VA ALERT]")
CONTEXT_LINES = int(os.getenv("CONTEXT_LINES", "6"))
DEDUP_COOLDOWN = int(os.getenv("DEDUP_COOLDOWN_SECS", "600"))
OFFSET_FILE = os.getenv("OFFSET_FILE", ".alerts.offset")
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "1.0"))
MAX_EMAIL_RETRIES = int(os.getenv("MAX_EMAIL_RETRIES", "5"))

# New: grouping window (seconds) to combine rapid matches into one email
GROUP_WINDOW_SECS = float(os.getenv("GROUP_WINDOW_SECS", "2.0"))

# How often to print suppressed counts (seconds)
SUPPRESSED_PRINT_INTERVAL = float(
    os.getenv("SUPPRESSED_PRINT_INTERVAL", "10.0"))

if not SMTP_USER or not SMTP_PASS:
    print("ERROR: SMTP_USER and SMTP_PASS environment variables must be set.",
          file=sys.stderr)
    sys.exit(2)


# --- small helpers ---
def read_offset():
    try:
        with open(OFFSET_FILE, "r") as f:
            data = f.read().strip()
            if not data:
                return 0
            return int(data)
    except FileNotFoundError:
        return 0
    except Exception:
        return 0


def write_offset(offset):
    try:
        with open(OFFSET_FILE + ".tmp", "w") as f:
            f.write(str(offset))
        os.replace(OFFSET_FILE + ".tmp", OFFSET_FILE)
    except Exception as e:
        print("Failed to write offset:", e, file=sys.stderr)


def send_email(subject, body, to_addrs):
    msg = EmailMessage()
    msg["From"] = ALERT_FROM
    msg["To"] = ", ".join(to_addrs)
    msg["Subject"] = subject
    msg.set_content(body)

    attempt = 0
    while attempt < MAX_EMAIL_RETRIES:
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_HOST,
                                  SMTP_PORT,
                                  context=context,
                                  timeout=20) as smtp:
                smtp.login(SMTP_USER, SMTP_PASS)
                smtp.send_message(msg)
            return True
        except Exception as e:
            attempt += 1
            sleep_for = min(60, 2**attempt)
            print(
                f"[{datetime.now().isoformat()}] Email send failed (attempt {attempt}): {e}. Retrying in {sleep_for}s",
                file=sys.stderr)
            time.sleep(sleep_for)
    print(
        f"[{datetime.now().isoformat()}] Giving up after {MAX_EMAIL_RETRIES} attempts to send email.",
        file=sys.stderr)
    return False


def mk_subject(multi=False, kw=None, first_line=""):
    ts = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    if multi:
        return f"{SUBJECT_PREFIX} Multiple alerts @ {ts}"
    else:
        return f"{SUBJECT_PREFIX} {kw} @ {ts}: {first_line[:120]}"


# --- main tail loop ---
def tail_and_alert():
    kw_lower = [k.lower() for k in ALERT_KEYWORDS]
    dedupe = defaultdict(lambda: datetime.min.replace(tzinfo=timezone.utc))
    context_buffer = deque(maxlen=CONTEXT_LINES + 20)

    # For suppressed logging: count suppressed alerts per keyword and last print time
    suppressed_counts = defaultdict(int)
    last_suppressed_print = defaultdict(lambda: datetime.min)

    last_offset = read_offset()

    # small grouping buffer for coalescing rapid matches
    group_buffer = []  # list of tuples (kw, matched_line, ts)
    last_group_flush = datetime.min

    # if file missing, wait until it exists
    while True:
        if os.path.exists(LOGFILE):
            break
        print(
            f"[{datetime.now().isoformat()}] Waiting for logfile {LOGFILE} to appear...",
            file=sys.stderr)
        time.sleep(2)

    with open(LOGFILE, "r", errors="replace") as f:
        f.seek(0, os.SEEK_END)
        file_size = f.tell()
        if last_offset <= file_size:
            f.seek(last_offset)
        else:
            f.seek(0, os.SEEK_END)

        print(
            f"[{datetime.now().isoformat()}] Monitoring {LOGFILE} from offset {f.tell()}",
            file=sys.stderr)

        while True:
            line = f.readline()
            if not line:
                # no new data
                try:
                    curr_offset = f.tell()
                    write_offset(curr_offset)
                except Exception:
                    pass

                # flush any grouped matches older than GROUP_WINDOW_SECS
                if group_buffer:
                    elapsed = (datetime.now(timezone.utc) -
                               last_group_flush).total_seconds()
                    if elapsed >= GROUP_WINDOW_SECS:
                        flush_group_buffer(group_buffer, context_buffer)
                        group_buffer.clear()

                # periodic suppressed summary prints
                now = datetime.now(timezone.utc)
                for kw, count in list(suppressed_counts.items()):
                    last_print = last_suppressed_print[kw]
                    if count > 0 and (now - last_print).total_seconds(
                    ) >= SUPPRESSED_PRINT_INTERVAL:
                        print(
                            f"[{datetime.now().isoformat()}] Suppressed {count} duplicate '{kw}' alerts in last {SUPPRESSED_PRINT_INTERVAL}s",
                            file=sys.stderr)
                        suppressed_counts[kw] = 0
                        last_suppressed_print[kw] = now

                time.sleep(POLL_INTERVAL)
                # handle rotation
                try:
                    if f.tell() > os.path.getsize(LOGFILE):
                        f.close()
                        f = open(LOGFILE, "r", errors="replace")
                        print(
                            f"[{datetime.now().isoformat()}] Log rotated/truncated, reopened file.",
                            file=sys.stderr)
                except Exception:
                    pass
                continue

            timestamped_line = line.rstrip("\n")
            context_buffer.append(timestamped_line)
            low = timestamped_line.lower()
            now = datetime.now(timezone.utc)

            matched_any = False
            for kw, kw_l in zip(ALERT_KEYWORDS, kw_lower):
                if kw_l in low:
                    matched_any = True
                    last_time = dedupe[kw]
                    if (now - last_time).total_seconds() < DEDUP_COOLDOWN:
                        # increment suppressed counter but don't spam console
                        suppressed_counts[kw] += 1
                        # print only first suppressed occurrence immediately
                        if suppressed_counts[kw] == 1:
                            print(
                                f"[{datetime.now().isoformat()}] Skipping duplicate alert for '{kw}' (cooldown). Suppressing further duplicates for now.",
                                file=sys.stderr)
                        continue

                    # eligible to alert: add to group buffer
                    group_buffer.append((kw, timestamped_line, now))
                    last_group_flush = now
                    # update dedupe timestamp to prevent repeated sends for same kw quickly
                    dedupe[kw] = now

            # if grouping buffer contains items older than GROUP_WINDOW_SECS, flush them now
            if group_buffer:
                elapsed = (datetime.now(timezone.utc) -
                           last_group_flush).total_seconds()
                if elapsed >= GROUP_WINDOW_SECS:
                    flush_group_buffer(group_buffer, context_buffer)
                    group_buffer.clear()

            # persist offset frequently
            try:
                write_offset(f.tell())
            except Exception:
                pass


def flush_group_buffer(group_buffer, context_buffer):
    """
    Create and send a combined email for the entries in group_buffer.
    group_buffer: list of (kw, line, ts)
    """
    if not group_buffer:
        return

    # Build an email body that groups by keyword
    by_kw = defaultdict(list)
    first_line = ""
    for kw, line, ts in group_buffer:
        by_kw[kw].append((ts, line))
        if not first_line:
            first_line = line

    multi = len(by_kw) > 1 or len(group_buffer) > 1
    subject = mk_subject(multi=multi,
                         kw=(list(by_kw.keys())[0] if not multi else None),
                         first_line=first_line)

    parts = []
    parts.append(f"Grouped alert summary ({len(group_buffer)} match(es))\n")
    for kw, entries in by_kw.items():
        parts.append(f"--- {kw} ({len(entries)} match(es)) ---")
        for ts, line in entries[-10:]:
            parts.append(f"{ts.isoformat()}  {line}")
        parts.append("")

    # include trailing context lines
    parts.append(f"Context (last {CONTEXT_LINES} lines):")
    parts.append("\n".join(list(context_buffer)[-CONTEXT_LINES:]))
    parts.append(f"\nLogfile: {LOGFILE}\nTime: {datetime.now().isoformat()}\n")

    body = "\n".join(parts)
    sent = send_email(subject, body, ALERT_TO)
    if sent:
        print(
            f"[{datetime.now().isoformat()}] Sent grouped alert ({len(group_buffer)} matches) to {ALERT_TO}",
            file=sys.stderr)
    else:
        print(f"[{datetime.now().isoformat()}] Failed to send grouped alert.",
              file=sys.stderr)


if __name__ == "__main__":
    try:
        tail_and_alert()
    except KeyboardInterrupt:
        print("alerts.py stopped by user.", file=sys.stderr)
    except Exception as e:
        print("alerts.py crashed:", e, file=sys.stderr)
        raise

# alerts.py (snippet)
WATCHED_PROCS = [
    "elina_instagram_reels_connector.py", "printify_pod_connector.py"
]


def check_procs():
    import psutil
    missing = []
    for pfile in WATCHED_PROCS:
        found = False
        for p in psutil.process_iter(['cmdline']):
            cmd = " ".join(p.info['cmdline'] or [])
            if pfile in cmd:
                found = True
                break
        if not found:
            missing.append(pfile)
    return missing


def restart_missing():
    missing = check_procs()
    for m in missing:
        # simple restart using nohup
        os.system(f"nohup python3 connectors/{m} > logs/{m}.log 2>&1 &")
        send_alert_email(f"Restarted missing process {m}")
