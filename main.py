"""
Daily job search run (command-line version — the dashboard's "Run search"
button does the same thing from the browser instead).

    python main.py                 # dry-run: report + drafts only, no submissions
    python main.py --live-apply    # also auto-submits on eligible Greenhouse postings
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

from fetch_sources import fetch_all
from generate_search_links import build_links
from scorer import rank_jobs
from draft_cover_letters import draft_all
from auto_apply_greenhouse import apply_to_job, is_greenhouse_url


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-apply", action="store_true",
                         help="Auto-submit on eligible Greenhouse postings instead of dry-run")
    parser.add_argument("--config", default="config.json")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"No {args.config} found. Run the dashboard first (python app.py) and "
              f"complete the setup form, or run setup manually before using main.py directly.")
        return

    with open(config_path) as f:
        config = json.load(f)

    candidate = config.get("candidate", {})
    if not candidate.get("name") or not candidate.get("email"):
        print("config.json is missing your name/email — complete setup in the dashboard "
              "(python app.py) before running the command-line version.")
        return

    print("Fetching jobs from public sources...")
    raw_jobs = fetch_all(config.get("target_titles", [])[:5])
    print(f"  {len(raw_jobs)} unique remote-source jobs fetched")

    ranked = rank_jobs(raw_jobs, config)
    print(f"  {len(ranked)} jobs above match threshold ({config.get('min_match_score_to_report', 35)})")

    drafted = draft_all(ranked, config)

    apply_log = []
    auto_apply_threshold = config.get("min_match_score_to_auto_apply", 65)
    for job in drafted:
        if job["score"] >= auto_apply_threshold and is_greenhouse_url(job["url"]):
            result = apply_to_job(
                job_url=job["url"],
                candidate=candidate,
                resume_path=candidate.get("resume_path", ""),
                cover_note=job["cover_note"],
                live=args.live_apply,
            )
            apply_log.append({"job": job["title"], "company": job["company"], **result})

    on_site_links = build_links(config)

    today = datetime.now().strftime("%Y-%m-%d")
    report_path = Path(f"applications/report_{today}.json")
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(json.dumps({
        "date": today,
        "matched_jobs": drafted,
        "auto_apply_log": apply_log,
        "manual_search_links": on_site_links,
        "fetched_count": len(raw_jobs),
        "live_apply": args.live_apply,
    }, indent=2))

    print(f"\nReport written to {report_path}")
    print(f"Auto-apply attempts: {len(apply_log)}")
    for entry in apply_log:
        print(f"  - {entry['company']} / {entry['job']}: {entry['status']}")
    print(f"\n{len(on_site_links)} manual search links generated — see the report file.")


if __name__ == "__main__":
    main()
