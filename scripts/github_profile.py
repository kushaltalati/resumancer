#!/usr/bin/env python3
"""Fetch a public GitHub profile and its most relevant repos as JSON + a markdown summary.
Usage: python3 -I github_profile.py <username> [--out file.json] [--max 15]
Uses `gh` if present (higher rate limit), else the public API via urllib. No tokens stored."""
import json, subprocess, sys, shutil, urllib.request, urllib.error, argparse, base64

def api(path):
    if shutil.which("gh"):
        r = subprocess.run(["gh", "api", path], capture_output=True, text=True)
        if r.returncode == 0:
            return json.loads(r.stdout)
    req = urllib.request.Request("https://api.github.com/" + path, headers={"User-Agent": "resumancer", "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"_error": f"{e.code} {path}"}

def readme_head(owner, repo, lines=25):
    d = api(f"repos/{owner}/{repo}/readme")
    if not isinstance(d, dict) or "content" not in d:
        return ""
    try:
        txt = base64.b64decode(d["content"]).decode("utf-8", "replace")
    except Exception:
        return ""
    return "\n".join(l for l in txt.splitlines()[:lines])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("user"); ap.add_argument("--out"); ap.add_argument("--max", type=int, default=15)
    a = ap.parse_args()
    user = api(f"users/{a.user}")
    if "_error" in user or "login" not in user:
        print(json.dumps({"error": f"user {a.user} not found", "detail": user})); sys.exit(1)
    repos = api(f"users/{a.user}/repos?per_page=100&sort=pushed")
    if not isinstance(repos, list):
        repos = []
    own = [r for r in repos if not r.get("fork")]
    own.sort(key=lambda r: (r.get("stargazers_count", 0), r.get("pushed_at", "")), reverse=True)
    top = own[: a.max]
    out = {
        "login": user["login"], "name": user.get("name"), "bio": user.get("bio"), "company": user.get("company"),
        "location": user.get("location"), "blog": user.get("blog"), "public_repos": user.get("public_repos"),
        "followers": user.get("followers"), "html_url": user.get("html_url"),
        "repos": [],
    }
    for r in top:
        out["repos"].append({
            "name": r["name"], "url": r["html_url"], "description": r.get("description"), "language": r.get("language"),
            "stars": r.get("stargazers_count", 0), "forks": r.get("forks_count", 0), "topics": r.get("topics", []),
            "created_at": r.get("created_at"), "pushed_at": r.get("pushed_at"), "archived": r.get("archived", False),
            "readme_head": readme_head(a.user, r["name"]),
        })
    # merged PRs to other people's repos (public search)
    prs = api(f"search/issues?q=author:{a.user}+is:pr+is:merged+-user:{a.user}&per_page=30")
    out["merged_prs_elsewhere"] = [
        {"title": i["title"], "url": i["html_url"], "repo": i["repository_url"].split("repos/")[-1], "merged_at": i.get("closed_at")}
        for i in (prs.get("items", []) if isinstance(prs, dict) else [])
    ]
    if a.out:
        with open(a.out, "w") as f:
            json.dump(out, f, indent=2)
    # markdown summary
    print(f"# GitHub: {out['login']} ({out.get('name') or ''}) — {out.get('public_repos')} public repos, {out.get('followers')} followers")
    if out.get("bio"): print(f"Bio: {out['bio']}")
    print("\n## Top own repos")
    for r in out["repos"]:
        print(f"- **{r['name']}** ({r['language'] or '?'}, ★{r['stars']}, pushed {str(r['pushed_at'])[:10]}) — {r['description'] or 'no description'} — {r['url']}")
    if out["merged_prs_elsewhere"]:
        print("\n## Merged PRs in other repos")
        for p in out["merged_prs_elsewhere"]:
            print(f"- {p['repo']}: {p['title']} ({str(p['merged_at'])[:10]}) — {p['url']}")
    if a.out:
        print(f"\n(saved {a.out})")

if __name__ == "__main__":
    main()
