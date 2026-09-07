"""
Pulls raw job listings from sources that are (a) free, (b) require no login,
and (c) publicly document that programmatic access is allowed.

Deliberately NOT included: LinkedIn, Indeed, Rozee.pk scraping. Those sites
prohibit automated access in their Terms of Service and use anti-bot
detection that can get your personal account banned. For those, see
generate_search_links.py instead, which just builds you a pre-filtered
search URL to click.
"""
import requests
import feedparser
from datetime import datetime, timezone

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JobSearchAgent/1.0; personal use)"
}


def fetch_remoteok(keyword: str = "") -> list[dict]:
    """RemoteOK public JSON API. Tech-skewed but includes some support/ops roles."""
    url = "https://remoteok.com/api"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[remoteok] fetch failed: {e}")
        return []

    jobs = []
    for item in data:
        if not isinstance(item, dict) or "id" not in item:
            continue  # first element is a legal/meta blob, skip it
        jobs.append({
            "source": "remoteok",
            "title": item.get("position", ""),
            "company": item.get("company", ""),
            "location": item.get("location", "Remote") or "Remote",
            "remote": True,
            "description": item.get("description", ""),
            "url": item.get("url") or f"https://remoteok.com/remote-jobs/{item.get('id')}",
            "tags": item.get("tags", []),
            "posted": item.get("date", ""),
        })
    return jobs


def fetch_arbeitnow(keyword: str = "") -> list[dict]:
    """Arbeitnow free job board API. Broader than RemoteOK, supports search param."""
    url = "https://www.arbeitnow.com/api/job-board-api"
    params = {"search": keyword} if keyword else {}
    jobs = []
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[arbeitnow] fetch failed: {e}")
        return []

    for item in data.get("data", []):
        jobs.append({
            "source": "arbeitnow",
            "title": item.get("title", ""),
            "company": item.get("company_name", ""),
            "location": item.get("location", "") or ("Remote" if item.get("remote") else ""),
            "remote": bool(item.get("remote", False)),
            "description": item.get("description", ""),
            "url": item.get("url", ""),
            "tags": item.get("tags", []),
            "posted": datetime.fromtimestamp(
                item.get("created_at", 0), tz=timezone.utc
            ).isoformat() if item.get("created_at") else "",
        })
    return jobs


WWR_CATEGORY_FEEDS = {
    "customer_support": "https://weworkremotely.com/categories/remote-customer-support-jobs.rss",
    "sales_marketing": "https://weworkremotely.com/categories/remote-sales-and-marketing-jobs.rss",
    "all_other": "https://weworkremotely.com/categories/remote-all-other-jobs.rss",
}


def fetch_weworkremotely() -> list[dict]:
    """WeWorkRemotely category RSS feeds — public, no auth."""
    jobs = []
    for category, feed_url in WWR_CATEGORY_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
        except Exception as e:
            print(f"[weworkremotely:{category}] fetch failed: {e}")
            continue
        for entry in feed.entries:
            title = getattr(entry, "title", "")
            company = ""
            job_title = title
            if ":" in title:
                company, job_title = title.split(":", 1)
            jobs.append({
                "source": f"weworkremotely/{category}",
                "title": job_title.strip(),
                "company": company.strip(),
                "location": "Remote",
                "remote": True,
                "description": getattr(entry, "summary", ""),
                "url": getattr(entry, "link", ""),
                "tags": [],
                "posted": getattr(entry, "published", ""),
            })
    return jobs


def fetch_all(keywords: list[str]) -> list[dict]:
    """Run all sources across the given keyword list, deduping by URL."""
    all_jobs = {}
    for kw in keywords:
        for job in fetch_arbeitnow(kw):
            all_jobs[job["url"]] = job
    for job in fetch_remoteok(""):
        all_jobs[job["url"]] = job
    for job in fetch_weworkremotely():
        all_jobs[job["url"]] = job
    return list(all_jobs.values())


if __name__ == "__main__":
    import json
    jobs = fetch_all(["customer service", "travel", "virtual assistant"])
    print(f"Fetched {len(jobs)} unique jobs")
    print(json.dumps(jobs[:3], indent=2))
