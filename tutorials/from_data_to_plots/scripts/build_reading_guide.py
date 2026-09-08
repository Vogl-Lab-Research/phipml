#!/usr/bin/env python3
"""Build a self-contained HTML reading edition; requires Python-Markdown.

Optional documentation utility; not needed to fit models or plot results.
Install with: python -m pip install Markdown
"""
from __future__ import annotations

import base64
import html
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = [
    ("walkthrough", "Walkthrough", ROOT / "README.md"),
    ("model-config", "Model config", ROOT / "docs/MODEL_CONFIG.md"),
    ("hyperparameters", "Hyperparameters", ROOT / "docs/HYPERPARAMETERS.md"),
    ("plot-config", "Plot config", ROOT / "docs/PLOTTING_CONFIG.md"),
    ("reference-run", "Verified results", ROOT / "reports/REFERENCE_RUN.md"),
]

CSS = """
:root{--ink:#213547;--muted:#536875;--accent:#176b73;--line:#dce7e8;--paper:#fff;--bg:#f1f5f5}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:22px}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.68 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
aside{position:fixed;inset:0 auto 0 0;width:252px;padding:32px 24px;background:#12343c;color:#ebf3f3;overflow:auto}
aside .brand{font-size:32px;letter-spacing:-1px;font-weight:800}aside .sub{font-size:13px;color:#b8d2d5;margin:4px 0 28px}aside a{display:block;color:#d8ecee;text-decoration:none;padding:9px 10px;border-radius:5px;font-size:14px}aside a:hover,aside a.current{background:#24515b;color:#fff}aside small{display:block;font-size:12px;color:#b8d2d5;margin-top:30px}aside button{margin-top:18px;background:#275661;color:white;border:1px solid #50747c;border-radius:5px;padding:9px 13px;cursor:pointer}
main{max-width:1380px;margin:0 auto 0 252px;padding:38px 4vw 70px}.hero{padding:35px 38px;background:#dceceb;border-top:5px solid var(--accent);border-radius:7px;margin-bottom:30px}.eyebrow{font-size:12px;font-weight:800;letter-spacing:1.5px;color:var(--accent);text-transform:uppercase}.hero h1{font-size:42px;line-height:1.1;margin:13px 0 14px;letter-spacing:-1.5px}.hero p{max-width:760px;margin:0}.badges{display:flex;flex-wrap:wrap;gap:8px;margin-top:20px}.badges span{font-size:12px;line-height:1.3;padding:7px 10px;border:1px solid #94b7b9;border-radius:4px;background:#f2f9f8}
section{background:var(--paper);padding:30px 36px 45px;border:1px solid var(--line);border-radius:7px;margin-bottom:28px;overflow:hidden}h1,h2,h3{line-height:1.25;color:#173740}section h1{font-size:31px;margin-top:0;padding-bottom:18px;border-bottom:2px solid var(--line);letter-spacing:-.6px}h2{font-size:24px;margin:38px 0 14px;letter-spacing:-.3px}h3{font-size:19px;margin:28px 0 12px}p{margin:12px 0}a{color:#166b87;text-underline-offset:3px}strong{font-weight:700}blockquote{margin:22px 0;padding:10px 20px;border-left:4px solid var(--accent);background:#eef7f6}blockquote p{margin:7px 0}img{max-width:100%;height:auto;display:block;margin:22px auto;border:1px solid #e2e7e9;border-radius:4px}.table-wrap{overflow-x:auto;margin:20px 0}table{border-collapse:collapse;font-size:14px;line-height:1.5;width:100%;table-layout:auto}th{background:#e5eff0;text-align:left;color:#173740}td,th{padding:11px 13px;border:1px solid #dfe7e9;vertical-align:top}tr:nth-child(even) td{background:#f7f9fa}td:first-child{min-width:135px}td{overflow-wrap:anywhere}code{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:.86em;background:#edf2f4;border-radius:3px;padding:2px 4px;overflow-wrap:anywhere}pre{position:relative;padding:20px;overflow:auto;background:#142d38;color:#e5f0f1;border-radius:6px;line-height:1.5;font-size:14px;margin:20px 0}pre code{background:none;padding:0;font-size:inherit;white-space:pre;overflow-wrap:normal}pre .copy{position:absolute;top:7px;right:8px;color:#c6dce0;background:#284651;border:1px solid #48636d;border-radius:4px;font-size:11px;padding:4px 8px;cursor:pointer}li{margin:7px 0}.footer{font-size:13px;color:var(--muted);text-align:center;margin:25px 0}
@media(max-width:1000px){aside{position:static;width:auto;padding:20px}aside nav{display:flex;flex-wrap:wrap}aside .sub{margin:0 0 12px}aside small,aside button{display:none}main{margin:0;padding:20px}section{padding:22px}.hero{padding:25px}.hero h1{font-size:34px}}
@media print{body{background:white;font-size:10pt;line-height:1.45}aside,.copy,.footer{display:none!important}main{margin:0;padding:0;max-width:none}.hero{padding:18px;margin-bottom:15px}.hero h1{font-size:26pt}section{border:0;padding:0;margin:0;overflow:visible;break-before:page}section h1{font-size:22pt}h2{font-size:16pt;break-after:avoid}h3{font-size:13pt;break-after:avoid}pre{white-space:pre-wrap;font-size:8pt;background:#f2f4f5;color:#142d38;overflow:visible;break-inside:auto}pre code{white-space:pre-wrap;overflow-wrap:anywhere}.table-wrap{overflow:visible}table{font-size:8.5pt}tr{break-inside:avoid}img{max-height:235mm;object-fit:contain;break-inside:avoid}a{color:inherit}thead{display:table-header-group}@page{size:A4;margin:16mm}}
"""


