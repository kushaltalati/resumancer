# ATS support

`scripts/ats.py <url>` detects the system and writes `questions.json`:

| ATS | Detect | Questions | Form URL | Filler |
|---|---|---|---|---|
| Greenhouse | `greenhouse.io` hosts, `gh_jid=`, embedded `job_board/js?for=<board>` | public API `boards-api.greenhouse.io/v1/boards/<board>/jobs/<id>?questions=true` (labels, types, options, required) | `job-boards.greenhouse.io/embed/job_app?for=<board>&token=<id>` | full (text, react-select dropdowns, async school search, file upload, education block, country+phone) |
| Lever | `jobs.lever.co/<co>/<id>` | `api.lever.co/v0/postings/<co>/<id>` (posting only) → use `discover` | `jobs.lever.co/<co>/<id>/apply` | discover + fill (labels, selects, file) |
| Ashby | `jobs.ashbyhq.com/<org>/<id>` | `discover` | `…/<id>/application` | discover + fill (best effort) |
| Workable, SmartRecruiters | host | `discover` | the posting's apply page | best effort |
| Workday | `myworkdayjobs.com` | none (account + multi-step) | — | manual: print the answer sheet |
| Unknown | — | `discover` on the apply URL | — | best effort |

## `answers.json` format (consumed by `fill_form.mjs fill`)
```json
{
  "actions": [
    {"type": "text",     "label": "^First Name", "value": "Ada"},
    {"type": "select",   "label": "^Country",    "value": "United Kingdom"},
    {"type": "text",     "label": "^Phone",      "value": "7700900000"},
    {"type": "file",     "label": "Resume",      "path": "/abs/path/resume.pdf"},
    {"type": "search",   "label": "^School",     "typed": "Imperial", "prefer": "Imperial College London"},
    {"type": "select",   "label": "^Degree",     "value": "Master's Degree"},
    {"type": "checkbox", "label": "privacy policy", "value": true},
    {"type": "skip",     "label": "preferred pronouns", "reason": "user decides"}
  ]
}
```
- `label` is a case-insensitive regular expression matched against the field's accessible label.
- `select` types the first characters of `value` and clicks the option whose text starts with `value` (apostrophe variants tolerated). If no option matches it logs `NO MATCH` and moves on; it never presses Enter (Enter can submit a form).
- `search` is for async lists (schools, companies): types `typed`, waits, prefers the option matching `prefer`, else the first option containing `typed`.
- `skip` documents a field left blank on purpose so the final report can list it.
- The script never clicks a button whose text matches /submit|apply now|send application/i. The window stays open until the user closes it.

## `fields.json` (from `fill_form.mjs discover`)
A list of `{label, type, required, options[], name, id}` for every input, select, combobox, file and checkbox found (iframes included for Greenhouse embeds). Build `answers.json` from it when `questions.json` is empty.
