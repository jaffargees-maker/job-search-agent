# Job Search Agent

Finds jobs matching your background, scores and ranks them, drafts a
tailored cover note per match, safely auto-applies where that's genuinely
possible (Greenhouse only, with your review), and gives you ready-to-click
search links everywhere else. Runs entirely on your own computer.

## Two ways to run this, depending on who you are

**If you're the applicant** — someone handed you a file called
**`JobSearchAgentSetup.exe`**: skip to
["For applicants: installing JobSearchAgentSetup.exe"](#for-applicants-installing-jobsearchagentsetupexe)
below. You don't need Python, and you don't need anything in this repo
except that one file.

**If you're packaging this for others** (or just want a single .exe
instead of the `.bat` + Python route) — see
["For packagers: building the .exe"](#for-packagers-building-the-exe)
below. This is a one-time step *you* run once, on a Windows PC, to
produce that `JobSearchAgentSetup.exe` file. It's not something every
applicant repeats.

**If you're fine using Python directly** — `install_windows.bat` /
`start_dashboard.bat` (below) still work exactly as before and need no
build step at all.

---

## For applicants: installing JobSearchAgentSetup.exe

1. Double-click **`JobSearchAgentSetup.exe`**.
   - If Windows shows a blue "Windows protected your PC" warning, click
     **"More info"** then **"Run anyway"** — expected for any unsigned
     installer, not a sign of a problem.
   - No admin password is needed; it installs to your own user folder.
2. Leave "Launch Job Search Agent now" checked and click **Finish**.
   - The very first launch downloads one browser component used for
     Greenhouse auto-apply (a few minutes, needs internet — only happens
     once). Everything else works immediately.
   - Your browser opens automatically to `http://127.0.0.1:5050`.
3. Fill in the **Passenger details** form: your name, email, phone,
   resume (PDF), the roles you're targeting, your current location, the
   cities you'd consider on-site work in, and your country. Everything
   stays on your computer — nothing is uploaded anywhere else.
4. Click **Save details**, then **Run search**.

A desktop and Start Menu shortcut are created, so next time just open
"Job Search Agent" like any other app — no re-installing.

### Changing your location or other details later

Click **"Passenger details"** in the top-right of the dashboard any time
to update your resume, target roles, current location, target cities, or
country — nothing is locked in after the first run.

---

## For packagers: building the .exe

PyInstaller (which makes the .exe) only builds for the operating system
it's running on, so this step has to happen **on an actual Windows
machine** — it can't be cross-compiled from Mac/Linux. Two ways to do
that:

### Option A — automatically, via GitHub Actions (no Windows PC needed)

This repo includes `.github/workflows/build-windows-installer.yml`,
which builds the installer on GitHub's own Windows runners.

1. Push this folder to a GitHub repository.
2. It builds automatically on every push to `main`, or you can trigger
   it manually from the repo's **Actions** tab → *Build Windows
   installer* → **Run workflow**.
3. When it finishes, open that run and download **`JobSearchAgentSetup`**
   from the *Artifacts* section at the bottom — that's
   `JobSearchAgentSetup.exe`, ready to hand to applicants.
4. For a stable, permanent download link instead of digging through
   Actions runs each time: push a version tag, e.g.
   ```
   git tag v1.0
   git push origin v1.0
   ```
   This publishes a GitHub Release with `JobSearchAgentSetup.exe`
   attached, at a URL that doesn't change.

### Option B — manually, on a Windows PC

1. Get this whole `job_agent_product` folder onto a Windows PC.
2. Double-click **`BUILD_INSTALLER.bat`** once.
   - Installs Python build dependencies into a local `build_venv`
     (doesn't touch your system Python).
   - Runs PyInstaller to produce `dist\JobSearchAgent.exe`.
   - If [Inno Setup](https://jrsoftware.org/isinfo.php) (free) is
     installed, also produces `Output\JobSearchAgentSetup.exe` — the
     single file to hand to applicants.
   - If Inno Setup isn't installed, you still get the standalone
     `dist\JobSearchAgent.exe`, which applicants can run directly (it
     creates its own `uploads`/`applications`/`logs` folders next to
     itself) — you just won't get the guided installer/shortcuts/
     uninstaller around it.

Either way, distribute `JobSearchAgentSetup.exe` to applicants — that's
the only file they need.

---

## Quick start without building anything (Python route)

1. Extract this whole folder anywhere on your computer.
2. Double-click **`install_windows.bat`**.
   - If Windows shows a blue "Windows protected your PC" warning, click
     **"More info"** then **"Run anyway"** — this happens for any
     unsigned script, it's expected.
   - The first run installs Python packages and a browser component, so
     it can take a few minutes. You'll see progress in the black window.
   - When it's done, your browser opens automatically to
     `http://127.0.0.1:5050`.
3. Fill in the **Passenger details** form that appears: your name, email,
   phone, resume (PDF), the roles you're targeting, and keywords that
   describe what you're looking for. Everything here stays on your
   computer — nothing is uploaded anywhere else.
4. Click **Save details**, then **Run search**.

That's it — you'll see matched jobs, drafted cover notes, and manual
search links for the sites that don't allow automation (LinkedIn, Indeed,
Rozee.pk, etc).

### Running it again later

Once it's installed, you don't need `install_windows.bat` again — just
double-click **`start_dashboard.bat`** instead. It's faster since it skips
the install steps.

### Editing your details later

Click **"Passenger details"** in the top-right of the dashboard any time
to update your resume, target roles, or keywords.

## What's actually automatic vs. what isn't

| Source | What happens |
|---|---|
| RemoteOK, Arbeitnow, WeWorkRemotely | Fetched automatically via free, public, no-login APIs. |
| Greenhouse-hosted postings scoring above your auto-apply threshold | Form filled, resume uploaded, cover note inserted, screenshotted. **Only submitted if you tick "Also submit on Greenhouse"** — off by default. If a posting has custom screening questions, it stops and flags for your review instead of guessing answers. |
| LinkedIn, Indeed, Rozee.pk, etc. | **Never auto-applied.** These sites prohibit scraping/automation in their Terms of Service and detect bots — the agent instead builds pre-filtered search links for you to click through. |

This is a deliberate choice: automatic only where it's actually safe for
your accounts and doesn't risk sending out low-quality, guessed answers.

## Running it automatically every day (optional)

1. Press the Windows key, type `Task Scheduler`, open it.
2. Click **"Create Basic Task..."**, name it, set a daily trigger and a
   time.
3. For the action, choose **"Start a program"** and browse to
   **`run_daily_search.bat`** inside this folder.
4. Finish. It'll run quietly in the background at that time each day,
   writing to `logs\cron.log` and `applications\report_<date>.json`.

By default this only fills and screenshots Greenhouse applications, never
submits. To let it actually submit once you trust the matches, open
`run_daily_search.bat` in Notepad and change `main.py` to
`main.py --live-apply`.

## Your data

- `config.json` — your details and search preferences, created after you
  fill in the setup form. You can open and edit it directly if you'd
  rather not use the form.
- `uploads/` — your uploaded resume.
- `applications/` — one JSON report per day you've run it.
- `logs/` — screenshots of filled Greenhouse forms, plus the daily cron
  log if you set up automation.

Nothing in this folder is sent anywhere except the job-fetching APIs
(RemoteOK, Arbeitnow, WeWorkRemotely) and, if you enable it, the specific
Greenhouse posting you're applying to.

## Troubleshooting

- **"Python was not found"** when running the installer — install Python
  from https://www.python.org/downloads/windows/ and make sure you check
  **"Add python.exe to PATH"** during setup, then run the installer again.
- **Dashboard won't load in the browser** — check the black window is
  still open and says `Dashboard running at http://127.0.0.1:5050`; if
  it's closed, run `start_dashboard.bat` again.
- **Very few matches** — RemoteOK and Arbeitnow skew toward tech roles,
  so daily volume will vary by field. Try loosening your keywords in
  Passenger details, or lowering "Min score to list a match".
