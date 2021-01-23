"""
What I really want to know is if a package exists and pypi's xmlrpc api's
are down today & at risk of going away altogether. The HTML API is ugly.

So I'm using a stats API. As a side effect, I can add a cut off for
unpopular packages.
"""

import json
from functools import lru_cache
from typing import Optional

import pypistats

# endpoints
# -----------
# recent downloads
# overall downloads, broken down by mirrors
# major, minor, system, downloads by minor version, system, etc
import requests


@lru_cache(maxsize=1000)
def get_download_count(module: str) -> Optional[int]:
    """Get download count and cache it"""
    try:
        item_string = pypistats.overall(module.strip(), format="json")
    except requests.exceptions.HTTPError as error:
        if error.response.status_code == 404:
            return None
        if error.response.status_code == 429:
            # too many requests
            # BUG: This is wrong
            return None
        raise
    # print(item_string)
    item = json.loads(item_string)
    downloads = None
    if isinstance(item, dict):
        for category in item["data"]:
            if "without_mirrors" in category.values():
                downloads = category["downloads"]
    return downloads
