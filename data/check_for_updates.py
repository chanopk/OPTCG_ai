import subprocess
import sys
import os

def run_step(script_name, description):
    print("="*60)
    print(f"STEP: {description}")
    print(f"Running: {script_name}")
    print("="*60)
    
    cmd = ["uv", "run", script_name]
    
    try:
        # Check if uv is available, else try python directly if environment is active
        # But limiting to 'uv run' as per project standard
        
        result = subprocess.run(cmd, check=True)
        print(f"[OK] {description} Success.")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error running {script_name}. Exit code: {e.returncode}")
        print("Stopping update pipeline.")
        sys.exit(e.returncode)
    except FileNotFoundError:
        # Fallback for when 'uv' isn't in PATH, though unlikely in this environment
        print("Error: 'uv' command not found. Please verify your installation.")
        sys.exit(1)

def main():
    print("Starting Knowledge Base Update Pipeline...")
    
    # 1. Fetch Group IDs (Check for new sets)
    run_step("data/fetch_group_id.py", "1. Fetch New Group IDs")
    
    # 2. Fetch Cards (Download content for new sets)
    # We capture output to check if any updates happened
    try:
        print("="*60)
        print("STEP: 2. Download Card Data")
        print("Running: data/fetch_cards.py")
        print("="*60)
        
        # Run and stream output to console while capturing it
        process = subprocess.Popen(
            ["uv", "run", "data/fetch_cards.py"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            text=True
        )
        
        output_lines = []
        for line in process.stdout:
            print(line, end="") # Print to console in real-time
            output_lines.append(line)
            
        process.wait()
        if process.returncode != 0:
            print(f"[ERROR] Step 2 Failed with code {process.returncode}")
            sys.exit(process.returncode)
            
        full_output = "".join(output_lines)
        
        if "All groups are already up-to-date!" in full_output:
            print("\n[INFO] No new cards found. Skipping Vector DB Update to save time/cost.")
            print("\n" + "="*60)
            print("All steps completed successfully!")
            print("Knowledge Base is up to date.")
            print("="*60)
            return
            
    except Exception as e:
        print(f"[ERROR] Step 2 execution failed: {e}")
        sys.exit(1)
    
    # 3. Update Vector DB (Index the data) - Only runs if Step 2 downloaded something
    run_step("data/embed_loader.py", "3. Update Vector Database")
    
    print("\n" + "="*60)
    print("All steps completed successfully!")
    print("Knowledge Base is up to date.")
    print("="*60)

if __name__ == "__main__":
    main()
