"""
Drafts a short, tailored cover note per matched job. Uses a template filled
with strengths YOU provided in the setup form (config["candidate"]["key_strengths"]) —
no external API call needed, so it works even with the sandboxed network.

IMPORTANT: this file intentionally does not hardcode anyone's experience.
Earlier versions of this script had one person's specific work history baked
in as a lookup table, which meant every applicant using it would send out
cover letters describing someone else's background. Every sentence used here
now comes from what the applicant themselves entered during setup.
"""
import json


def _pick_strengths(job: dict, strengths: list[str], max_n: int = 2) -> list[str]:
    if not strengths:
        return []
    blob = (job.get("title", "") + " " + job.get("description", "")).lower()

    # Prefer strengths whose own words show up in the job listing; fall back
    # to the applicant's first strengths if nothing lines up textually.
    scored = []
    for s in strengths:
        words = [w.strip(".,") for w in s.lower().split() if len(w) > 4]
        hits = sum(1 for w in words if w in blob)
        scored.append((hits, s))
    scored.sort(key=lambda x: x[0], reverse=True)

    picked = [s for hits, s in scored if hits > 0][:max_n]
    if not picked:
        picked = strengths[:max_n]
    return picked


def draft_note(job: dict, candidate: dict) -> str:
    strengths = candidate.get("key_strengths") or []
    picked = _pick_strengths(job, strengths)

    if picked:
        strengths_text = " ".join(f"{s.rstrip('.')}." for s in picked)
    else:
        strengths_text = ("I've reviewed the role and believe my background is a strong fit "
                           "for what you're looking for.")

    company = job.get("company") or "your team"
    title = job.get("title") or "this role"

    note = (
        f"Dear Hiring Team at {company},\n\n"
        f"I'm writing to apply for the {title} position. {strengths_text}\n\n"
        f"I'd welcome the chance to bring this experience to {company}. "
        f"My CV is attached with full details.\n\n"
        f"Best regards,\n{candidate.get('name', '')}\n"
        f"{candidate.get('email', '')} | {candidate.get('phone', '')}"
    )
    return note


def draft_all(ranked_jobs: list[dict], config: dict) -> list[dict]:
    candidate = config["candidate"]
    out = []
    for job in ranked_jobs:
        note = draft_note(job, candidate)
        out.append({**job, "cover_note": note})
    return out


if __name__ == "__main__":
    with open("config.json") as f:
        config = json.load(f)
    sample_job = {"title": "Remote Customer Support Agent", "company": "Acme Travel",
                  "description": "airline ticketing support"}
    print(draft_note(sample_job, config["candidate"]))
