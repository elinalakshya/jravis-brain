# vabot/phase1_connectors.py
import os
import requests
import json
from datetime import datetime, timedelta


# -------------------------------
# Instagram Reels (Mock)
# -------------------------------
def instagram_reels():
    return {
        "platform": "Instagram Reels",
        "followers": 15230,
        "views_yesterday": 23500,
        "revenue_est": "₹25,000"
    }


# -------------------------------
# Printify POD Store (LIVE)
# -------------------------------
def printify_store():
    api_key = os.getenv("PRINTIFY_API_KEY")
    if not api_key:
        return {
            "platform": "Printify POD Store",
            "status": "❌ PRINTIFY_API_KEY missing"
        }

    url = "https://api.printify.com/v1/shops.json"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
        return {"platform": "Printify POD Store", "shops": r.json()}
    except Exception as e:
        return {"platform": "Printify POD Store", "status": f"❌ Error: {e}"}


# -------------------------------
# Meshy AI Store (LIVE)
# -------------------------------
def meshy_store():
    api_key = os.getenv("MESHY_API_KEY")
    stats_url = os.getenv("MESHY_STATS_URL")
    if not api_key:
        return {
            "platform": "Meshy AI Store",
            "status": "❌ MESHY_API_KEY missing"
        }
    if not stats_url:
        return {
            "platform": "Meshy AI Store",
            "status": "❌ MESHY_STATS_URL missing"
        }

    today = datetime.utcnow().date()
    yday = today - timedelta(days=1)
    params = {"date_from": yday.isoformat(), "date_to": today.isoformat()}

    try:
        r = requests.get(stats_url,
                         headers={
                             "Authorization": f"Bearer {api_key}",
                             "Accept": "application/json"
                         },
                         params=params,
                         timeout=20)
        r.raise_for_status()
        data = r.json()

        orders = 0
        revenue = 0
        if isinstance(data, dict):
            orders = data.get("orders_yesterday") or data.get("count") or 0
            revenue = data.get("revenue_yesterday") or data.get(
                "total_amount") or 0
            if "items" in data and isinstance(data["items"], list):
                orders = len(data["items"])
                revenue = sum((it.get("total") or it.get("amount") or 0)
                              for it in data["items"])
        elif isinstance(data, list):
            orders = len(data)
            revenue = sum((it.get("total") or it.get("amount") or 0)
                          for it in data if isinstance(it, dict))

        return {
            "platform": "Meshy AI Store",
            "orders_yesterday": orders,
            "revenue_yesterday": revenue,
            "note": "✅ Live Meshy stats"
        }
    except requests.RequestException as e:
        return {
            "platform": "Meshy AI Store",
            "status": "❌ Network error",
            "detail": str(e)
        }
    except (ValueError, json.JSONDecodeError) as e:
        return {
            "platform": "Meshy AI Store",
            "status": "❌ Bad JSON",
            "detail": str(e)
        }


# -------------------------------
# YouTube (LIVE)
# -------------------------------
def youtube_stats(channel_id="UCe2cqtUKLMCm9v9vmsAkKaA"):
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        return {"platform": "YouTube", "status": "❌ YOUTUBE_API_KEY missing"}

    url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={channel_id}&key={api_key}"
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()
        return {"platform": "YouTube", "stats": data}
    except Exception as e:
        return {"platform": "YouTube", "status": f"❌ Error: {e}"}


# -------------------------------
# Cad Crowd Auto Work (Mock)
# -------------------------------
def cadcrowd_auto():
    return {
        "platform": "Cad Crowd Auto Work",
        "projects_done": 2,
        "earnings_yesterday": "₹30,000"
    }


# -------------------------------
# Fiverr AI Gig Automation (Mock)
# -------------------------------
def fiverr_ai():
    return {
        "platform": "Fiverr AI Gig Automation",
        "orders": 3,
        "earnings_yesterday": "₹18,000"
    }


# -------------------------------
# Upwork Freelance Work (Mock)
# -------------------------------
def upwork():
    return {
        "platform": "Upwork",
        "contracts": 1,
        "earnings_yesterday": "₹12,500"
    }


# -------------------------------
# Redbubble POD (Mock)
# -------------------------------
def redbubble():
    return {
        "platform": "Redbubble POD",
        "orders_yesterday": 5,
        "revenue_yesterday": "₹7,200"
    }


# -------------------------------
# Etsy Store (Mock)
# -------------------------------
def etsy_store():
    return {
        "platform": "Etsy Store",
        "orders": 6,
        "revenue_yesterday": "₹9,800"
    }


# -------------------------------
# Freelancer.com Work (Mock)
# -------------------------------
def freelancer_work():
    return {
        "platform": "Freelancer.com",
        "projects_done": 1,
        "earnings_yesterday": "₹6,500"
    }


# -------------------------------
# Amazon KDP (Mock)
# -------------------------------
def amazon_kdp():
    return {
        "platform": "Amazon KDP",
        "books_sold": 15,
        "royalties_yesterday": "₹12,000"
    }


# -------------------------------
# EXPORT ALL
# -------------------------------
CONNECTORS = [
    instagram_reels, printify_store, meshy_store, youtube_stats, cadcrowd_auto,
    fiverr_ai, upwork, redbubble, etsy_store, freelancer_work, amazon_kdp
]
