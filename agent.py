#!/usr/bin/env python3
"""
Competitive intelligence agent for Novaterra.

This script loads a fixed list of competitors from `competitors.json`,
queries the web for recent information about each competitor, filters out
previously reported links from `memory.json`, assigns a simple category to
each new result and writes a dated Markdown report in the `reports/`
directory.  It also updates `memory.json` so that future runs only notify
about genuinely new items.

The script is designed to be executed weekly by a GitHub Action.  It does
not require any external credentials; however, the simple scraping
approach using DuckDuckGo may be brittle.  For production use, consider
switching to a paid search API for more reliable results.
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

import requests
from bs4 import BeautifulSoup


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/114.0 Safari/537.36"
)


def load_json(path: str) -> Any:
    """Load JSON from a file, returning an empty dict on failure."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as exc:
        print(f"Error decoding JSON from {path}: {exc}", file=sys.stderr)
        return {}


def save_json(path: str, data: Any) -> None:
    """Write JSON to a file with UTF‑8 encoding and pretty formatting."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def search_duckduckgo(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    """Perform a simple DuckDuckGo search and return a list of result dicts.

    Each result contains a `title` and a `url`.  The function scrapes the
    HTML from DuckDuckGo's no‑JavaScript results page (`/html/`).  Note that
    DuckDuckGo throttles requests and may block repeated queries.  For a
    production‑grade implementation consider using a proper search API.
    """
    results: List[Dict[str, str]] = []
    url = "https://duckduckgo.com/html/"
    params = {"q": query, "ia": "web"}
    try:
        response = requests.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"Error fetching search results for '{query}': {exc}", file=sys.stderr)
        return results
    soup = BeautifulSoup(response.text, "html.parser")
    # DuckDuckGo returns results in <a class="result__a" href="...">text</a>
    for link_tag in soup.select("a.result__a"):
        href = link_tag.get("href")
        # DuckDuckGo rewrites the result URLs through '/l/?kh='; keep as is for memory key
        title = link_tag.get_text(strip=True)
        if href and title:
            results.append({"title": title, "url": href})
            if len(results) >= max_results:
                break
    return results


def classify_title(title: str) -> str:
    """Classify the result into one of four high‑level categories based on keywords.

    - **Annonces produit**: product launches, new phases, project openings or
      deliveries.
    - **Pricing & commercial**: pricing changes, promotions, discounts or new
      offers.
    - **Communication & presse**: press releases, articles, partnerships and
      events.
    - **Signaux faibles**: recruitment, leadership moves, permits and other
      weak signals.
    """
    text = title.lower()
    product_keywords = ["phase", "project", "launch", "delivery", "opening", "introducing"]
    pricing_keywords = ["price", "promotion", "offer", "discount", "rs", "deal", "package"]
    press_keywords = ["press", "article", "release", "partnership", "event", "conference", "seminar"]
    weak_keywords = ["recruit", "hiring", "appointment", "director", "ceo", "permit", "certificate", "linkedin"]

    if any(k in text for k in product_keywords):
        return "Annonces produit"
    if any(k in text for k in pricing_keywords):
        return "Pricing & commercial"
    if any(k in text for k in press_keywords):
        return "Communication & presse"
    if any(k in text for k in weak_keywords):
        return "Signaux faibles"
    return "Unclassified"


def main() -> None:
    # Determine today's date in UTC for report naming
    today = datetime.utcnow().date().isoformat()

    # Load competitor definitions and existing memory
    competitors: List[Dict[str, Any]] = load_json(os.path.join(os.path.dirname(__file__), "competitors.json"))
    memory: Dict[str, List[str]] = load_json(os.path.join(os.path.dirname(__file__), "memory.json"))

    # Ensure memory contains an entry for each competitor
    for comp in competitors:
        memory.setdefault(comp["name"], [])

    new_items: List[Dict[str, str]] = []

    # Loop through competitors and search for each keyword
    for comp in competitors:
        name = comp["name"]
        keywords: List[str] = comp.get("keywords", [])
        seen_links = set(memory.get(name, []))
        for query in keywords:
            results = search_duckduckgo(query, max_results=5)
            for res in results:
                link = res["url"]
                title = res["title"]
                # Use the raw link as identifier; DuckDuckGo rewrites links but the
                # memory should store exactly what is returned to avoid duplicates.
                if link not in seen_links:
                    category = classify_title(title)
                    new_items.append({
                        "competitor": name,
                        "title": title,
                        "url": link,
                        "category": category
                    })
                    memory[name].append(link)
                    seen_links.add(link)

    # Write report if there are any new items
    if new_items:
        reports_dir = os.path.join(os.path.dirname(__file__), "reports")
        os.makedirs(reports_dir, exist_ok=True)
        report_path = os.path.join(reports_dir, f"{today}.md")
        with open(report_path, "w", encoding="utf-8") as report_file:
            report_file.write(f"# Veille concurrentielle – Semaine du {today}\n\n")
            report_file.write("Ce rapport liste les nouveautés identifiées pour les smart cities concurrentes de Beau Plan durant la semaine écoulée.\n\n")
            # Group items by competitor for readability
            items_by_comp: Dict[str, List[Dict[str, str]]] = {}
            for item in new_items:
                items_by_comp.setdefault(item["competitor"], []).append(item)
            for competitor, items in items_by_comp.items():
                report_file.write(f"## {competitor}\n\n")
                for item in items:
                    report_file.write(f"* **{item['category']}** – [{item['title']}]({item['url']})\n")
                report_file.write("\n")

    # Persist updated memory
    save_json(os.path.join(os.path.dirname(__file__), "memory.json"), memory)


if __name__ == "__main__":
    main()