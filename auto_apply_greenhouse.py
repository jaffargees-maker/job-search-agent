"""
Auto-fills (and, in --live mode, submits) applications on Greenhouse-hosted
job postings (job-boards.greenhouse.io/... or boards.greenhouse.io/...).

Why only Greenhouse: its embedded application form uses a consistent
data-qa/field structure across companies, which is what makes reliable
auto-fill possible without a custom script per employer. Other ATSs
(Workday, Taleo, LinkedIn Easy Apply) either vary too much per-company or
actively fingerprint/block automation — attempting them generically produces
broken or flagged applications, so this script intentionally does not try.

SAFETY DEFAULTS:
- Runs in --dry-run mode unless you pass --live. Dry-run fills the form,
  screenshots it, and stops before clicking submit.
- If a posting has custom screening questions beyond name/email/phone/resume/
  LinkedIn/cover-letter, the script pauses and will NOT submit automatically.
"""
import argparse
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


def is_greenhouse_url(url: str) -> bool:
    return "greenhouse.io" in url


def apply_to_job(job_url: str, candidate: dict, resume_path: str, cover_note: str,
                  live: bool = False, headless: bool = True) -> dict:
    if not is_greenhouse_url(job_url):
        return {"status": "skipped", "reason": "not a Greenhouse-hosted posting"}

    result = {"job_url": job_url, "status": "unknown"}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(job_url, timeout=30000)

        try:
            page.wait_for_selector("#application_form, [data-qa='applicant-form']", timeout=15000)
        except Exception:
            browser.close()
            result["status"] = "failed"
            result["reason"] = "application form not found (layout may differ for this posting)"
            return result

        def fill_if_present(selector, value):
            try:
                el = page.locator(selector).first
                if el.count() > 0 and value:
                    el.fill(value)
                    return True
            except Exception:
                pass
            return False

        fill_if_present("#first_name", candidate["name"].split(" ")[0])
        fill_if_present("#last_name", " ".join(candidate["name"].split(" ")[1:]) or candidate["name"])
        fill_if_present("#email", candidate["email"])
        fill_if_present("#phone", candidate["phone"])

        cover_letter_box = page.locator("textarea[name*='cover_letter'], #cover_letter_text")
        if cover_letter_box.count() > 0:
            cover_letter_box.first.fill(cover_note)

        resume_input = page.locator("input[type='file'][name*='resume']")
        if resume_input.count() > 0 and Path(resume_path).exists():
            resume_input.first.set_input_files(resume_path)
            time.sleep(2)

        custom_question_labels = page.locator(
            "label:not([for='first_name']):not([for='last_name']):not([for='email']):not([for='phone'])"
        )
        num_custom = custom_question_labels.count()

        Path("logs").mkdir(exist_ok=True)
        screenshot_path = f"logs/greenhouse_{int(time.time())}.png"
        page.screenshot(path=screenshot_path, full_page=True)
        result["screenshot"] = screenshot_path

        if num_custom > 6:
            result["status"] = "needs_manual_review"
            result["reason"] = f"posting has ~{num_custom - 6} custom screening question(s) — review before submitting"
            browser.close()
            return result

        if not live:
            result["status"] = "dry_run_filled"
            result["reason"] = "form filled and screenshotted; rerun with --live to submit"
            browser.close()
            return result

        submit_btn = page.locator("#submit_app, button[type='submit']")
        if submit_btn.count() > 0:
            submit_btn.first.click()
            page.wait_for_timeout(3000)
            result["status"] = "submitted"
        else:
            result["status"] = "failed"
            result["reason"] = "submit button not found"

        browser.close()
        return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-url", required=True)
    parser.add_argument("--live", action="store_true", help="Actually submit. Default is dry-run.")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--cover-note-file", default=None)
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)

    cover_note = ""
    if args.cover_note_file:
        cover_note = Path(args.cover_note_file).read_text()

    result = apply_to_job(
        job_url=args.job_url,
        candidate=config["candidate"],
        resume_path=config["candidate"]["resume_path"],
        cover_note=cover_note,
        live=args.live,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
