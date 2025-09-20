from team_login import get_login
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

IST = ZoneInfo("Asia/Kolkata")

def _ts():
    from datetime import datetime
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")

def login_and_sync(headless: bool = True):
    creds = get_login(6)  # Sl.No 6 — Etsy Digital Store (Elina)
    email, password = creds["email"], creds["password"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        try:
            page.goto("https://www.etsy.com/signin", timeout=60000)
            # Fill login form (Etsy sometimes loads an embedded form)
            page.wait_for_selector('input[name="email"]', timeout=60000)
            page.fill('input[name="email"]', email)
            page.fill('input[name="password"]', password)
            # Click submit
            page.click('button[type="submit"]')
            # Wait for either success (top nav) or 2FA challenge
            try:
                page.wait_for_selector('[data-ui="top-nav"]', timeout=30000)
                logged_in = True
            except PWTimeout:
                logged_in = False

            # 2FA or challenge?
            if not logged_in:
                if page.locator('text=verification code').count() or page.locator('input[type="tel"]').count():
                    return {"ok": False, "why": "2FA required on Etsy login"}
                # Any error banner?
                if page.locator('[role="alert"]').count():
                    err = page.locator('[role="alert"]').inner_text()
                    return {"ok": False, "why": f"login failed: {err.strip()}"}
                return {"ok": False, "why": "login not confirmed (no top-nav detected)"}

            # SUCCESS: proof artifact (screenshot)
            outdir = Path("DailyReport/out"); outdir.mkdir(parents=True, exist_ok=True)
            snap = outdir / f"etsy_login_{datetime.now(IST).strftime('%Y%m%d_%H%M%S')}.png"
            page.screenshot(path=str(snap), full_page=True)
            # TODO: add real sync actions here (listings/orders)
            return {"ok": True, "why": f"logged in as {email}", "screenshot": str(snap)}
        finally:
            context.close()
            browser.close()
