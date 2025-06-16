import os
import json
import sys
import requests
from notion_client import Client
from dotenv import load_dotenv

# ─── Setup ────────────────────────────────────────────────
load_dotenv()
NOTION_TOKEN     = os.getenv("NOTION_API_TOKEN")
DATABASE_ID      = os.getenv("NOTION_DATABASE_ID")
TEMPLATE_PAGE_ID = os.getenv("AUTO_BOOK_TEMPLATE_ID")
GITHUB_RAW       = os.getenv("GITHUB_RAW")
notion           = Client(auth=NOTION_TOKEN)

# ─── Directories ──────────────────────────────────────────
BASE_DIR        = os.path.dirname(os.path.dirname(__file__))
NEW_DIR         = os.path.join(BASE_DIR, "books", "new_books")
PROCESSED_DIR   = os.path.join(BASE_DIR, "books", "processed_books")
COVERS_DIR      = os.path.join(BASE_DIR, "books", "covers")

# ─── Fetch template blocks once ───────────────────────────
def fetch_template_blocks(template_id):
    blocks = []
    cursor = None
    while True:
        resp = notion.blocks.children.list(
            block_id=template_id,
            start_cursor=cursor,
            page_size=100
        )
        blocks.extend(resp["results"])
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return blocks

TEMPLATE_BLOCKS = fetch_template_blocks(TEMPLATE_PAGE_ID)

# ─── Read book JSON ───────────────────────────────────────
def read_book_json(isbn, folder):
    path = os.path.join(folder, f"{isbn}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"No JSON for ISBN {isbn}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ─── Check existence in Notion ────────────────────────────
def book_exists(isbn):
    resp = notion.databases.query(
        database_id=DATABASE_ID,
        filter={"property":"ISBN","rich_text":{"equals":isbn}}
    )
    return bool(resp.get("results"))

# ─── Inject summary into template blocks ──────────────────
def build_children_with_summary(template_blocks, summary_text):
    MAX_LEN = 2000
    if len(summary_text) > MAX_LEN:
        summary_text = summary_text[:MAX_LEN-3] + "..."
    children = []
    skip_next = False
    for block in template_blocks:
        if skip_next:
            skip_next = False
            continue
        children.append(block)
        if block["type"] == "heading_2" and \
           any("📘 Summary" in t.get("plain_text","") 
               for t in block["heading_2"]["rich_text"]):
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type":"text","text":{"content": summary_text or "No summary available."}}
                    ]
                }
            })
            skip_next = True
    return children

# ─── Create Notion page ───────────────────────────────────
def create_book_page(book):
    isbn      = book["ISBN"]
    cover_url = (book.get("Cover","") or "").strip()
    if not cover_url:
        local_fp = os.path.join(COVERS_DIR, f"{isbn}.jpg")
        if os.path.exists(local_fp):
            cover_url = f"{GITHUB_RAW}/books/covers/{isbn}.jpg"
    cover_block = {"type":"external","external":{"url":cover_url}} if cover_url else None

    props = {
        "Title":       {"title":[{"text":{"content": book["Title"]}}]},
        "Status":      {"status":{"name": book["Status"]}},
        "Pages":       {"number": book["Pages"]},
        "Progress":    {"number": book["Progress"]},
        "Author":      {"multi_select":[{"name":a} for a in book["Author"]]},
        "Format":      {"select":{"name": book["Format"]}},
        "ISBN":        {"rich_text":[{"text":{"content": isbn}}]},
        "Created via": {"select":{"name":"Automation"}}
    }
    if cover_url:
        props["url_cover"]  = {"url": cover_url}
        props["book_cover"] = {"files":[{"type":"external","name":f"{isbn}.jpg","external":{"url":cover_url}}]}

    summary  = book.get("Summary","")
    children = build_children_with_summary(TEMPLATE_BLOCKS, summary)

    notion.pages.create(
        parent     = {"database_id": DATABASE_ID},
        properties = props,
        icon       = {"type":"emoji","emoji":"📘"},
        cover      = cover_block,
        children   = children
    )
    print(f"✅ Added to Notion: {book['Title']}")

# ─── Bulk Publish & Move ──────────────────────────────────
if __name__ == "__main__":
    os.makedirs(NEW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    files = [f for f in os.listdir(NEW_DIR) if f.endswith(".json")]
    print(f"→ Publishing {len(files)} new books…")

    for fname in files:
        isbn      = fname.removesuffix(".json")
        new_path  = os.path.join(NEW_DIR, fname)
        proc_path = os.path.join(PROCESSED_DIR, fname)

        print(f"\n→ Processing ISBN: {isbn}")
        if book_exists(isbn):
            print("✔ Already in Notion")
        else:
            book = read_book_json(isbn, NEW_DIR)
            create_book_page(book)

        # Move JSON to processed
        os.replace(new_path, proc_path)
        print(f"📦 Moved {fname} to processed_books/")

    print("\n✅ All done!")
