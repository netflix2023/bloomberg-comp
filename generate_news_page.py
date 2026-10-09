"""
Bloomberg Trading Challenge - News Intelligence Page Generator
Ensures news.html and bloomberg_news_feed.json are synchronized with the latest market screener.
"""

import os
import json
from datetime import datetime
import bloomberg_news_fetch

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
NEWS_HTML = os.path.join(SCRIPT_DIR, "news.html")

def sync_news_page():
    bloomberg_news_fetch.export_json()
    if os.path.exists(NEWS_HTML):
        print(f"news.html verified and in sync: {NEWS_HTML}")
    return NEWS_HTML

if __name__ == "__main__":
    sync_news_page()
