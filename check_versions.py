import requests

versions = ["4.3.0", "4.2.0", "4.1.0", "4.0.2"]
base_url = "https://download.blender.org/release/Blender{major}.{minor}/blender-{version}-linux-x64.tar.xz"

for v in versions:
    major, minor, patch = v.split('.')
    url = base_url.format(major=major, minor=minor, version=v)
    try:
        response = requests.head(url)
        if response.status_code == 200:
            print(f"FOUND: {v} at {url}")
            break
        else:
            print(f"NOT FOUND: {v} ({response.status_code})")
    except Exception as e:
        print(f"Error checking {v}: {e}")
