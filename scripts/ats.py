#!/usr/bin/env python3
"""Detect the applicant-tracking system behind a job URL and fetch its form questions where a public API exists.
Usage: python3 -I ats.py <url> [--out questions.json]
Output JSON: {ats, board, job_id, form_url, apply_mode: api|discover|manual, questions:[{label,type,required,options[]}], title, location}"""
import json, re, sys, argparse, urllib.request, urllib.parse, html

UA = {"User-Agent": "Mozilla/5.0 (resumancer)"}

def get(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.geturl(), r.read().decode("utf-8", "replace")

def greenhouse_questions(board, job_id):
    _, body = get(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{job_id}?questions=true")
    d = json.loads(body)
    qs = []
    def add(q, section):
        f = q["fields"][0]
        qs.append({"label": html.unescape(q["label"]).strip(), "type": f["type"], "required": bool(q.get("required")),
                   "options": [v["label"] for v in (f.get("values") or [])], "section": section})
    for q in d.get("questions", []): add(q, "application")
    for q in d.get("location_questions", []): add(q, "location")
    for c in d.get("compliance", []) or []:
        for q in c.get("questions", []): add(q, "compliance")
    dq = d.get("demographic_questions")
    if isinstance(dq, dict):
        for q in dq.get("questions", []):
            qs.append({"label": q["label"], "type": "demographic", "required": bool(q.get("required")),
                       "options": [v["label"] for v in q.get("answer_options", [])], "section": "demographic"})
    edu = d.get("education") or {}
    return qs, d.get("title"), (d.get("location") or {}).get("name"), bool(d.get("questions"))

def detect(url):
    out = {"input_url": url, "ats": "unknown", "board": None, "job_id": None, "form_url": None, "apply_mode": "discover", "questions": [], "title": None, "location": None, "notes": []}
    u = urllib.parse.urlparse(url)
    host = u.netloc.lower()
    final_url, page = url, ""
    try:
        final_url, page = get(url)
    except Exception as e:
        out["notes"].append(f"fetch failed: {e}")
    # Many career sites embed the ATS only on an /apply sub-page; probe it when the posting itself shows no ATS marker.
    if not re.search(r"greenhouse|lever\.co|ashbyhq|workday|smartrecruiters|workable", page, re.I):
        for probe in (final_url.rstrip("/") + "/apply", final_url.rstrip("/") + "/apply/"):
            try:
                pu, pp = get(probe)
                if re.search(r"greenhouse|lever\.co|ashbyhq|workday|smartrecruiters|workable", pp, re.I):
                    out["notes"].append(f"ATS marker found on {pu}"); page = page + "\n" + pp; break
            except Exception:
                pass
    m = re.search(r"gh_jid=(\d+)", final_url) or re.search(r"gh_jid=(\d+)", page) or re.search(r"greenhouse\.io/(?:embed/)?job_app\?for=([\w-]+)&token=(\d+)", page)
    board = None
    mb = re.search(r"job_board/js\?for=([\w-]+)", page) or re.search(r"boards\.greenhouse\.io/(?:embed/job_board\?for=)?([\w-]+)", final_url + page)
    if mb: board = mb.group(1)
    if not board:
        # the board token usually sits in the job-board embed script on the /apply sub-page
        base = final_url.split("?")[0].rstrip("/")
        for probe in (base + "/apply", base + "/apply/"):
            try:
                _, pp = get(probe)
                mb2 = re.search(r"job_board/js\?for=([\w-]+)", pp) or re.search(r"job_app\?for=([\w-]+)", pp)
                if mb2: board = mb2.group(1); page += "\n" + pp; out["notes"].append(f"board token found on {probe}"); break
            except Exception:
                pass
    if "greenhouse.io" in host or m or "greenhouse" in page[:200000]:
        out["ats"] = "greenhouse"
        jm = re.search(r"/jobs/(\d+)", final_url) or re.search(r"token=(\d+)", final_url) or (m if m and m.lastindex == 1 else None)
        job_id = (jm.group(1) if jm else None) or (m.group(2) if m and m.lastindex == 2 else None)
        if "greenhouse.io" in host and not board:
            pm = re.search(r"greenhouse\.io/(?:embed/job_app\?for=)?([\w-]+)", final_url)
            if pm: board = pm.group(1)
        if not job_id and board:
            # match the posting title against the board's public job list
            tm = re.search(r"<title>(.*?)</title>", page, re.S | re.I)
            og = re.search(r'property="og:title"\s+content="([^"]+)"', page, re.I)
            title = html.unescape((og.group(1) if og else (tm.group(1) if tm else ""))).strip()
            norm = lambda t: re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()
            try:
                _, jb = get(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=false")
                jobs = json.loads(jb).get("jobs", [])
                nt = norm(title)
                best = [j for j in jobs if norm(j["title"]) and norm(j["title"]) in nt]
                if len(best) > 1:
                    loc_hint = norm(page[:300000])
                    best.sort(key=lambda j: (norm(j["location"]["name"]).split(" ")[0] in nt, len(norm(j["title"]))), reverse=True)
                if best:
                    job_id = str(best[0]["id"]); out["notes"].append(f"job id resolved by title match: {best[0]['title']} ({best[0]['location']['name']})")
            except Exception as e:
                out["notes"].append(f"board job list failed: {e}")
        if not job_id:
            cands = re.findall(r"\b(\d{8,10})\b", page)
            if cands: job_id = max(set(cands), key=cands.count)
        out["board"], out["job_id"] = board, job_id
        if board and job_id:
            try:
                qs, title, loc, has = greenhouse_questions(board, job_id)
                out["questions"], out["title"], out["location"] = qs, title, loc
                out["form_url"] = f"https://job-boards.greenhouse.io/embed/job_app?for={board}&token={job_id}"
                out["apply_mode"] = "api"
                out["notes"].append("standard Greenhouse fields (name, email, phone, resume, education block) are always present even if not listed")
            except Exception as e:
                out["notes"].append(f"greenhouse API failed: {e}")
        else:
            out["notes"].append("could not resolve board/job id; run fill_form.mjs discover on the apply page")
    elif "lever.co" in host:
        out["ats"] = "lever"
        pm = re.match(r"/([^/]+)/([0-9a-f-]{36})", u.path)
        if pm:
            out["board"], out["job_id"] = pm.group(1), pm.group(2)
            out["form_url"] = f"https://jobs.lever.co/{pm.group(1)}/{pm.group(2)}/apply"
            try:
                _, b = get(f"https://api.lever.co/v0/postings/{pm.group(1)}/{pm.group(2)}")
                d = json.loads(b); out["title"] = d.get("text"); out["location"] = (d.get("categories") or {}).get("location")
            except Exception as e:
                out["notes"].append(f"lever API: {e}")
        out["notes"].append("Lever form questions are not exposed by the public API; use discover mode")
    elif "ashbyhq.com" in host:
        out["ats"] = "ashby"; pm = re.match(r"/([^/]+)/([0-9a-f-]{36})", u.path)
        if pm:
            out["board"], out["job_id"] = pm.group(1), pm.group(2)
            out["form_url"] = f"https://jobs.ashbyhq.com/{pm.group(1)}/{pm.group(2)}/application"
    elif "myworkdayjobs.com" in host or "workday" in page[:100000]:
        out["ats"] = "workday"; out["apply_mode"] = "manual"; out["notes"].append("Workday needs an account and a multi-step flow; print the answer sheet and fill manually")
    elif "smartrecruiters.com" in host:
        out["ats"] = "smartrecruiters"; out["form_url"] = url
    elif "workable.com" in host:
        out["ats"] = "workable"; out["form_url"] = url
    else:
        am = re.search(r'href="([^"]*(?:apply|application)[^"]*)"', page, re.I)
        if am:
            out["form_url"] = urllib.parse.urljoin(final_url, html.unescape(am.group(1)))
            out["notes"].append("unknown ATS; guessed the apply link, run discover on it")
    if not out["title"]:
        tm = re.search(r"<title>(.*?)</title>", page, re.S | re.I)
        if tm: out["title"] = html.unescape(tm.group(1)).strip()[:120]
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("url"); ap.add_argument("--out")
    a = ap.parse_args()
    out = detect(a.url)
    if a.out:
        with open(a.out, "w") as f: json.dump(out, f, indent=2)
    print(f"ATS: {out['ats']} | mode: {out['apply_mode']} | board: {out['board']} | job: {out['job_id']}")
    print(f"title: {out['title']} | location: {out['location']}")
    print(f"form: {out['form_url']}")
    for n in out["notes"]: print("note:", n)
    for q in out["questions"]:
        req = "REQ" if q["required"] else "opt"
        print(f"[{req}][{q['type']}] {q['label']}" + (f"  options={q['options'][:8]}{'…' if len(q['options'])>8 else ''}" if q["options"] else ""))
    if a.out: print(f"(saved {a.out})")

if __name__ == "__main__":
    main()
