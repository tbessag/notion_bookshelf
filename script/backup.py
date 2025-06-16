import os
import json
from datetime import datetime
from notion_client import Client
from dotenv import load_dotenv

# ─── Setup ────────────────────────────────────────────────
load_dotenv()  # still ok to use .env locally; GH Actions will use secrets
NOTION_TOKEN = os.getenv("NOTION_API_TOKEN")
DATABASE_ID  = os.getenv("NOTION_DATABASE_ID")
BACKUP_DIR   = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups")

notion = Client(auth=NOTION_TOKEN)

# ─── Fetch all pages from the database ────────────────────
def fetch_all_books():
    all_pages = []
    cursor = None
    while True:
        resp = notion.databases.query(
            **{"database_id": DATABASE_ID, "start_cursor": cursor, "page_size": 100}
        )
        all_pages.extend(resp["results"])
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return all_pages

# ─── Main ─────────────────────────────────────────────────
if __name__ == "__main__":
    # ensure backup folder exists
    os.makedirs(BACKUP_DIR, exist_ok=True)

    # fetch
    pages = fetch_all_books()
    
    # write JSON file with today’s date
    today = datetime.now().strftime("%Y-%m-%d")
    out_path = os.path.join(BACKUP_DIR, f"{today}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"date": today, "count": len(pages), "pages": pages}, f, indent=2)
    
    print(f"✅ Backed up {len(pages)} pages to {out_path}")
