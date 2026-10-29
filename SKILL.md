---
name: resumancer
description: >-
  End-to-end job application pipeline for any user. First run interviews the user (existing resume, work history, GitHub and other profiles) and builds a base profile plus a base report under ~/.resumancer/. Every later run takes a job URL or pasted posting, tailors a one-page resume from the profile, compiles it to PDF, reviews it with a hiring panel, fills the employer's application form in an isolated browser, stops before Submit, and records the application. Use when the user types /resumancer, or asks to apply to a job, tailor a resume for a posting, or set up their application profile.
argument-hint: "<job URL | path to posting | pasted posting> [--no-panel] [--no-fill] [--onboard] [--status]"
user-invocable: true
---

# /resumancer — raise your resume, send it into battle

Everything per user lives in `~/.resumancer/`. Nothing in this skill is specific to one person. Scripts live next to this file in `scripts/`; call them by absolute path (`$SKILL_DIR` below means the directory containing this SKILL.md).

```
~/.resumancer/
  profile.md            the living base profile (facts, experience, projects, skills, answer bank, rules, changelog)
  BASE_REPORT.md        the standing assessment: strengths, gaps, target roles, what to fix before applying
  applications.md       tracker (one row per application)
  applications/<YYYY-MM-DD>-<company>-<role>/   job.md, questions.json, answers.json, resume.tex, resume.pdf, resume.png, panel.md, form.png, log
```

Rules that never bend:
- **Accuracy over everything.** Never invent an employer, title, date, number, skill or result. Every bullet must trace to a line in `profile.md`. If a fact is missing, ask or leave `[ADD: …]`.
- **Shared work stays shared.** "Built with a teammate", "on a team that", "led a 4-person team; teammates built X" — never claim others' work. The profile records who did what; the resume must agree with it.
- **Never click Submit.** The form is filled and left open; the user reviews and submits. Never fill a consent, signature or legal-attestation field with anything but the option the user chose in their answer bank.
- **One page** unless the user's profile says otherwise (academic CVs, senior roles).
- **Ask, don't infer, for route-specific rules** (campus placement vs direct, which email, which grading scale) the first time they come up; store the answer in `profile.md` so it is never asked twice.

## 0. Parse the request

`$ARGUMENTS` may contain:
- a URL → job intake from that page
- a file path → read it as the posting
- pasted text → the posting
- `--onboard` → (re)run onboarding even if a profile exists
- `--status` → print `~/.resumancer/applications.md` and stop
- `--no-panel` → skip the review step; `--no-fill` → stop after the PDF
- nothing → if no profile exists, onboard; else ask for the job URL

Set `SKILL_DIR` to the directory of this file. Run `bash $SKILL_DIR/scripts/setup.sh --check` once per session; if it reports a missing tool, tell the user exactly what to install and continue with whatever still works (no compiler → deliver the .tex and say so; no browser → deliver the answer sheet).

## 1. First run: onboarding (if `~/.resumancer/profile.md` is missing or `--onboard`)

Follow `references/onboarding.md`. In short:
1. Ask, in one message, for: existing resume(s) (file paths, PDFs are fine to Read directly, or pasted text), GitHub username, LinkedIn (pasted profile text or a PDF export, it cannot be fetched), other profiles (portfolio, Codeforces, LeetCode, Kaggle, Google Scholar, Behance…), and the kinds of roles they are targeting.
2. Read every resume given. Run `python3 -I $SKILL_DIR/scripts/github_profile.py <username> --out ~/.resumancer/github.json` and read its markdown summary.
3. Build `~/.resumancer/profile.md` from `templates/PROFILE_TEMPLATE.md`: one entry per job, project, education, achievement, with **provenance** (solo / team / what exactly the user did) and **source** (which resume line, which repo).
4. Confirm the facts that get people rejected, in one question batch: exact grades and scales, dates, legal name, email to use, phone, location, work authorisation per region, earliest start date, notice period, pronouns (or "prefer not to say"), salary expectations if they want them stored. Store them in the answer bank section of `profile.md`.
5. Write `~/.resumancer/BASE_REPORT.md` (see onboarding.md §4): strengths, gaps per target role, honesty flags (team-credit items, in-progress projects, unverifiable numbers), and a short "fix before applying" list.
6. Tell the user where the files are and what to correct. Stop if no job was given; otherwise continue.

