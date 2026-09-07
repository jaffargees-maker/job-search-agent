"""
Job search dashboard — includes a setup wizard so any applicant can enter
their own details, upload their own resume, and define their own target
roles/keywords, instead of hand-editing config.json.

Run:
    python app.py
Then open http://127.0.0.1:5050

Nothing here changes the underlying safety behaviour: the "Also submit on
Greenhouse" checkbox on the dashboard is exactly main.py's --live-apply flag.
Leave it unchecked and every Greenhouse posting is only filled and
screenshotted, never submitted.
"""
import json
import sys
import threading
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, render_template
from werkzeug.utils import secure_filename

from fetch_sources import fetch_all
from scorer import rank_jobs
from draft_cover_letters import draft_all
from generate_search_links import build_links
from auto_apply_greenhouse import apply_to_job, is_greenhouse_url

# --- Path handling -----------------------------------------------------
# When this file runs as plain Python, "next to this file" is the right
# place for both bundled resources (templates/static) and the applicant's
# own data (config.json, uploads, applications, logs).
#
# When frozen into a Windows .exe by PyInstaller (see job_agent.spec),
# bundled resources are unpacked read-only into a temp folder
# (sys._MEIPASS), which disappears when the app closes — so persistent,
# writable data must live somewhere else: next to the .exe itself, which
# stays put across runs and across app updates.
FROZEN = getattr(sys, "frozen", False)
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
APP_DIR = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parent

REPORTS_DIR = APP_DIR / "applications"
UPLOADS_DIR = APP_DIR / "uploads"
CONFIG_PATH = APP_DIR / "config.json"

REPORTS_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)
(APP_DIR / "logs").mkdir(exist_ok=True)

app = Flask(
    __name__,
    template_folder=str(RESOURCE_DIR / "templates"),
    static_folder=str(RESOURCE_DIR / "static"),
)

_lock = threading.Lock()
STATE = {
    "status": "idle",       # idle | running | done | error
    "step": "",
    "live": False,
    "started_at": None,
    "finished_at": None,
    "error": None,
    "result": None,
}

DEFAULT_CONFIG = {
    "candidate": {
        "name": "", "email": "", "phone": "", "current_location": "",
        "resume_path": "", "key_strengths": [],
    },
    "search": {"on_site_cities": [], "include_remote": True, "country_code": ""},
    "target_titles": [],
    "must_have_keywords": [],
    "nice_to_have_keywords": [],
    "exclude_keywords": [],
    "languages": [],
    "min_match_score_to_report": 35,
    "min_match_score_to_auto_apply": 65,
}


def _set(**kwargs):
    with _lock:
        STATE.update(kwargs)


def _load_config():
    if not CONFIG_PATH.exists():
        return json.loads(json.dumps(DEFAULT_CONFIG))
    with open(CONFIG_PATH) as f:
        return json.load(f)


def _save_config(config):
    CONFIG_PATH.write_text(json.dumps(config, indent=2))


def _is_setup_complete(config) -> bool:
    c = config.get("candidate", {})
    return bool(c.get("name")) and bool(c.get("email")) and bool(c.get("resume_path"))


def _lines(text: str) -> list[str]:
    return [line.strip() for line in (text or "").splitlines() if line.strip()]


def _csv(text: str) -> list[str]:
    return [item.strip() for item in (text or "").split(",") if item.strip()]


