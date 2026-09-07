"""
Simple, transparent keyword-based scoring — no black box. Every point is
traceable back to a specific keyword hit so you can see *why* a job matched.
"""
import re


def _text_blob(job: dict) -> str:
    parts = [job.get("title", ""), job.get("description", ""), " ".join(job.get("tags", []))]
    return " ".join(parts).lower()


def score_job(job: dict, config: dict) -> dict:
    blob = _text_blob(job)

    for bad in config.get("exclude_keywords", []):
        if bad.lower() in blob:
            return {"score": 0, "reasons": [f"excluded: matched '{bad}'"]}

    score = 0
    reasons = []

    for kw in config.get("must_have_keywords", []):
        if re.search(r"\b" + re.escape(kw.lower()) + r"\b", blob):
            score += 8
            reasons.append(f"+8 must-have: '{kw}'")

    for kw in config.get("nice_to_have_keywords", []):
        if re.search(r"\b" + re.escape(kw.lower()) + r"\b", blob):
            score += 3
            reasons.append(f"+3 nice-to-have: '{kw}'")

    for title in config.get("target_titles", []):
        if title.lower() in job.get("title", "").lower():
            score += 15
            reasons.append(f"+15 title match: '{title}'")
            break

    if job.get("remote"):
        score += 5
        reasons.append("+5 remote-friendly")

    score = min(score, 100)
    return {"score": score, "reasons": reasons}


def rank_jobs(jobs: list[dict], config: dict) -> list[dict]:
    scored = []
    for job in jobs:
        result = score_job(job, config)
        if result["score"] >= config.get("min_match_score_to_report", 35):
            job = {**job, **result}
            scored.append(job)
    scored.sort(key=lambda j: j["score"], reverse=True)
    return scored
