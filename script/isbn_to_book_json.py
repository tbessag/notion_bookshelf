import os
import json
import requests
from datetime import date

# --- Google Books Fetch ---
def fetch_book_metadata(isbn: str) -> dict:
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    response = requests.get(url)
    data = response.json()

    if "items" not in data:
        raise ValueError(f"No book found for ISBN: {isbn}")

    book_info = data["items"][0]["volumeInfo"]
    authors = book_info.get("authors", ["Unknown Author"])

    return {
        "Title": book_info.get("title", "Unknown Title"),
        "Status": "Not started",
        "Pages": book_info.get("pageCount", None),
        "Progress": 0,
        "Started On": "",
        "Finished On": "",
        "Author": authors,
        "Collection": "",
        "Genre": "",
        "Format": "Physical",
        "ISBN": isbn,
        "Cover": book_info.get("imageLinks", {}).get("thumbnail", ""),
        "Summary": book_info.get("description", "")
    }

# --- OpenLibrary Fallback ---
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
        raise ValueError(f"OpenLibrary: No book found for ISBN: {isbn}")

    data = response.json()
    authors = data.get("authors", [])
    author_names = [get_author_name(a) for a in authors]

    # Description fallback handling
    desc = data.get("description", "")
    if isinstance(desc, dict):
        desc = desc.get("value", "")

    return {
        "Title": data.get("title", "Unknown Title"),
        "Status": "Not started",
        "Pages": data.get("number_of_pages", None),
        "Progress": 0,
        "Started On": "",
        "Finished On": "",
        "Author": author_names,
        "Collection": "",
        "Genre": "",
        "Format": "Physical",
        "ISBN": isbn,
        "Cover": f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg",
        "Summary": desc
    }

# --- Save to File ---
def save_book_json(metadata: dict, output_dir="books"):
    os.makedirs(output_dir, exist_ok=True)
    isbn = metadata["ISBN"]
    path = os.path.join(output_dir, f"{isbn}.json")

    if os.path.exists(path):
        print(f"⚠️ Book already exists: {path}")
    else:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        print(f"✅ Saved: {path}")

# --- Cover download ---
def download_cover_image(cover_url: str, isbn: str, output_dir="covers"):
    if not cover_url:
        print(f"⚠️ No cover URL for ISBN: {isbn}")
        return

    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"{isbn}.jpg")

    if os.path.exists(filename):
        print(f"🖼️ Cover already exists: {filename}")
        return

    try:
        response = requests.get(cover_url, stream=True, verify=False)
        if response.status_code == 200:
            with open(filename, "wb") as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"✅ Cover saved: {filename}")
        else:
            print(f"❌ Failed to download cover for ISBN {isbn} (HTTP {response.status_code})")
    except Exception as e:
        print(f"❌ Error downloading cover for {isbn}: {e}")

# --- Batch Processing ---
def process_isbn_list(isbn_list):
    for isbn in isbn_list:
        try:
            metadata = fetch_book_metadata(isbn)
        except ValueError:
            print(f"🔄 Trying OpenLibrary for {isbn}...")
            try:
                metadata = fetch_book_metadata_openlibrary(isbn)
            except Exception as e:
                print(f"❌ OpenLibrary also failed for {isbn}: {e}")
                continue
        except Exception as e:
            print(f"❌ Failed for {isbn}: {e}")
            continue

        save_book_json(metadata)
        download_cover_image(metadata.get("Cover"), isbn)


# --- Entry Point ---
if __name__ == "__main__":
    raw_input = {
        "isbn": [
            "978-1-5098-6739-1",
            "978-0-679-76288-1",
            "978-2-07-036822-8",
            "978-0-141-03613-7"
        ]
    }

    def sanitize_isbn_list(data):
        import re
        return [re.sub(r"[^\d]", "", x) for x in data.get("isbn", []) if len(re.sub(r"[^\d]", "", x)) == 13]

    clean_isbns = sanitize_isbn_list(raw_input)
    process_isbn_list(clean_isbns)
