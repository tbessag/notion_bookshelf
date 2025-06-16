#!/usr/bin/env python3
import os, json, re, sys

ROOT       = os.path.dirname(os.path.dirname(__file__))
INPUT_FILE = os.path.join(ROOT, "isbn_input.json")

def load_input():
    if not os.path.exists(INPUT_FILE):
        return {"isbn": []}
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_input(data):
    with open(INPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def sanitize(isbn_raw):
    digits = re.sub(r"[^\d]", "", isbn_raw)
    return digits if len(digits) == 13 else None

if __name__ == "__main__":
    raw = input("Enter ISBN (13 digits or with dashes): ").strip()
    isbn = sanitize(raw)
    if not isbn:
        print("❌ Invalid ISBN. Must be 13 digits.")
        sys.exit(1)

    data = load_input()
    if isbn in data.get("isbn", []):
        print(f"↩️  ISBN {isbn} is already in isbn_input.json")
    else:
        data.setdefault("isbn", []).append(isbn)
        save_input(data)
        print(f"✅ Appended ISBN {isbn} to isbn_input.json")
