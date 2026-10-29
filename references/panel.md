# The hiring panel (built in)

Seven reviewers try to reject the resume; then it is rebuilt with every mistake fixed. Never flatter the resume. Adapted, with thanks, from `/hiring-panel` by Alex Chen (@nocodealex, chen.media, MIT).

Inputs: `resume.md` (a plain-text rendering of the current `resume.tex`: same words, same order, no LaTeX) and `job.md`. Write both into the application folder before starting. Reviewers get ONLY these two files, never the profile, never each other's notes.

## Round 1 — seven sub-agents, all at once (one message, seven Agent calls)

**1. The automated screen** — the system that decides whether a human ever sees this resume. Checks in order: (a) readable top to bottom (columns, tables, text in images, odd section names)? (b) job titles, employers, dates clear? (c) which of the posting's key skills and terms appear, which are missing (give a present/missing table)? (d) contact details present, length sensible, no filler. Answers PASS or REJECT, then at most five reasons, each quoting the line it is about. Under 250 words.

**2. The hiring manager** — decides whether this person gets an interview. Answers INTERVIEW or NO; what decided it in the first ten seconds; the questions they would ask in the interview, especially anything that smells over-claimed or credit-by-proximity; the three weakest lines, quoted. Under 250 words.

Five readers, each alone, each under 120 words: HIRE, MAYBE or PASS; the one line that hurt most (quoted); two more problems.
**3. The day-one hiring manager** — reads for one thing: can this person do the job on day one?
**4. Another applicant** — a strong rival for the same posting; where is this resume weaker than theirs?
**5. The CEO** — reads for impact only: what did this person change, and by how much? Which numbers are real outcomes, which are vanity or belong to someone else?
**6. The recruiter** — 30 seconds, 100 resumes today; reads the top third only.
**7. The teammate** — would sit next to this person: do they share credit, communicate, review code, take feedback, finish things?

Prompt skeleton for each (fill the role text from above):
```
Read the resume at <folder>/resume.md and the job at <folder>/job.md. You are <role>. <role instructions>. Never flatter. Answer in the required format.
```

## Merge
One numbered list of mistakes, worst first, duplicates merged. For each: the quoted line, why it gets rejected, which of the seven flagged it. Keep every "credit belongs to someone else" finding at the top: it is the one that fails a reference check.

## Rebuild
Fix every numbered mistake using only facts already in the resume or in `profile.md`. Allowed: reorder, reword, cut, add dates/scales/links, add posting keywords that the profile supports, move a number to the user's own part, name what teammates built. Not allowed: new facts. A missing fact becomes `[ADD: …]` in the .tex and a question for the user. Recompile (`compile.py`), check one page.

## Round 2 — re-screen
Run reviewer 1 again on the rebuilt `resume.md`. Report before/after. If it still REJECTs for something fixable, fix and re-screen once more. Maximum two full rounds in total.

## Output
`<folder>/panel.md`: the seven verdicts, the merged mistake list, the before/after screen verdict, and the open `[ADD]` questions. The user sees, in chat: one line per reviewer, the five worst mistakes, before/after, and the file path. A PDF with any `[ADD]` left in it is never attached to a form.

## If the resume is strong
Say so, and say which reviewer came closest to rejecting it and why it still held.

This is a structured second opinion produced by language models. It does not guarantee an interview and is not career or legal advice.
