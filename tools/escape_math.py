#!/usr/bin/env python3
"""Escape '<' inside $...$ / $$...$$ in lessons and corrections ('<b' would be parsed as an HTML tag)."""
import glob, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for f in sorted(glob.glob(os.path.join(ROOT, 'lessons/*.html')) + glob.glob(os.path.join(ROOT, 'corrections/*.html'))):
    s = open(f).read()
    fix = lambda m: re.sub(r'<(?=[^/!])', '&lt;', m.group(0))
    s2 = re.sub(r'\$\$.*?\$\$', fix, s, flags=re.S)
    s2 = re.sub(r'(?<!\$)\$(?!\$)[^$]+?\$', fix, s2)
    if s2 != s:
        open(f, 'w').write(s2)
        print('escaped', os.path.relpath(f, ROOT))
