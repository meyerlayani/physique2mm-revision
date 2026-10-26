# Physics 2mm (Technion 114075) – revision site

Static revision site for the summer 2026 exam (Friday 30/10/2026): 11 chapters following
`syllabus/syllabus_physique2mm_ete2026.txt`, each with a detailed lesson (FR / HE) and a
selection of 110 past-exam questions (Hebrew statements cropped from the PDFs, shuffled
options, official solution + detailed correction in FR / HE), and a progress counter saved
in the browser.

## Use
Open `index.html` through a web server (the pages load JSON with `fetch`, which browsers
block for `file://`). Locally: `python3 -m http.server` then http://localhost:8000.
On GitHub Pages it works as is (relative paths, no build step).

## Layout
- `index.html`, `chapter.html`, `css/`, `js/` – the site
- `lessons/chNN.html` – lessons; `corrections/chNN.html` – detailed corrections
- `data/` – `chapters.json` (N = 110), `chNN.json` (questions), `selection.json` (which past-exam questions)
- `img/q/` – statements (`<exam>-qNN.png`) and options (`-oK.png`); `img/sol/` – official solutions
- `vendor/katex/` – KaTeX 0.16.11 (math rendering, MIT licence)
- `tools/` – author tools, not used by the site: `extract.py` (crops from `exam/`),
  `build.py` (data JSON), `answers.json` (official answers), `overrides.json`,
  `escape_math.py`, `check.mjs` (browser check with Playwright)
- `exam/`, `syllabus/` – sources

## Rebuild after a change
```
python3 tools/extract.py --chapter N     # crops for chapter N
python3 tools/escape_math.py             # after editing lessons / corrections
python3 tools/build.py                   # data/*.json
node tools/check.mjs                     # browser check of every chapter
```
