import os
import json
from datetime import datetime
from notion_client import Client
from dotenv import load_dotenv

# ─── Setup ────────────────────────────────────────────────
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_API_TOKEN")
DATABASE_ID  = os.getenv("NOTION_DATABASE_ID")
BACKUP_DIR   = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups")

notion = Client(auth=NOTION_TOKEN)

# ─── Recursively fetch all children blocks ────────────────
def fetch_block_children(block_id):
    children = []
    cursor = None
    while True:
        resp = notion.blocks.children.list(
            block_id=block_id,
            start_cursor=cursor,
            page_size=100
        )
        for block in resp["results"]:
            # if this block has its own children, recurse
            if block.get("has_children"):
                block["children"] = fetch_block_children(block["id"])
            children.append(block)
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return children

# ─── Fetch all pages + their full block content ───────────┐
def fetch_all_books_with_content():
    all_entries = []
    cursor = None
    while True:
        resp = notion.databases.query(
            **{
                "database_id": DATABASE_ID,
                "start_cursor": cursor,
                "page_size": 100
            }
        )
        for page in resp["results"]:
            page_id = page["id"]
            entry = {
                "id": page_id,
                "properties": page["properties"],
                "content": fetch_block_children(page_id)
            }
            all_entries.append(entry)
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return all_entries

# ─── Main ─────────────────────────────────────────────────
if __name__ == "__main__":
    # ensure backup folder exists
    os.makedirs(BACKUP_DIR, exist_ok=True)

    # fetch pages + content
    entries = fetch_all_books_with_content()
    
    # write JSON file with today’s date
    today = datetime.utcnow().strftime("%Y-%m-%d")
    out_path = os.path.join(BACKUP_DIR, f"{today}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {"date": today, "count": len(entries), "entries": entries},
            f,
            indent=2,
            ensure_ascii=False
        )
    
    print(f"✅ Backed up {len(entries)} pages (with content) to {out_path}")
 