Onboarding must never run twice silently: if `profile.md` exists and the user did not pass `--onboard`, skip to §2.

## 2. Job intake

1. Fetch the posting (WebFetch for URLs; read the file or text otherwise). Write `job.md` in a new `~/.resumancer/applications/<date>-<company>-<role>/` folder: title, company, location, deadline, dates, process, requirements (must-have vs nice-to-have), keywords, eligibility rules (citizenship, location of study, graduation window, visa, start date, re-apply policy), apply URL.
2. Run `python3 -I $SKILL_DIR/scripts/ats.py "<url>" --out <folder>/questions.json`. It detects the ATS (Greenhouse, Lever, Ashby, Workday, SmartRecruiters, Workable, unknown), finds the form URL, and for Greenhouse downloads every question with its options. For other ATSs it says whether the browser filler can discover the fields.
3. **Eligibility check before any writing.** Compare the posting's rules with `profile.md`. If a hard rule fails (wrong region, outside graduation window, no work authorisation), say so plainly with the quoted rule, say what the honest answer on the form will be, and ask whether to continue. Do not soften or hide this.
4. Duplicate check: `python3 -I $SKILL_DIR/scripts/tracker.py check "<company>"` warns if the same company was applied to recently (many firms have cool-off rules).

## 3. Tailor the resume

Follow `references/writing_rules.md`.
1. Pick the sections and bullets from `profile.md` that answer the posting's must-haves; order sections by what the reader wants first (projects before experience for a student applying to a systems role, experience first for a professional).
2. Write `resume.tex` from `templates/resume_template.tex` (keep its preamble; change only the body). Use the user's chosen header fields from the answer bank.
3. Compile: `python3 -I $SKILL_DIR/scripts/compile.py <folder>/resume.tex`. It prints JSON with `pages`, `pdf`, `png`. Look at the PNG. If pages > 1, cut in this order: volunteering, oldest or weakest project, third bullet of each entry, coursework line. Recompile until it fits.

## 4. Review

Follow `references/panel.md` (the full seven-reviewer hiring panel is built in: automated screen, hiring manager, day-one manager, rival applicant, CEO, recruiter, teammate; then merge, rebuild, re-screen). Write `resume.md` (plain-text rendering of the .tex) and give reviewers only `resume.md` + `job.md`. Apply every fix that does not need a new fact; list the `[ADD]` questions for the user; recompile; re-screen. Maximum two rounds. Save verdicts to `panel.md`. Skip only with `--no-panel`.

## 5. Fill the application form (unless `--no-fill`)

1. Build `answers.json` (format in `references/ats.md`): one action per form field, values taken from the answer bank, the job folder's resume PDF for the upload, and the posting for job-specific questions. Any question with no stored answer and no safe default → ask the user in one batch (AskUserQuestion) or leave it blank and say so. Consent/attestation fields: fill only with the exact option the user approved in the answer bank; otherwise leave blank.
2. If `questions.json` has no fields (non-Greenhouse), first run discovery: `node $SKILL_DIR/scripts/fill_form.mjs discover --url "<form url>" --out <folder>/fields.json`, read it, then build `answers.json` against the discovered labels.
3. Fill: `node $SKILL_DIR/scripts/fill_form.mjs fill --url "<form url>" --answers <folder>/answers.json --out <folder>` run in the background. It opens an isolated Chrome window, fills everything, uploads the resume, screenshots to `form.png`, and keeps the window open. It has no code path that clicks Submit.
4. Read `form.png` and the log. Report every field it could not fill and every field left blank on purpose.

## 6. Record

1. `python3 -I $SKILL_DIR/scripts/tracker.py add --company "<c>" --role "<r>" --url "<u>" --deadline "<d>" --status filled --folder <folder>`.
2. Append to `profile.md` changelog: date, company, which bullets were newly written (so the next run reuses them), any fact the user confirmed or corrected. Update `BASE_REPORT.md` only if a gap was closed or a new one found.
3. Final message to the user: where the PDF is, what the panel said (one line per reviewer, five worst fixes), what is blank on the form, the eligibility caveats, and the single instruction: review the open window and click Submit yourself.

## Status

`/resumancer --status` prints the tracker and the deadlines in the next 30 days.
