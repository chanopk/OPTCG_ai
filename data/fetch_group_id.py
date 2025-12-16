import requests
import json
import os
import time

"""
Script: fetch_group_id.py
Description: Used to discover and update the list of One Piece Card Game Group IDs from TCGPlayer (via tcgcsv.com).

Usage:
  Run this command to fetch new groups and update data/config_group_id.json:
  $ uv run data/fetch_group_id.py

Output:
  Updates 'data/config_group_id.json' with any new Group IDs found for Category 68 (One Piece).
  Preserves existing 'loaded' status.
"""

# Target Configuration
CONFIG_FILE = "data/config_group_id.json"
CATEGORY_ID = 68
BASE_URL = "https://tcgcsv.com/tcgplayer"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://tcgcsv.com/"
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {"category_id": CATEGORY_ID, "groups": []}
    return {"category_id": CATEGORY_ID, "groups": []}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    print(f"Updated {CONFIG_FILE}")

def fetch_group_ids():
    url = f"{BASE_URL}/{CATEGORY_ID}/groups"
    print(f"Fetching Group IDs from: {url}")
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and "results" in data:
                items = data["results"]
            elif isinstance(data, list):
                items = data
            else:
                print("Unknown response format.")
                return

            print(f"Found {len(items)} groups online.")
            
            # Load existing config
            config = load_config()
            existing_groups = config.get("groups", [])
            
            # Create a lookup for existing groups: groupId -> index
            existing_map = {g["groupId"]: i for i, g in enumerate(existing_groups)}
            
            new_count = 0
            
            for item in items:
                gid = item.get("groupId")
                name = item.get("name")
                
                if gid:
                    if gid in existing_map:
                        # Update name if changed? Or skip.
                        pass
                    else:
                        # New Group found
                        print(f"New Group Found: {name} ({gid})")
                        new_group_obj = {
                            "groupId": gid,
                            "name": name,
                            "loaded": False,
                            "card_count": 0
                        }
                        existing_groups.insert(0, new_group_obj) # Add to top
                        new_count += 1
            
            # Save back updated list
            config["groups"] = existing_groups
            save_config(config)
            
            if new_count > 0:
                print(f"Added {new_count} new groups.")
            else:
                print("No new groups found.")
            
        else:
            print(f"Failed to fetch groups. Status: {resp.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_group_ids()
