#!/usr/bin/env bash
# One-time setup / environment check for the /resumancer skill.
#   bash setup.sh          install node deps and report tools
#   bash setup.sh --check  report only
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
ok=0; miss=()
have() { command -v "$1" >/dev/null 2>&1; }
echo "== tools =="
for t in node npm python3; do if have $t; then echo "  $t: $($t --version 2>&1 | head -1)"; else echo "  $t: MISSING"; miss+=($t); fi; done
if have tectonic; then echo "  latex: tectonic"; elif have pdflatex; then echo "  latex: pdflatex"; else echo "  latex: MISSING (brew install tectonic | cargo install tectonic | TeX Live)"; miss+=(latex); fi
if have pdftoppm; then echo "  preview: pdftoppm"; elif have qlmanage; then echo "  preview: qlmanage (macOS)"; else echo "  preview: none (PNG preview skipped)"; fi
if have gh; then echo "  gh: yes"; else echo "  gh: no (GitHub data via public API, lower rate limit)"; fi
if [ -d "/Applications/Google Chrome.app" ] || have google-chrome || have google-chrome-stable || have chromium; then echo "  chrome: yes"; else echo "  chrome: not found — run: cd $DIR && npx playwright-core install chromium  (or install Google Chrome)"; fi
if [ "${1:-}" != "--check" ] && have npm; then
  echo "== installing node deps in $DIR =="
  (cd "$DIR" && npm install --no-audit --no-fund --loglevel=error) && echo "  playwright-core installed" || echo "  npm install FAILED"
fi
if [ -d "$DIR/node_modules/playwright-core" ]; then echo "  playwright-core: ok"; else echo "  playwright-core: MISSING (run: cd $DIR && npm install)"; miss+=(playwright-core); fi
mkdir -p "$HOME/.resumancer/applications"
echo "== state dir: $HOME/.resumancer =="
[ -f "$HOME/.resumancer/profile.md" ] && echo "  profile.md: present" || echo "  profile.md: absent (first run will onboard)"
if [ ${#miss[@]} -gt 0 ]; then echo "MISSING: ${miss[*]}"; exit 1; fi
echo "all good"
