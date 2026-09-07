"""
Entry point used to build JobSearchAgent.exe (see job_agent.spec).

Not meant to be run any differently from `python app.py` conceptually —
it just adds the bits a double-clickable desktop app needs that a
developer running from a terminal doesn't:

  1. Make sure relative paths (config.json, uploads/, applications/,
     logs/) resolve next to the .exe, not into PyInstaller's temp
     extraction folder.
  2. Make sure the Chromium browser Playwright needs for Greenhouse
     auto-apply is installed, downloading it once on first run if not.
  3. Open the user's default browser to the dashboard automatically.
  4. Keep the console window open with readable status instead of
     dumping a stack trace and vanishing if something goes wrong.
"""
import os
import sys
import threading
import time
import webbrowser
from pathlib import Path


def _app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _ensure_chromium():
    """Install Playwright's bundled Chromium the first time the app runs.

    Only needed for the optional Greenhouse auto-apply feature — the job
    search, scoring, cover-note drafting, and manual search links all
    work without it.

    IMPORTANT: this must invoke Playwright's actual driver executable,
    never `sys.executable`. In a normal `python app.py` run, sys.executable
    is python.exe and `-m playwright` works. But once frozen into
    JobSearchAgent.exe by PyInstaller, sys.executable *is*
    JobSearchAgent.exe — there is no separate Python interpreter bundled
    inside it. Calling `subprocess.run([sys.executable, "-m", "playwright", ...])`
    in that case just relaunches JobSearchAgent.exe itself, which runs
    this same first-run check again, which relaunches it again... an
    infinite loop of windows. compute_driver_executable() below returns
    Playwright's own bundled Node-based driver instead, sidestepping
    sys.executable entirely.
    """
    marker = _app_dir() / "logs" / ".chromium_ready"
    if marker.exists():
        return
    print("First-time setup: downloading the browser component used for")
    print("Greenhouse auto-apply. This can take a few minutes and needs")
    print("an internet connection. Everything else in the app works")
    print("without it, so this only happens once.\n")
    try:
        import subprocess
        from playwright._impl._driver import compute_driver_executable, get_driver_env
        node_exe, cli_path = compute_driver_executable()
        result = subprocess.run(
            [node_exe, cli_path, "install", "chromium"],
            env=get_driver_env(),
        )
        if result.returncode == 0:
            marker.parent.mkdir(exist_ok=True)
            marker.write_text("ok")
        else:
            print("\nCouldn't download the browser component automatically.")
            print("Greenhouse auto-apply will be unavailable until this is")
            print("resolved. Everything else (search, scoring, cover notes,")
            print("manual search links) still works.\n")
            # Don't retry every launch if it failed — avoid nagging on a
            # machine with no internet access. Mark as "attempted" so the
            # rest of the app remains usable; auto-apply will simply error
            # per-job instead of blocking the whole dashboard.
            marker.parent.mkdir(exist_ok=True)
            marker.write_text("failed")
    except Exception as e:
        print(f"\nBrowser setup skipped ({e}). Auto-apply will be unavailable")
        print("until this is resolved; everything else still works.\n")
        marker.parent.mkdir(exist_ok=True)
        marker.write_text("failed")


def _open_browser_when_ready(url: str):
    # Small delay so Flask has bound the port before the browser requests it.
    time.sleep(1.5)
    try:
        webbrowser.open(url)
    except Exception:
        pass
    print(f"\nIf your browser didn't open automatically, go to:\n  {url}\n")


def main():
    # Safety net: if anything ever spawns this exe as a subprocess of
    # itself again (the exact bug just fixed above), refuse to run rather
    # than silently looping. A real launch never sets this variable.
    if os.environ.get("JOB_SEARCH_AGENT_CHILD") == "1":
        print("JobSearchAgent.exe was launched as a child of itself, which")
        print("should never happen. Refusing to start to avoid a loop.")
        input("Press Enter to exit...")
        return
    os.environ["JOB_SEARCH_AGENT_CHILD"] = "1"

    app_dir = _app_dir()
    # Every module in this project (auto_apply_greenhouse.py's "logs/",
    # main.py's "applications/", etc.) uses paths relative to the current
    # working directory, so anchor that here once, at the top.
    os.chdir(app_dir)
    (app_dir / "logs").mkdir(exist_ok=True)
    (app_dir / "uploads").mkdir(exist_ok=True)
    (app_dir / "applications").mkdir(exist_ok=True)

    print("============================================")
    print("  Job Search Agent")
    print("============================================\n")

    _ensure_chromium()

    import app as flask_app_module  # local import: after chdir/env setup

    url = "http://127.0.0.1:5050"
    threading.Thread(target=_open_browser_when_ready, args=(url,), daemon=True).start()

    print(f"Dashboard running at {url}")
    print("Leave this window open while you use the dashboard.")
    print("Close this window (or press Ctrl+C) to stop it.\n")

    flask_app_module.app.run(host="127.0.0.1", port=5050, debug=False, threaded=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        print("\nJob Search Agent hit an error and needs to close. If this")
        print("keeps happening, please share the message above.")
        input("Press Enter to exit...")
