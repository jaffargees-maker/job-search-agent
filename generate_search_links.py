"""
For platforms that prohibit scraping/automated applications in their ToS
(LinkedIn, Indeed, Rozee.pk), we don't scrape or auto-submit. Instead this
builds direct, pre-filtered search URLs so you can review + one-click apply.
"""
import urllib.parse


def build_links(config: dict) -> list[dict]:
    cities = config.get("search", {}).get("on_site_cities", [])
    titles = config.get("target_titles", [])
    links = []

    if not titles:
        return links

    country_code = (config.get("search", {}).get("country_code") or "").lower()

    # Rozee.pk — Pakistan's largest job board (relevant when country is PK)
    if country_code == "pk":
        for city in cities:
            for title in titles[:6]:
                q = urllib.parse.quote(title)
                c = urllib.parse.quote(city)
                links.append({
                    "site": "Rozee.pk",
                    "query": f"{title} in {city}",
                    "url": f"https://www.rozee.pk/job/jsearch/q/{q}/fc/{c}",
                })

    # Indeed (localized by country code when available, else .com)
    indeed_domain = f"{country_code}.indeed.com" if country_code and country_code != "us" else "www.indeed.com"
    for city in cities:
        q = urllib.parse.quote_plus(" OR ".join(titles[:4]))
        c = urllib.parse.quote_plus(city)
        links.append({
            "site": "Indeed",
            "query": f"Top roles in {city}",
            "url": f"https://{indeed_domain}/jobs?q={q}&l={c}",
        })

    # LinkedIn Jobs (remote + each city)
    q = urllib.parse.quote_plus(" OR ".join(titles[:4]))
    links.append({
        "site": "LinkedIn",
        "query": "Remote roles",
        "url": f"https://www.linkedin.com/jobs/search/?keywords={q}&f_WT=2",
    })
    for city in cities:
        c = urllib.parse.quote_plus(city)
        links.append({
            "site": "LinkedIn",
            "query": f"Roles in {city}",
            "url": f"https://www.linkedin.com/jobs/search/?keywords={q}&location={c}",
        })

    return links


if __name__ == "__main__":
    import json
    with open("config.json") as f:
        config = json.load(f)
    for link in build_links(config):
        print(f"[{link['site']}] {link['query']}\n  {link['url']}\n")
