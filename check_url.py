import requests

BLENDER_VERSION = "4.0.2"
BLENDER_URL = f"https://download.blender.org/release/Blender{BLENDER_VERSION[:3]}/blender-{BLENDER_VERSION}-linux-x64.tar.xz"

try:
    response = requests.head(BLENDER_URL)
    if response.status_code == 200:
        print(f"URL is valid: {BLENDER_URL}")
    else:
        print(f"URL returned status code: {response.status_code}")
except Exception as e:
    print(f"Error checking URL: {e}")
