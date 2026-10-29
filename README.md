# resumancer — `/resumancer`

A Claude Code skill that takes a job posting and ends with a tailored, reviewed, compiled resume attached to the employer's application form, filled and waiting for the user to press Submit. Works for any user: the first run builds that user's profile under `~/.resumancer/`.

## Install

```bash
git clone <this repo> ~/resumancer          # or copy the folder
ln -s ~/resumancer ~/.claude/skills/resumancer   # makes /resumancer available in every Claude Code session
bash ~/resumancer/scripts/setup.sh          # installs playwright-core, checks for a LaTeX compiler, Chrome, gh
```

Requirements: Node 18+, Python 3.9+, Google Chrome (or run `npx playwright install chromium` once), a LaTeX engine (`tectonic` or `pdflatex`), optional `gh` for richer GitHub data, optional `pdftoppm` for page previews (macOS falls back to Quick Look).

## Use

```
/resumancer                        # first time: onboarding interview → ~/.resumancer/profile.md + BASE_REPORT.md
/resumancer https://…/jobs/123     # tailor → compile → panel review → fill the form → stop before Submit
/resumancer --status               # tracker + upcoming deadlines
/resumancer --onboard              # redo or extend the profile (new job, new project)
/resumancer <url> --no-fill        # just the resume
```

## What it does, in order

1. Intake: fetches the posting, extracts requirements and eligibility rules, detects the ATS, downloads the form's questions (Greenhouse API; field discovery for others).
2. Eligibility: compares the rules with the profile and says, before any writing, if a hard rule fails.
3. Resume: picks bullets from the profile (never invents), writes a one-page LaTeX resume, compiles, checks page count and preview.
4. Review: a built-in seven-reviewer hiring panel (automated screen, hiring manager, day-one manager, rival applicant, CEO, recruiter, teammate) tries to reject the resume; the mistakes are merged, the resume rebuilt from the same facts, recompiled and re-screened.
5. Form: fills the application in an isolated Chrome window (Greenhouse and Lever tested; Ashby and Workable via field discovery; Workday is manual), uploads the PDF, screenshots, leaves the window open.
6. Record: tracker row, profile changelog.

## What it will never do

- Click Submit, or fill a consent field with anything the user did not approve.
- Claim work that the profile marks as a teammate's.
- Round a grade, invent a number, or add a skill the user has not used.

## Files

```
SKILL.md                  the orchestration instructions Claude follows
templates/PROFILE_TEMPLATE.md, resume_template.tex
references/onboarding.md, writing_rules.md, panel.md, review.md, ats.md
scripts/setup.sh, github_profile.py, ats.py, compile.py, fill_form.mjs, tracker.py
```

## Credits

The hiring-panel procedure is adapted from `/hiring-panel` by Alex Chen (@nocodealex, chen.media), MIT licensed.

## License

MIT.
