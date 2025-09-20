"""
Platform Connectors for VA Bot
Merged into one file for easier handling
"""

import os
import requests
from playwright.sync_api import sync_playwright

# --------------------------
# Instagram
# --------------------------
INSTAGRAM_USER = os.getenv("INSTAGRAM_USER")
INSTAGRAM_PASS = os.getenv("INSTAGRAM_PASS")


def login_instagram():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.instagram.com/accounts/login/")
        page.fill("input[name='username']", INSTAGRAM_USER)
        page.fill("input[name='password']", INSTAGRAM_PASS)
        page.click("button[type='submit']")
        page.wait_for_timeout(5000)
        cookies = page.context.cookies()
        browser.close()
        return {"status": "logged_in", "cookies": cookies}


# --------------------------
# Printify
# --------------------------
PRINTIFY_API_KEY = os.getenv("PRINTIFY_API_KEY")


def get_printify_shops():
    url = "https://api.printify.com/v1/shops.json"
    headers = {"Authorization": f"Bearer {PRINTIFY_API_KEY}"}
    r = requests.get(url, headers=headers)
    return r.json() if r.status_code == 200 else {"error": r.text}


# --------------------------
# MeshyAI
# --------------------------
MESHY_API_KEY = os.getenv("MESHY_API_KEY")


def list_models():
    url = "https://api.meshy.ai/v1/models"
    headers = {"Authorization": f"Bearer {MESHY_API_KEY}"}
    r = requests.get(url, headers=headers)
    return r.json() if r.status_code == 200 else {"error": r.text}


# --------------------------
# CadCrowd
# --------------------------
CAD_USER = os.getenv("CAD_USER")
CAD_PASS = os.getenv("CAD_PASS")


def login_cadcrowd():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.cadcrowd.com/login")
        page.fill("input[name='email']", CAD_USER)
        page.fill("input[name='password']", CAD_PASS)
        page.click("button[type='submit']")
        page.wait_for_timeout(5000)
        cookies = page.context.cookies()
        browser.close()
        return {"status": "logged_in", "cookies": cookies}


# --------------------------
# Fiverr
# --------------------------
FIVERR_USER = os.getenv("FIVERR_USER")
FIVERR_PASS = os.getenv("FIVERR_PASS")


def login_fiverr():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.fiverr.com/login")
        page.fill("input[name='username']", FIVERR_USER)
        page.fill("input[name='password']", FIVERR_PASS)
        page.click("button[type='submit']")
        page.wait_for_timeout(5000)
        cookies = page.context.cookies()
        browser.close()
        return {"status": "logged_in", "cookies": cookies}


# --------------------------
# YouTube
# --------------------------
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


def get_channel_stats(channel_id):
    url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={channel_id}&key={YOUTUBE_API_KEY}"
    r = requests.get(url)
    return r.json() if r.status_code == 200 else {"error": r.text}


# --------------------------
# StockImageVideo (Shutterstock)
# --------------------------
STOCK_USER = os.getenv("STOCK_USER")
STOCK_PASS = os.getenv("STOCK_PASS")


def login_shutterstock():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://submit.shutterstock.com/login")
        page.fill("input[name='user']", STOCK_USER)
        page.fill("input[name='password']", STOCK_PASS)
        page.click("button[type='submit']")
        page.wait_for_timeout(5000)
        cookies = page.context.cookies()
        browser.close()
        return {"status": "logged_in", "cookies": cookies}


# --------------------------
# Amazon KDP
# --------------------------
KDP_USER = os.getenv("KDP_USER")
KDP_PASS = os.getenv("KDP_PASS")


def login_kdp():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://kdp.amazon.com/")
        page.fill("input[name='email']", KDP_USER)
        page.fill("input[name='password']", KDP_PASS)
        page.click("input[type='submit']")
        page.wait_for_timeout(5000)
        cookies = page.context.cookies()
        browser.close()
        return {"status": "logged_in", "cookies": cookies}


# --------------------------
# Shopify Digital Products
# --------------------------
SHOPIFY_USER = os.getenv("SHOPIFY_USER")
SHOPIFY_PASS = os.getenv("SHOPIFY_PASS")


def login_shopify():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://accounts.shopify.com/store-login")
        page.fill("input[name='account[email]']", SHOPIFY_USER)
        page.fill("input[name='account[password]']", SHOPIFY_PASS)
        page.click("button[type='submit']")
        page.wait_for_timeout(5000)
        cookies = page.context.cookies()
        browser.close()
        return {"status": "logged_in", "cookies": cookies}


# --------------------------
# Amazon Seller Central (Stationery Export)
# --------------------------
AMAZON_USER = os.getenv("AMAZON_USER")
AMAZON_PASS = os.getenv("AMAZON_PASS")


def login_amazon_seller():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://sellercentral.amazon.in/")
        page.fill("input[name='username']", AMAZON_USER)
        page.fill("input[name='password']", AMAZON_PASS)
        page.click("input[type='submit']")
        page.wait_for_timeout(5000)
        cookies = page.context.cookies()
        browser.close()
        return {"status": "logged_in", "cookies": cookies}
