"""Check every URL in the pathway catalog. Run on Replit (needs internet):
    python -m tests.check_links
Then set verified=true and checked_on=YYYY-MM-DD for links you have opened yourself."""
import urllib.request

from src.backend.data_store import load

for item in load()["catalog"]:
    url = item.get("url")
    if not url:
        continue
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        code = urllib.request.urlopen(req, timeout=20).status
    except Exception as e:  # noqa: BLE001
        code = f"ERROR {e}"
    print(f"{code}\t{item['id']}\t{url}")
