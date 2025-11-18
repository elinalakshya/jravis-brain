import yaml
import time
from datetime import datetime, date

from va_bot import VAInterface

with open("config/phase_automation.yaml") as f:
    config = yaml.safe_load(f)

va_bot = VAInterface(config["settings"]["payout_method_default"])

STATE = {
    "current_phase": "phase1",  # "phase1" → "phase2" → "phase3"
    "activated_streams": [],  # list of all activated stream IDs across phases
    "phase_stabilization_start":
    None,  # date when stabilization started for current phase
}


def log(msg):
    print(f"[JRAVIS] {datetime.now().isoformat()} :: {msg}")


def get_phase_obj():
    return config["phases"][STATE["current_phase"]]


def get_phase_streams(phase_key=None):
    if not phase_key:
        phase_key = STATE["current_phase"]
    return config["phases"][phase_key]["streams"]


def get_phase_stream_ids(phase_key=None):
    return [s["id"] for s in get_phase_streams(phase_key)]


def get_phase_activated_ids():
    phase_ids = set(get_phase_stream_ids())
    return [sid for sid in STATE["activated_streams"] if sid in phase_ids]


def all_streams_activated_for_phase():
    return len(get_phase_activated_ids()) == len(get_phase_stream_ids())


def stabilization_days_elapsed():
    if not STATE["phase_stabilization_start"]:
        return 0
    return (date.today() - STATE["phase_stabilization_start"]).days


def advance_phase_if_ready():
    """Move from phase1 → phase2 → phase3 after 10 days of stabilization."""
    if not all_streams_activated_for_phase():
        return  # can’t move if activation not finished

    if stabilization_days_elapsed() < 10:
        return  # still stabilizing

    # Move to next phase
    old_phase = STATE["current_phase"]
    if old_phase == "phase1":
        STATE["current_phase"] = "phase2"
    elif old_phase == "phase2":
        STATE["current_phase"] = "phase3"
    else:
        log("✅ All phases completed. No further phase to advance.")
        return

    STATE["phase_stabilization_start"] = None
    log(f"🚀 Phase shifted: {old_phase} → {STATE['current_phase']} (activation mode)"
        )


def auto_solve_issue(stream, issue_description):
    try:
        solution_summary = va_bot.solve_issue(stream["platform"],
                                              issue_description)
        log(f"🛠 Auto-solved issue for stream {stream['id']}: {issue_description} → {solution_summary}"
            )
        va_bot.log_issue(stream["id"], issue_description, solution_summary)
        return solution_summary
    except Exception as e:
        msg = f"❌ Failed auto-solve for stream {stream['id']}: {issue_description} | error={str(e)}"
        log(msg)
        va_bot.log_issue(stream["id"], issue_description, msg)
        return msg


def activate_next_stream_if_needed():
    """
    Called once per day at activation time.
    1) If there are unactivated streams in this phase → activate ONE.
    2) If all are activated → start/continue 10-day stabilization (no new streams).
    3) After 10 days of stabilization → advance to next phase.
    """
    phase = get_phase_obj()
    phase_streams = phase["streams"]
    phase_ids = get_phase_stream_ids()
    active_ids = get_phase_activated_ids()

    # 1) ACTIVATION MODE – still have streams to turn on
    for stream in phase_streams:
        if stream["id"] not in STATE["activated_streams"]:
            log(f"🔄 Activating new stream in {STATE['current_phase']}: {stream['name']} (ID={stream['id']})"
                )
            try:
                va_bot.run_setup_tasks(stream["tasks"]["setup"])
                STATE["activated_streams"].append(stream["id"])
                log(f"🎉 Stream activated: {stream['name']} (ID={stream['id']})"
                    )
            except Exception as e:
                issue_msg = f"Activation failed: {str(e)}"
                auto_solve_issue(stream, issue_msg)
            return  # only one activation per day

    # 2) STABILIZATION MODE – all streams in this phase are activated
    if all_streams_activated_for_phase():
        if STATE["phase_stabilization_start"] is None:
            STATE["phase_stabilization_start"] = date.today()
            log(f"🧪 Stabilization started for {STATE['current_phase']} on {STATE['phase_stabilization_start']}"
                )
        else:
            log(f"🧪 Stabilizing {STATE['current_phase']} – day {stabilization_days_elapsed()+1}/10"
                )

        # Run stabilization checks daily during this period
        run_stabilization_checks_current_phase()

        # Check if we can move to next phase after 10 days
        advance_phase_if_ready()


def run_daily_tasks_all_streams():
    """VA Bot runs income-generating tasks for ALL activated streams (across all phases)."""
    if not STATE["activated_streams"]:
        log("ℹ No activated streams yet. Skipping daily tasks.")
        return

    for phase_key in ["phase1", "phase2", "phase3"]:
        for stream in get_phase_streams(phase_key):
            if stream["id"] not in STATE["activated_streams"]:
                continue
            try:
                va_bot.run_daily_tasks(stream["id"], stream["tasks"]["daily"])
            except Exception as e:
                issue_msg = f"Daily task error: {str(e)}"
                auto_solve_issue(stream, issue_msg)


def run_stabilization_checks_current_phase():
    """Deep check for each stream in current phase: errors, broken flows, low income, etc."""
    phase = get_phase_obj()
    for stream in phase["streams"]:
        if stream["id"] not in STATE["activated_streams"]:
            continue
        try:
            issues_found = va_bot.run_stabilization_checks(
                stream["id"], stream.get("issues", []))
            for issue in issues_found:
                auto_solve_issue(stream, issue)
        except Exception as e:
            auto_solve_issue(stream, f"Stabilization error: {str(e)}")


def send_daily_report():
    report_data = va_bot.collect_daily_metrics(STATE["activated_streams"])
    va_bot.send_report(report_data, config["settings"]["report_email"])
    log("📨 Daily report sent to Boss.")


def send_weekly_report():
    va_bot.generate_weekly_report()
    log("📨 Weekly report generated & sent to Boss.")


def tick_scheduler():
    now = datetime.now()
    now_time = now.strftime("%H:%M")
    weekday = now.strftime("%A")

    # DAILY: one new stream activation or stabilization
    if now_time == config["scheduler"]["daily_activation_time"]:
        activate_next_stream_if_needed()

    # DAILY: income-generating work for all active streams
    if now_time == config["scheduler"]["daily_task_time"]:
        run_daily_tasks_all_streams()

    # DAILY REPORT
    if now_time == config["scheduler"]["report_time"]:
        send_daily_report()

    # WEEKLY REPORT
    if weekday == "Sunday" and now_time == config["scheduler"][
            "weekly_report_time"]:
        send_weekly_report()


if __name__ == "__main__":
    log("❤️ JRAVIS Phase Engine started.")
    while True:
        tick_scheduler()
        time.sleep(60)
