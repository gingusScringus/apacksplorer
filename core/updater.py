import requests
from main import __version__

def check_for_update(repo="gingusScringus/APacKsplorer"):
    try:
        resp = requests.get(f"https://api.github.com/repos/{repo}/releases/latest", timeout=5)
        resp.raise_for_status()
        latest = resp.json()["tag_name"].lstrip("v")
        return latest if latest != __version__ else None
    except requests.RequestException:
        return None