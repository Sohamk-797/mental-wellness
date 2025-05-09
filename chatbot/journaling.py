import json
import os
from datetime import datetime

# File to store journal entries
JOURNAL_FILE = "journal_entries.json"

def save_entry(entry):
    """Save a journal entry to the journal file."""
    entries = get_entries()
    entries.append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "content": entry
    })
    with open(JOURNAL_FILE, "w") as f:
        json.dump(entries, f, indent=4)

def get_entries():
    """Retrieve all journal entries from the journal file."""
    if os.path.exists(JOURNAL_FILE):
        with open(JOURNAL_FILE, "r") as f:
            return json.load(f)
    return []
