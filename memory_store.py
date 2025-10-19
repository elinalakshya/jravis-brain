from tinydb import TinyDB, Query
from datetime import datetime

db = TinyDB('jr_memory.json')
reports = db.table('reports')
earnings = db.table('earnings')


def add_report(date, summary, locked=False):
    reports.insert({"date": date, "summary": summary, "locked": locked})


def add_earnings(date, amount, source):
    earnings.insert({"date": date, "amount": amount, "source": source})


# sample usage
if __name__ == "__main__":
    add_report(datetime.utcnow().isoformat(), "Sample daily run", locked=False)
    add_earnings(datetime.utcnow().date().isoformat(), 125000, "Stream A")
    print("Saved sample entries.")
