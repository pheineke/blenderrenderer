import os
import sys
import subprocess
import requests
import tarfile
import shutil
import time
from pathlib import Path

# Configuration
BLENDER_VERSION = "4.4"
BLENDER_URL = f"https://download.blender.org/release/Blender{BLENDER_VERSION[:3]}/blender-{BLENDER_VERSION}-linux-x64.tar.xz"
BLENDER_DIR = Path("blender-bin")
CLOUDFLARED_PATH = Path("cloudflared/cloudflared-linux-amd64")

def check_blender():
    """Check if blender is available in PATH or locally."""
    # Check PATH
    if shutil.which("blender"):
        print("Blender found in PATH.")
        return "blender"
    
    # Check local directory
    local_blender = BLENDER_DIR / f"blender-{BLENDER_VERSION}-linux-x64/blender"
    if local_blender.exists():
        print(f"Blender found locally at {local_blender}")
        return str(local_blender.absolute())
    
    return None

def download_blender():
    """Download and extract Blender."""
    print(f"Blender not found. Downloading from {BLENDER_URL}...")
    BLENDER_DIR.mkdir(exist_ok=True)
    
    tar_path = BLENDER_DIR / "blender.tar.xz"
    
    response = requests.get(BLENDER_URL, stream=True)
    response.raise_for_status()
    
    with open(tar_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            
    print("Download complete. Extracting...")
    with tarfile.open(tar_path, "r:xz") as tar:
        tar.extractall(path=BLENDER_DIR)
        
    print("Extraction complete.")
    # Cleanup tar file
    os.remove(tar_path)
    
    local_blender = BLENDER_DIR / f"blender-{BLENDER_VERSION}-linux-x64/blender"
    return str(local_blender.absolute())

def start_cloudflared():
    """Start cloudflared tunnel."""
    if not CLOUDFLARED_PATH.exists():
        print(f"Warning: Cloudflared binary not found at {CLOUDFLARED_PATH}")
        return None
        
    print("Starting Cloudflared tunnel...")
    # Make sure it's executable
    os.chmod(CLOUDFLARED_PATH, 0o755)
    
    # Start tunnel for port 5000
    # Using 'tunnel --url' for quick ad-hoc tunnel, or user might have a config.
    # Assuming ad-hoc for now as per "handles cloudflared tunnel" request without config details.
    cmd = [str(CLOUDFLARED_PATH), "tunnel", "--url", "http://localhost:5000"]
    
    # Run in background
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return proc

def main():
    # 1. Setup Blender
    blender_path = check_blender()
    if not blender_path:
        blender_path = download_blender()
        
    print(f"Using Blender at: {blender_path}")
    os.environ["BLENDER_PATH"] = blender_path
    
    # 2. Start Cloudflared
    # We'll start it in the background. 
    # Note: In a real deployment, you might want to read the output to get the URL.
    cf_process = start_cloudflared()
    
    if cf_process:
        print("Cloudflared started. Check logs for URL if not configured via config file.")
    
    # 3. Start Flask App
    print("Starting Flask server...")
    try:
        # Run app.py using the current python interpreter
        subprocess.run([sys.executable, "app.py"], check=True)
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        if cf_process:
            print("Stopping Cloudflared...")
            cf_process.terminate()

if __name__ == "__main__":
    main()
