import os

def fix_env_encoding():
    file_path = ".env"
    if not os.path.exists(file_path):
        print(".env not found.")
        return

    content = ""
    # Try reading with different encodings
    encodings = ["utf-16", "utf-16-le", "utf-8-sig", "latin1"]
    
    success = False
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                content = f.read()
            print(f"Successfully read .env using {enc}")
            success = True
            break
        except Exception as e:
            continue
            
    if not success:
        print("Failed to read .env with common encodings.")
        return

    # Clean up content (remove BOMs or weird chars if any remain, though standard read handles them)
    # Ensure it starts with basic chars if possible, but the key is what matters.
    
    # Write back as utf-8
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Successfully re-saved .env as UTF-8")
    except Exception as e:
        print(f"Error saving .env: {e}")

if __name__ == "__main__":
    fix_env_encoding()
