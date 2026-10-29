# Onboarding (first run, or `/resumancer --onboard`)

Goal: a `~/.resumancer/profile.md` the user trusts, and a `BASE_REPORT.md` that says honestly where they stand. Spend the user's time on facts, not on prose.

## 1. Ask once, in one message
- Existing resume(s): file paths (PDF, .docx, .tex, .md all fine; Read PDFs directly) or pasted text. Older variants are useful too: they carry bullets already approved by the user.
- GitHub username (public data is fetched by `scripts/github_profile.py`).
- LinkedIn: ask them to paste the profile text or export the PDF (Settings → Save to PDF). It cannot be fetched.
- Other profiles that matter for their field: portfolio, Codeforces/LeetCode/Kaggle, Google Scholar, Behance/Dribbble, Stack Overflow, personal site.
- Target roles: 2–4 role families, seniority, geographies, remote or not, and anything they want to avoid.
- Route rules: do any applications go through a placement cell / career office with its own resume rules? If yes, ask for those rules verbatim and store them in profile §0.

## 2. Build the profile
- Read every resume. For each job, project, education entry, achievement: record the exact title/dates/numbers as written and mark `source: <file>`.
- Run `python3 -I $SKILL_DIR/scripts/github_profile.py <user> --out ~/.resumancer/github.json` and read the printed summary: top repos, languages, stars, recency, README first lines. Add repos that are not on any resume as candidate projects (mark `[not yet on a resume]`).
- For every item that could be shared work (any project with other contributors, any team metric), ask: "Solo, or team? If team, what was your part?" Store the answer as provenance. This is the single biggest source of rejected resumes and failed reference checks.
- For every number, ask how it was measured if the resume does not say. Unverifiable numbers go to §12 (open accuracy items).
- Skills: list only what appears in a resume, a repo, or the user's answer. Build the "never list" from tools they mention wanting to learn.

## 3. Confirm the rejection-critical facts (one AskUserQuestion batch)
Grades with scale, dates, legal name, email(s) and when each is used, phone, location, work authorisation per region they target, visa sponsorship need, earliest start date, notice period, graduation timing, years of professional experience (as they want it counted), pronouns, salary expectation (optional), which consents the filler may tick without asking (privacy policy yes/no; proctoring/AI-use attestations: ask each time by default).

## 4. Write BASE_REPORT.md
Short, honest, in this order:
1. **Positioning**: one paragraph per target role family: what leads, what supports.
2. **Strengths**: the 5 items a reader would remember, each tied to evidence.
3. **Gaps per role family**: what postings in that family ask for that the profile cannot show; what would close each gap (a project, a certification, a number to measure).
4. **Honesty flags**: shared-credit items and how they must be worded; in-progress work; numbers without a measurement.
5. **Fix before applying**: concrete to-dos (confirm a grade, move code to a standalone repo, finish a README, get a PR merged).
6. **Default resume skeleton** per role family: section order and which entries go in.

Update this file only when something changes; `profile.md` is the living record.

## 5. End of onboarding
Tell the user: the two file paths, the top 3 things to correct, and that `/resumancer <url>` now works. If a URL was given with the first run, continue straight into intake.
