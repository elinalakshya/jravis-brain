#!/usr/bin/env python3
"""
printify_create_api_key.py
Headless attempt to login to Printify and create an API token.
Requires: MASTER_USER and MASTER_PASS exported in the environment.
Saves result to generated_api_keys.json (merges if exists).
"""
import os, json, time, sys
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

MASTER_USER = os.getenv("MASTER_USER")
MASTER_PASS = os.getenv("MASTER_PASS")
if not MASTER_USER or not MASTER_PASS:
    print("Missing MASTER_USER / MASTER_PASS in env.")
    sys.exit(2)

OUTFILE = "generated_api_keys.json"


def save_result(platform, data):
    out = {}
    if os.path.exists(OUTFILE):
        out = json.load(open(OUTFILE, "r"))
    out.setdefault("generated", {}).update({platform: data})
    # keep needs_manual section if present
    if "needs_manual" not in out:
        out["needs_manual"] = {}
    json.dump(out, open(OUTFILE, "w"), indent=2)
    print(f"Saved {platform} result to {OUTFILE}")


with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False)  # start with headed = easier for first run
    context = browser.new_context()
    page = context.new_page()
    try:
        print("Opening Printify login page...")
        page.goto("https://printify.com/login", timeout=60000)
        # wait & fill login form — selectors may need adjustment (inspect page)
        page.fill("input[type='email']", MASTER_USER)
        page.fill("input[type='password']", MASTER_PASS)
        page.click("button[type='submit']")
        # wait for navigation
        page.wait_for_load_state("networkidle", timeout=30000)
        time.sleep(2)

        # After login, navigate to API tokens page — URL may differ; try common paths
        # Try direct path used by Printify for API tokens
        possible_paths = [
            "https://printify.com/app/settings/integrations",
            "https://printify.com/app/developers/api-tokens",
            "https://printify.com/app/settings/api"
        ]
        found = False
        for url in possible_paths:
            try:
                page.goto(url, timeout=20000)
                page.wait_for_load_state("networkidle", timeout=20000)
                # heuristics: look for "Generate token" or "Create token" button
                if page.query_selector(
                        "button:has-text('Generate')") or page.query_selector(
                            "button:has-text('Create')"):
                    found = True
                    break
            except PWTimeout:
                pass

        if not found:
            print(
                "Could not find API token page automatically. Please navigate manually in the opened browser to the Printify API token page and generate one, then paste it here."
            )
            browser.close()
            sys.exit(3)

        # click generate button (try multiple button text variants)
        btn = None
        for text in ("Generate token", "Generate API token", "Create token",
                     "Create API token", "Generate new token"):
            btn = page.query_selector(f"button:has-text(\"{text}\")")
            if btn:
                print(f"Clicking button '{text}'")
                btn.click()
                break

        if not btn:
            print(
                "No generate button found after navigation. Please generate token manually in the opened browser."
            )
            browser.close()
            sys.exit(4)

        # After clicking, token may appear in a modal or row; wait for input/textarea showing token
        try:
            # token often in input or textarea or a code element
            page.wait_for_selector("input[readonly]", timeout=5000)
            token_el = page.query_selector("input[readonly]")
            token = token_el.get_attribute("value") if token_el else None
        except PWTimeout:
            token = None

        if not token:
            # try to find code or text with typical token prefix
            possible = page.query_selector_all("code, pre, input, textarea")
            for el in possible:
                txt = el.text_content() or el.get_attribute("value") or ""
                if txt and ("printify" in txt.lower()
                            or len(txt.strip()) > 10):
                    token = txt.strip()
                    break

        if not token:
            print(
                "Token not found automatically. Please check the browser window, copy the token and paste it in the console now (or set PRINTIFY_KEY in Replit secrets)."
            )
            # keep browser open for manual copy
            print("Browser will remain open for 5 minutes for manual copy...")
            time.sleep(300)
            browser.close()
            sys.exit(5)

        print("Token captured:", token)
        save_result("PrintifyPOD", {"api_key": token})
        browser.close()
        sys.exit(0)

    except Exception as e:
        print("Error during automation:", e)
        browser.close()
        sys.exit(6)
