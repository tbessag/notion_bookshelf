import os
import json
import sys
import re
import requests
from datetime import date

# ─── Configuration ────────────────────────────────────────
BASE_DIR        = os.path.dirname(os.path.dirname(__file__))
ISBN_INPUT      = os.path.join(BASE_DIR, "isbn_input.json")
NEW_DIR         = os.path.join(BASE_DIR, "books", "new_books")
PROCESSED_DIR   = os.path.join(BASE_DIR, "books", "processed_books")
COVERS_DIR      = os.path.join(BASE_DIR, "books", "covers")

# ─── Google Books Fetch ──────────────────────────────────
def fetch_book_metadata(isbn: str) -> dict:
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    response = requests.get(url)
    data = response.json()
    if "items" not in data:
        raise ValueError(f"No book found for ISBN: {isbn}")
    info = data["items"][0]["volumeInfo"]
    authors = info.get("authors", ["Unknown Author"])
    return {
        "Title":    info.get("title", "Unknown Title"),
        "Status":   "Not started",
        "Pages":    info.get("pageCount"),
        "Progress": 0,
        "Author":   authors,
        "Format":   "Physical",
        "ISBN":     isbn,
        "Cover":    info.get("imageLinks", {}).get("thumbnail", ""),
        "Summary":  info.get("description", "")
    }

# ─── OpenLibrary Fallback ────────────────────────────────
def get_author_name(author_ref):
    if isinstance(author_ref, dict) and "key" in author_ref:
        key = author_ref["key"]
        url = f"https://openlibrary.org{key}.json"
        try:
            resp = requests.get(url, verify=False)
            if resp.status_code == 200:
                return resp.json().get("name", "")
        except Exception as e:
            print(f"⚠️ Failed to resolve author {key}: {e}")
    return ""

def fetch_book_metadata_openlibrary(isbn: str) -> dict:
    url = f"https://openlibrary.org/isbn/{isbn}.json"
    response = requests.get(url, verify=False)
    if response.status_code != 200:
        raise ValueError(f"No OpenLibrary entry for ISBN: {isbn}")
    data = response.json()
    authors = [get_author_name(a) for a in data.get("authors", [])]
    desc = data.get("description", "")
    if isinstance(desc, dict):
        desc = desc.get("value", "")
    return {
        "Title":    data.get("title", "Unknown Title"),
        "Status":   "Not started",
        "Pages":    data.get("number_of_pages"),
        "Progress": 0,
        "Author":   authors,
        "Format":   "Physical",
        "ISBN":     isbn,
        "Cover":    f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg",
        "Summary":  desc
    }

# ─── Save JSON Metadata ───────────────────────────────────
def save_book_json(metadata: dict):
    os.makedirs(NEW_DIR, exist_ok=True)
    path = os.path.join(NEW_DIR, f"{metadata['ISBN']}.json")
    if os.path.exists(path):
        print(f"↩️ Skipping existing: {path}")
    else:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        print(f"✅ Saved metadata: {path}")

# ─── Download Cover Image ────────────────────────────────
def download_cover_image(cover_url: str, isbn: str):
    if not cover_url:
        print(f"⚠️ No cover URL for ISBN: {isbn}")
        return
    os.makedirs(COVERS_DIR, exist_ok=True)
    filename = os.path.join(COVERS_DIR, f"{isbn}.jpg")
    if os.path.exists(filename):
        print(f"↩️ Cover already exists: {filename}")
        return
    try:
        resp = requests.get(cover_url, stream=True, verify=False)
        if resp.status_code == 200:
            with open(filename, "wb") as f:
                for chunk in resp.iter_content(1024):
                    f.write(chunk)
            print(f"✅ Saved cover: {filename}")
        else:
            print(f"❌ Failed to download cover ({resp.status_code}) for ISBN: {isbn}")
    except Exception as e:
        print(f"❌ Error downloading cover for {isbn}: {e}")

# ─── Batch Processing ────────────────────────────────────
def process_isbn_list(isbn_list):
    os.makedirs(NEW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    for isbn in isbn_list:
        new_path = os.path.join(NEW_DIR, f"{isbn}.json")
        done_path = os.path.join(PROCESSED_DIR, f"{isbn}.json")
        if os.path.exists(new_path) or os.path.exists(done_path):
            print(f"↩️ Skipping already handled ISBN: {isbn}")
            continue
        try:
            metadata = fetch_book_metadata(isbn)
        except ValueError:
            print(f"🔄 Falling back OpenLibrary for {isbn}...")
            try:
                metadata = fetch_book_metadata_openlibrary(isbn)
            except Exception as e:
                print(f"❌ OpenLibrary also failed for {isbn}: {e}")
                continue
        except Exception as e:
            print(f"❌ Fetch failed for {isbn}: {e}")
            continue
        save_book_json(metadata)
        download_cover_image(metadata.get("Cover", ""), isbn)

# ─── Entry Point ─────────────────────────────────────────
if __name__ == "__main__":
    if not os.path.exists(ISBN_INPUT):
        print(f"❌ isbn_input.json not found at {ISBN_INPUT}")
        sys.exit(1)
    with open(ISBN_INPUT, "r", encoding="utf-8") as f:
        raw = json.load(f)
    def sanitize(data):
        return [re.sub(r"[^\d]", "", s) for s in data.get("isbn", []) if len(re.sub(r"[^\d]", "", s)) == 13]
    isbns = sanitize(raw)
    print(f"→ Processing {len(isbns)} ISBNs...")
    process_isbn_list(isbns)