def _run_pipeline(live: bool):
    _set(status="running", step="Fetching listings\u2026", live=live,
         started_at=datetime.now().isoformat(), finished_at=None, error=None, result=None)
    try:
        config = _load_config()
        if not _is_setup_complete(config):
            _set(status="error", step="", error="Setup isn't complete yet — fill in the setup form first.",
                 finished_at=datetime.now().isoformat())
            return

        raw_jobs = fetch_all(config.get("target_titles", [])[:5])
        _set(step=f"Scoring {len(raw_jobs)} listings\u2026")

        ranked = rank_jobs(raw_jobs, config)
        _set(step=f"Drafting cover notes for {len(ranked)} matches\u2026")

        drafted = draft_all(ranked, config)

        apply_log = []
        auto_apply_threshold = config.get("min_match_score_to_auto_apply", 65)
        greenhouse_candidates = [j for j in drafted
                                  if j["score"] >= auto_apply_threshold and is_greenhouse_url(j["url"])]
        for i, job in enumerate(greenhouse_candidates, start=1):
            _set(step=f"Checking Greenhouse posting {i}/{len(greenhouse_candidates)}: {job.get('company', '')}\u2026")
            result = apply_to_job(
                job_url=job["url"],
                candidate=config["candidate"],
                resume_path=config["candidate"]["resume_path"],
                cover_note=job["cover_note"],
                live=live,
            )
            apply_log.append({"job": job["title"], "company": job["company"], **result})

        _set(step="Building manual search links\u2026")
        on_site_links = build_links(config)

        today = datetime.now().strftime("%Y-%m-%d")
        report_path = REPORTS_DIR / f"report_{today}.json"
        report = {
            "date": today,
            "matched_jobs": drafted,
            "auto_apply_log": apply_log,
            "manual_search_links": on_site_links,
            "fetched_count": len(raw_jobs),
            "live_apply": live,
        }
        report_path.write_text(json.dumps(report, indent=2))

        _set(status="done", step="Done", finished_at=datetime.now().isoformat(), result=report)
    except Exception as e:
        _set(status="error", step="", error=str(e), finished_at=datetime.now().isoformat())


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/run", methods=["POST"])
def api_run():
    with _lock:
        if STATE["status"] == "running":
            return jsonify({"ok": False, "reason": "already running"}), 409
    config = _load_config()
    if not _is_setup_complete(config):
        return jsonify({"ok": False, "reason": "setup incomplete"}), 400
    live = bool((request.get_json(silent=True) or {}).get("live", False))
    t = threading.Thread(target=_run_pipeline, args=(live,), daemon=True)
    t.start()
    return jsonify({"ok": True})


@app.route("/api/status")
def api_status():
    with _lock:
        return jsonify(dict(STATE))


@app.route("/api/reports")
def api_reports():
    dates = sorted(
        (p.stem.replace("report_", "") for p in REPORTS_DIR.glob("report_*.json")),
        reverse=True,
    )
    return jsonify(dates)


@app.route("/api/reports/<date>")
def api_report(date):
    safe = "".join(c for c in date if c.isalnum() or c == "-")
    path = REPORTS_DIR / f"report_{safe}.json"
    if not path.exists():
        return jsonify({"error": "not found"}), 404
    return jsonify(json.loads(path.read_text()))


@app.route("/api/setup", methods=["GET"])
def api_setup_get():
    config = _load_config()
    return jsonify({"complete": _is_setup_complete(config), "config": config})


@app.route("/api/setup", methods=["POST"])
def api_setup_post():
    config = _load_config()

    form = request.form
    candidate = config.setdefault("candidate", {})
    candidate["name"] = form.get("name", "").strip()
    candidate["email"] = form.get("email", "").strip()
    candidate["phone"] = form.get("phone", "").strip()
    candidate["current_location"] = form.get("current_location", "").strip()
    candidate["key_strengths"] = _lines(form.get("key_strengths", ""))

    resume_file = request.files.get("resume")
    if resume_file and resume_file.filename:
        filename = secure_filename(resume_file.filename)
        dest = UPLOADS_DIR / filename
        resume_file.save(dest)
        candidate["resume_path"] = str(dest)
    # if no new file was uploaded, keep whatever resume_path was already set

    search = config.setdefault("search", {})
    search["on_site_cities"] = _csv(form.get("on_site_cities", ""))
    search["include_remote"] = form.get("include_remote") == "on"
    search["country_code"] = form.get("country_code", "").strip().lower()

    config["target_titles"] = _lines(form.get("target_titles", ""))
    config["must_have_keywords"] = _lines(form.get("must_have_keywords", ""))
    config["nice_to_have_keywords"] = _lines(form.get("nice_to_have_keywords", ""))
    config["exclude_keywords"] = _lines(form.get("exclude_keywords", ""))
    config["languages"] = _csv(form.get("languages", ""))

    try:
        config["min_match_score_to_report"] = int(form.get("min_match_score_to_report", 35))
    except ValueError:
        config["min_match_score_to_report"] = 35
    try:
        config["min_match_score_to_auto_apply"] = int(form.get("min_match_score_to_auto_apply", 65))
    except ValueError:
        config["min_match_score_to_auto_apply"] = 65

    _save_config(config)

    if not candidate.get("name") or not candidate.get("email"):
        return jsonify({"ok": False, "reason": "Name and email are required."}), 400
    if not candidate.get("resume_path"):
        return jsonify({"ok": False, "reason": "A resume file is required."}), 400

    return jsonify({"ok": True, "complete": _is_setup_complete(config)})


if __name__ == "__main__":
    print("Dashboard running at http://127.0.0.1:5050")
    app.run(host="127.0.0.1", port=5050, debug=False, threaded=True)
