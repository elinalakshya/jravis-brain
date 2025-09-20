"""
Auto-link PayPal to all Phase 1 platforms
"""

import os
from playwright.sync_api import sync_playwright

PAYPAL_EMAIL = os.getenv("PAYPAL_EMAIL")
COMMON_PASS = os.getenv("COMMON_PASS")  # single password for all


def link_paypal(platform_url, email_field, pass_field, save_button):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(platform_url)
        page.fill(email_field, PAYPAL_EMAIL)
        if pass_field:
            page.fill(pass_field, COMMON_PASS)
        page.click(save_button)
        page.wait_for_timeout(5000)
        browser.close()
        return {"platform": platform_url, "status": "paypal_linked"}


def run_all():
    platforms = [
        ("https://www.instagram.com/payments", "input[name='email']", None,
         "button[type='submit']"),
        ("https://printify.com/settings/payouts", "input[name='paypal_email']",
         None, "button[type='submit']"),
        ("https://meshy.ai/settings/payments", "input[name='paypal']", None,
         "button[type='submit']"),
        ("https://www.cadcrowd.com/settings/payments", "input[name='paypal']",
         None, "button[type='submit']"),
        ("https://www.fiverr.com/settings/payouts",
         "input[name='paypal_email']", None, "button[type='submit']"),
        ("https://www.youtube.com/monetization/payments",
         "input[name='paypal']", None, "button[type='submit']"),
        ("https://submit.shutterstock.com/settings/payments",
         "input[name='paypal']", None, "button[type='submit']"),
        ("https://kdp.amazon.com/settings/payments", "input[name='paypal']",
         None, "button[type='submit']"),
        ("https://shopify.com/settings/payments", "input[name='paypal']", None,
         "button[type='submit']"),
        ("https://sellercentral.amazon.in/payments", "input[name='paypal']",
         None, "button[type='submit']"),
    ]

    results = []
    for url, ef, pf, sb in platforms:
        try:
            res = link_paypal(url, ef, pf, sb)
            results.append(res)
        except Exception as e:
            results.append({"platform": url, "status": f"error: {e}"})

    return results


if __name__ == "__main__":
    print("🔗 Linking PayPal across Phase 1 platforms...")
    results = run_all()
    for r in results:
        print(r)
