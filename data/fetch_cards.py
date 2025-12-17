import requests
import json
import os
import time
import random

# Configuration
CONFIG_FILE = "data/config_group_id.json"
BASE_URL = "https://tcgcsv.com/tcgplayer/68/{}/products"
OUTPUT_DIR = "data/raw_json"
DELAY_SECONDS = 20

HEAD_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

HEADERS = {
    "User-Agent": HEAD_USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Referer": "https://tcgcsv.com/",
    "Accept-Language": "en-US,en;q=0.9"
}

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return None
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def fetch_group(group_id):
    url = BASE_URL.format(group_id)
    print(f"[{group_id}] Fetching...", end=" ", flush=True)
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=45)
        
        if resp.status_code == 200:
            data = resp.json()
            products = data.get("results", []) if isinstance(data, dict) else data
            
            # Filter Logic
            cards = []
            for p in products:
                name = p.get("name", "").lower()
                is_sealed = any(x in name for x in ["booster pack", "booster box", "case", "display", "sleeves", "playmat", "storage box"])
                
                ext_data = p.get("extendedData", [])
                has_stats = any(d.get("name") in ["Number", "Power", "Life", "CardType"] for d in ext_data)
                
                if has_stats and not is_sealed:
                    cards.append(p)
            
            print(f"Success. Raw: {len(products)}, Cards: {len(cards)}")
            return cards
            
        elif resp.status_code == 403:
            print(f"BLOCKED (403).")
            return "BLOCKED"
        else:
            print(f"Failed ({resp.status_code}).")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    ensure_dir(OUTPUT_DIR)
    config = load_config()
    if not config:
        print("Config not found.")
        return

    groups = config.get("groups", [])
    print(f"Found {len(groups)} groups in config.")
    
    blocked_count = 0
    updated_any = False
    
    for idx, group in enumerate(groups):
        gid = group["groupId"]
        
        # SKIP if already loaded
        # SKIP if already loaded
        if group.get("loaded", False):
            print(f"[{gid}] Skipping (Already Loaded)") 
            continue
            
        # Check download limits
        if blocked_count >= 3:
            print("Too many blocks. Stopping.")
            break

        cards = fetch_group(gid)
        
        if cards == "BLOCKED":
            blocked_count += 1
        elif isinstance(cards, list):
            blocked_count = 0
            
            filepath = os.path.join(OUTPUT_DIR, f"cards_{gid}.json")
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(cards, f, indent=2, ensure_ascii=False)
            
            # Update Config loaded status
            group["loaded"] = True
            group["card_count"] = len(cards)
            updated_any = True
            
            # Save config incrementally (safer than waiting for end)
            save_config(config) 

            # Delay
            sleep_time = DELAY_SECONDS + random.uniform(-5, 5)
            print(f"Sleeping {sleep_time:.1f}s...")
            time.sleep(sleep_time)
            
        else:
            # Failed but not blocked (maybe 404 or timeout)
            time.sleep(5)
            
    if not updated_any:
        print("All groups are already up-to-date!")
    else:
        print("Ingestion batch complete.")

if __name__ == "__main__":
    main()
