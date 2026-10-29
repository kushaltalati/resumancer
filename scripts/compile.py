#!/usr/bin/env python3
"""Compile a .tex resume to PDF, count pages, render a PNG preview.
Usage: python3 -I compile.py <file.tex> [--outdir DIR]
Prints JSON: {ok, engine, pdf, pages, png, log_tail}. Guards pdfTeX-only glyph lines when the engine is XeTeX (tectonic)."""
import json, os, re, shutil, subprocess, sys, zlib, argparse

def count_pages(pdf):
    if shutil.which("pdfinfo"):
        r = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True)
        m = re.search(r"Pages:\s+(\d+)", r.stdout)
        if m: return int(m.group(1))
    d = open(pdf, "rb").read(); n = len(re.findall(rb"/Type\s*/Page[^s]", d))
    for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", d, re.S):
        try: n += len(re.findall(rb"/Type\s*/Page[^s]", zlib.decompress(m.group(1))))
        except Exception: pass
    return n

def render(pdf, outdir):
    png = os.path.join(outdir, os.path.splitext(os.path.basename(pdf))[0] + ".png")
    if shutil.which("pdftoppm"):
        base = png[:-4]
        subprocess.run(["pdftoppm", "-png", "-r", "110", "-f", "1", "-l", "1", "-singlefile", pdf, base], capture_output=True)
        if os.path.exists(png): return png
    if shutil.which("qlmanage"):
        subprocess.run(["qlmanage", "-t", "-s", "1400", "-o", outdir, pdf], capture_output=True)
        q = pdf + ".png"
        if os.path.exists(os.path.join(outdir, os.path.basename(q))):
            os.replace(os.path.join(outdir, os.path.basename(q)), png); return png
    return None

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("tex"); ap.add_argument("--outdir")
    a = ap.parse_args()
    tex = os.path.abspath(a.tex); outdir = os.path.abspath(a.outdir or os.path.dirname(tex))
    build = os.path.join(outdir, ".build"); os.makedirs(build, exist_ok=True)
    src = open(tex, encoding="utf-8").read()
    engine = None
    if shutil.which("tectonic"):
        engine = "tectonic"
        src = src.replace(r"\input{glyphtounicode}", r"\ifdefined\pdfglyphtounicode\input{glyphtounicode}\fi") \
                 .replace(r"\pdfgentounicode=1", r"\ifdefined\pdfgentounicode\pdfgentounicode=1\fi")
    elif shutil.which("latexmk"): engine = "latexmk"
    elif shutil.which("pdflatex"): engine = "pdflatex"
    if not engine:
        print(json.dumps({"ok": False, "error": "no LaTeX engine (install tectonic: brew install tectonic / cargo install tectonic, or TeX Live)"})); sys.exit(2)
    name = os.path.splitext(os.path.basename(tex))[0]
    btex = os.path.join(build, name + ".tex"); open(btex, "w", encoding="utf-8").write(src)
    if engine == "tectonic": cmd = ["tectonic", "-o", build, btex]
    elif engine == "latexmk": cmd = ["latexmk", "-pdf", "-interaction=nonstopmode", "-output-directory=" + build, btex]
    else: cmd = ["pdflatex", "-interaction=nonstopmode", "-output-directory=" + build, btex]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=build)
    bpdf = os.path.join(build, name + ".pdf")
    log = (r.stdout + r.stderr)
    if not os.path.exists(bpdf):
        errs = [l for l in log.splitlines() if l.startswith("!") or "error" in l.lower()][:8]
        print(json.dumps({"ok": False, "engine": engine, "error": "compile failed", "log_tail": errs})); sys.exit(1)
    pdf = os.path.join(outdir, name + ".pdf"); shutil.copyfile(bpdf, pdf)
    pages = count_pages(pdf); png = render(pdf, outdir)
    over = [l for l in log.splitlines() if l.startswith("Overfull")][:5]
    print(json.dumps({"ok": True, "engine": engine, "pdf": pdf, "pages": pages, "png": png, "overfull": over}))

if __name__ == "__main__":
    main()
