"""
Google Search + Fetch Tools for ADK

- google_search_tool(query, ...) -> returns numbered results (title, url, snippet)
- fetch_search_pages_tool(search_results_text, top_n=3, ...) -> fetches the first N URLs
  from the results text and returns cleaned page text (no model).

Env:
  GOOGLE_API_KEY  : Google Cloud API key for Custom Search JSON API
  GOOGLE_CSE_ID   : Your Programmable Search Engine (CSE) ID ("cx")

Add to requirements.txt:
  requests
  beautifulsoup4
"""

import os
import re
import time
from typing import Optional, List
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

from google.adk.tools import FunctionTool

load_dotenv()

GOOGLE_SEARCH = os.getenv("GOOGLE_SEARCH")
GOOGLE_CSE_ID  = os.getenv("GOOGLE_CSE_ID")

def google_web_search(
    query: str,
    num_results: int = 3,
    site: Optional[str] = None,
    recent_days: Optional[int] = None,
    lang: Optional[str] = None,
) -> str:
    """
    Perform a Google Custom Search; return numbered list with title, URL, snippet.
    """

    num = max(1, min(int(num_results), 10))

    q = query.strip()
    if site:
        site = site.strip()
        if not site.startswith("site:"):
            site = f"site:{site}"
        q = f"{site} {q}"

    params = {
        "key": GOOGLE_SEARCH,
        "cx": GOOGLE_CSE_ID,
        "q": q,
        "num": num,
        "safe": "active",  # or "off"
    }
    if lang:
        params["lr"] = f"lang_{lang}"
        params["hl"] = lang
    if recent_days and int(recent_days) > 0:
        params["dateRestrict"] = f"d{int(recent_days)}"

    try:
        resp = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=20)
        if resp.status_code != 200:
            return f"Search error {resp.status_code}: {resp.text}"
        data = resp.json()
        items = data.get("items", [])
        if not items:
            return "No results found."
        lines = []
        for i, it in enumerate(items, 1):
            title = (it.get("title") or "").strip()
            link = (it.get("link") or "").strip()
            snippet = (it.get("snippet") or "").replace("\n", " ").strip()
            lines.append(f"{i}. {title}\n{link}\n{snippet}")
        return "\n\n".join(lines)
    except Exception as e:
        return f"Error performing search: {e}"


# 2) Fetch & read top-N pages from search results text
def _extract_urls_from_results_text(results_text: str, limit: int) -> List[str]:
    # Finds http/https links in the text; keeps order, dedupes.
    urls = []
    seen = set()
    for m in re.finditer(r"https?://[^\s)]+", results_text):
        url = m.group(0).rstrip(").,]>'\"")  # trim common trailing punctuation
        if url not in seen:
            seen.add(url)
            urls.append(url)
        if len(urls) >= limit:
            break
    return urls

def _fetch_url_text(url: str, timeout: int = 20, max_chars: int = 8000) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/119.0 Safari/537.36"
        )
    }
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.status_code == 429:
            # simple backoff & retry once
            time.sleep(1.5)
            r = requests.get(url, headers=headers, timeout=timeout)
        if r.status_code != 200:
            return f"[{url}] HTTP {r.status_code} - unable to fetch."
        html = r.text or ""
        soup = BeautifulSoup(html, "html.parser")

        # Remove scripts/styles/nav/footer for cleaner text
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        for tag_name in ["nav", "footer", "form"]:
            for t in soup.find_all(tag_name):
                t.decompose()

        text = soup.get_text(separator="\n")
        # normalize whitespace
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{2,}", "\n\n", text)
        text = text.strip()

        if not text:
            return f"[{url}] Empty page or unreadable content."
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[...truncated...]"
        return f"[URL] {url}\n\n{text}"
    except Exception as e:
        return f"[{url}] Error: {e}"

def fetch_search_pages(
    search_results_text: str,
    top_n: int = 3,
    max_chars_per_page: int = 8000
) -> str:
    """
    Parse the numbered search results text (title/URL/snippet format),
    fetch the first N URLs, and return cleaned page text (plain text).
    """
    try:
        urls = _extract_urls_from_results_text(search_results_text, max(1, top_n))
        if not urls:
            return "No URLs found in the provided search results text."
        outputs = []
        for url in urls:
            outputs.append(_fetch_url_text(url, max_chars=max_chars_per_page))
        return "\n\n" + ("\n\n" + ("-" * 40) + "\n\n").join(outputs)
    except Exception as e:
        return f"Error fetching pages: {e}"
    
    
google_search_tool = FunctionTool(google_web_search)
fetch_search_pages_tool = FunctionTool(fetch_search_pages)