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
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=False,
        )
        if result.returncode == 0:
            marker.parent.mkdir(exist_ok=True)
            marker.write_text("ok")
        else:
            print("\nCouldn't download the browser component automatically.")
            print("Greenhouse auto-apply will be unavailable until you run:")
            print("  playwright install chromium")
            print("Everything else (search, scoring, cover notes, manual")
            print("search links) still works.\n")
    except Exception as e:
        print(f"\nBrowser setup skipped ({e}). Auto-apply will be unavailable")
        print("until this is resolved; everything else still works.\n")


def _open_browser_when_ready(url: str):
    # Small delay so Flask has bound the port before the browser requests it.
    time.sleep(1.5)
    try:
        webbrowser.open(url)
    except Exception:
        pass
    print(f"\nIf your browser didn't open automatically, go to:\n  {url}\n")


def main():
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