def main() -> None:
    sections, toc = [], []
    mapping = {str(path.relative_to(ROOT)): slug for slug, _, path in SECTIONS}
    for slug, label, path in SECTIONS:
        content = markdown.markdown(path.read_text(), extensions=["extra", "toc", "sane_lists"])
        content = re.sub(r'id="([^"]+)"', lambda m: f'id="{slug}-{m[1]}"', content)
        content = re.sub(r'href="#([^"]+)"', lambda m: f'href="#{slug}-{m[1]}"', content)
        def link(match: re.Match) -> str:
            value = html.unescape(match[1])
            if value.startswith(("#", "http:", "https:", "mailto:")):
                return match[0]
            resolved = (path.parent / value).resolve()
            try:
                relative = str(resolved.relative_to(ROOT))
            except ValueError:
                return match[0]
            return f'href="#{mapping[relative]}"' if relative in mapping else match[0]
        content = re.sub(r'href="([^"]+)"', link, content)
        def embed(match: re.Match) -> str:
            source = path.parent / html.unescape(match[1])
            if not source.is_file():
                raise FileNotFoundError(source)
            mime = "image/png" if source.suffix == ".png" else "image/svg+xml"
            return f'src="data:{mime};base64,{base64.b64encode(source.read_bytes()).decode()}"'
        content = re.sub(r'src="([^"]+)"', embed, content)
        content = content.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
        sections.append(f'<section id="{slug}">{content}</section>')
        toc.append(f'<a href="#{slug}">{label}</a>')
    js = """
document.querySelectorAll('pre').forEach(pre=>{const b=document.createElement('button');b.className='copy';b.textContent='Copy';b.onclick=async()=>{const text=pre.querySelector('code').textContent;try{await navigator.clipboard.writeText(text);b.textContent='Copied';}catch(e){const sel=window.getSelection();const r=document.createRange();r.selectNodeContents(pre.querySelector('code'));sel.removeAllRanges();sel.addRange(r);b.textContent='Selected';}setTimeout(()=>b.textContent='Copy',1800)};pre.appendChild(b)});
const observer=new IntersectionObserver(entries=>{entries.forEach(e=>{if(e.isIntersecting){document.querySelectorAll('aside a').forEach(a=>a.classList.toggle('current',a.hash==='#'+e.target.id))}})},{rootMargin:'-10% 0px -65% 0px'});document.querySelectorAll('section').forEach(s=>observer.observe(s));
"""
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>phipml — from data to plots</title><style>' + CSS + '</style></head><body>'
            '<aside><div class="brand">phipml</div><div class="sub">From data to plots<br>Runnable tutorial · v4.2.0</div><nav>' + ''.join(toc) + '</nav>'
            '<small>Source snapshot<br>932f14f · 8 September 2026<br><br>All results are synthetic.<br>All core scenarios were executed.</small>'
            '<button onclick="window.print()">Print / Save as PDF</button></aside><main>'
            '<header class="hero"><div class="eyebrow">Hands-on computational biology</div><h1>From peptide data<br>to model interpretation.</h1>'
            '<p>Install, configure, fit, validate, and explain. A complete command-line workflow with real synthetic-data outputs and a field-by-field reference.</p>'
            '<div class="badges"><span>6 scenarios × 2 estimators</span><span>Nested CV + external validation</span><span>ROC · PR · SHAP · feature tables</span><span>Works offline</span></div></header>'
            + ''.join(sections) + '<p class="footer">Generated from the Markdown documents in the runnable tutorial bundle. No external fonts, scripts, or image requests.</p>'
            '</main><script>' + js + '</script></body></html>')
    output = ROOT / "phipml-tutorial.html"
    output.write_text(page, encoding="utf-8")
    print(f"Wrote {output} ({output.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
