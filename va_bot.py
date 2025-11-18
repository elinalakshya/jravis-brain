class VAInterface:

    def __init__(self, default_payout):
        self.default_payout = default_payout

    # ---- SETUP + DAILY TASKS ----
    def run_setup_tasks(self, setup_tasks):
        for task in setup_tasks:
            self._run_task(task, phase="setup")

    def run_daily_tasks(self, stream_id, daily_tasks):
        for task in daily_tasks:
            self._run_task(task, phase="daily", stream_id=stream_id)

    def _run_task(self, task, phase="daily", stream_id=None):
        """
      Here you decode task dicts like:
      - {"create_account": {...}}
      - {"generate_reels": {"count": 3, "topics": [...]}}
      - {"design_products": {"count": 5, "types": [...]}}
      and call the appropriate automation functions / APIs.
      """
        # TODO: Implement real handlers per task key.
        pass

    # ---- STABILIZATION ----
    def run_stabilization_checks(self, stream_id, known_issues):
        """
      Return a list of issue descriptions that need fixing.
      This can include:
        - low_engagement
        - no_income_last_X_days
        - api_errors
        - payout_not_configured
      plus any issues from `known_issues`.
      """
        issues_detected = []

        # Example pseudo checks:
        # if self._engagement_too_low(stream_id):
        #     issues_detected.append("low_engagement")
        # if self._no_income_recently(stream_id):
        #     issues_detected.append("no_income_last_3_days")

        # Always include static issues from config as baseline
        issues_detected.extend(known_issues or [])
        return issues_detected

    def solve_issue(self, platform, issue_description):
        """
      Implement platform-specific fix logic:
        - Re-login, refresh tokens
        - Re-create failed posts
        - Update payout info
        - Re-sync products, etc.
      Return a human-readable solution summary.
      """
        # TODO: implement platform-wise resolution
        solution = f"Auto-resolution executed for {platform} issue: {issue_description}"
        return solution

    # ---- LOGGING & REPORTS ----
    def log_issue(self, stream_id, issue, fix):
        # Save to DB/Sheet; for now just print
        print(f"[ISSUE_LOG] Stream {stream_id} | Issue: {issue} | Fix: {fix}")

    def collect_daily_metrics(self, stream_ids):
        # Query all platforms & aggregate stats
        return {
            "streams": stream_ids,
            "timestamp": datetime.now().isoformat(),
            "total_estimated_income": 0,
            "per_stream": {}
        }

    def send_report(self, data, recipient):
        # Build PDF, lock with code, email to Boss
        pass

    def generate_weekly_report(self):
        # Weekly summary & invoices
        pass
