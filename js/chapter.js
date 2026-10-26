const LETTERS = 'אבגדהו';
const params = new URLSearchParams(location.search);
const C = parseInt(params.get('c') || '1', 10);
const pad = n => String(n).padStart(2, '0');
let corrections = null;

function math(el) {
  if (window.renderMathInElement) {
    renderMathInElement(el, {
      delimiters: [
        { left: '$$', right: '$$', display: true },
        { left: '\\[', right: '\\]', display: true },
        { left: '$', right: '$', display: false },
        { left: '\\(', right: '\\)', display: false },
      ],
      throwOnError: false,
    });
  }
}

function setLang(l) {
  document.body.dataset.lang = l;
  document.querySelectorAll('.lang button').forEach(b => b.classList.toggle('on', b.dataset.lang === l));
  P2MM.setLang(l);
}

// All PDF crops share one scale (200 dpi renders of a ~1514 px wide text column),
// so statement text and options appear at the same size. Tap a figure to zoom.
const PAGE_PX = 1514;
function setScale() {
  const w = document.getElementById('qlist').clientWidth || 360;
  document.documentElement.style.setProperty('--k', Math.min(0.62, (w - 28) / PAGE_PX));
}
function sized(img) {
  const apply = () => { img.style.width = `calc(var(--k) * ${img.naturalWidth}px)`; };
  if (img.complete && img.naturalWidth) apply(); else img.addEventListener('load', apply);
}
window.addEventListener('resize', setScale);

function fragment(html) {
  return new DOMParser().parseFromString(html, 'text/html');
}

function refreshHeader(data) {
  const s = P2MM.stats(data.questions.map(q => q.id));
  document.getElementById('ch-bar').style.width = pct(s.done, s.total) + '%';
  document.getElementById('ch-detail').textContent =
    `${s.done} / ${s.total} questions done · score ${s.good} / ${s.done}`;
  if (s.total && s.done === s.total && !document.querySelector('.cheer')) {
    const c = document.createElement('div');
    c.className = 'card cheer';
    c.innerHTML = `🎉 <b>Chapter complete!</b> Score ${s.good} / ${s.total}. On to the next one.`;
    document.getElementById('pager').before(c);
  }
}

function renderQuestion(q, idx, data) {
  const el = document.createElement('article');
  el.className = 'card question';
  el.id = q.id;
  const displayed = q.split ? q.order : [...Array(q.n).keys()];
  const correctPos = displayed.indexOf(q.answer);
  const also = q.alsoIn.length ? ` · also in ${q.alsoIn.map(a => a.label).join(', ')}` : '';
  el.innerHTML = `
    <header class="q-head">
      <span class="q-num">Q${idx + 1}</span>
      <span class="muted small">${q.examLabel}, question ${q.num}${also}</span>
      ${q.toVerify ? '<span class="badge warn">To verify</span>' : ''}
    </header>
    <figure class="statement" dir="rtl"><img loading="lazy" src="img/q/${q.id}.png" alt="Question statement (Hebrew), ${q.examLabel} Q${q.num}"></figure>
    <p class="muted small zoomhint">Tap the statement to zoom.</p>
    <div class="options ${q.split ? 'split' : 'compact'}" dir="rtl"></div>
    <div class="verdict" hidden></div>
    <div class="after" hidden>
      <section class="block official">
        <h3>1. Official solution</h3>
        ${q.officialSol ? `<div class="pdfimg"><img loading="lazy" src="img/sol/${q.id}.png" alt="Official solution (Hebrew)"></div><p class="muted small">Tap the image to zoom.</p>` : '<p class="muted">No official solution available for this question.</p>'}
      </section>
      <section class="block detailed">
        <h3>2. Detailed correction</h3>
        ${q.differs ? '<p class="badge warn">Note: differs from official solution</p>' : ''}
        <div class="corr"></div>
      </section>
    </div>`;
  el.querySelectorAll('.statement img, .official img').forEach(img => {
    sized(img);
    img.addEventListener('click', () => {
      const z = img.parentElement.classList.toggle('zoom');
      img.style.width = z ? `${Math.round(img.naturalWidth * 0.5)}px` : `calc(var(--k) * ${img.naturalWidth}px)`;
    });
  });
  const opts = el.querySelector('.options');
  displayed.forEach((orig, pos) => {
    const b = document.createElement('button');
    b.className = 'opt';
    b.dataset.pos = pos;
    b.innerHTML = q.split
      ? `<span class="letter">${LETTERS[pos]}</span><img loading="lazy" src="img/q/${q.id}-o${orig}.png" alt="Option ${LETTERS[pos]}">`
      : `<span class="letter">${LETTERS[pos]}</span>`;
    b.addEventListener('click', () => answer(pos));
    opts.appendChild(b);
  });

  // options of one question share a scale: the largest that fits the widest option (capped)
  const oimgs = [...opts.querySelectorAll('img')];
  const fitOptions = () => {
    if (!oimgs.length || oimgs.some(i => !i.naturalWidth)) return;
    const avail = opts.clientWidth - 70;
    const widest = Math.max(...oimgs.map(i => i.naturalWidth));
    const k = Math.min(0.5, avail / widest);
    oimgs.forEach(i => { i.style.width = `${Math.round(i.naturalWidth * k)}px`; });
  };
  oimgs.forEach(i => i.addEventListener('load', fitOptions));
  window.addEventListener('resize', fitOptions);
  setTimeout(fitOptions, 0);

  function show(pick, firstTime) {
    const ok = pick === correctPos;
    el.querySelectorAll('.opt').forEach((b, i) => {
      b.classList.toggle('right', i === correctPos);
      b.classList.toggle('wrong', i === pick && !ok);
      b.classList.toggle('picked', i === pick);
    });
    const v = el.querySelector('.verdict');
    v.hidden = false;
    v.className = 'verdict ' + (ok ? 'ok' : 'ko');
    const orig = LETTERS[q.answer];
    const note = q.split && orig !== LETTERS[correctPos]
      ? ` <span class="muted small">(labelled ${orig} in the official solution)</span>` : '';
    v.innerHTML = (ok ? '✔ Correct' : '✘ Wrong') + ` — correct answer: <b>${LETTERS[correctPos]}</b>${note}`;
    const after = el.querySelector('.after');
    if (after.hidden) {
      after.hidden = false;
      const art = corrections && corrections.querySelector(`article[data-id="${q.id}"]`);
      const box = el.querySelector('.corr');
      box.innerHTML = art ? art.innerHTML : '<p class="muted">Detailed correction not available yet.</p>';
      math(box);
    }
    if (firstTime) after.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
  function answer(pos) {
    const first = !P2MM.get(q.id);
    P2MM.record(q.id, pos, pos === correctPos);
    show(pos, first);
    el.classList.add('done');
    refreshHeader(data);
    if (first) {
      track(`answer/${q.id}/${pos === correctPos ? 'correct' : 'wrong'}`);
      const s = P2MM.stats(data.questions.map(x => x.id));
      if (s.done === s.total) track(`chapter-complete/${C}`);
    }
  }
  const saved = P2MM.get(q.id);
  if (saved) { el.classList.add('done'); setTimeout(() => show(saved.pick, false), 0); }
  return el;
}

Promise.all([
  fetch(`data/ch${pad(C)}.json?v=${Date.now()>>20}`).then(r => r.json()),
  fetch(`lessons/ch${pad(C)}.html?v=${Date.now()>>20}`).then(r => (r.ok ? r.text() : '')),
  fetch(`corrections/ch${pad(C)}.html?v=${Date.now()>>20}`).then(r => (r.ok ? r.text() : '')),
  fetch(`data/chapters.json?v=${Date.now()>>20}`).then(r => r.json()),
]).then(([data, lesson, corr, chapters]) => {
  document.title = `${C}. ${data.title} · פיזיקה 2ממ`;
  document.getElementById('title').textContent = data.title;
  document.getElementById('kicker').textContent = `Chapter ${C} of ${chapters.chapters.length}`;
  document.documentElement.style.setProperty('--c', `var(--c${C})`);
  const L = document.getElementById('lesson');
  L.innerHTML = lesson ? fragment(lesson).body.innerHTML : '<p class="muted">Lesson coming soon.</p>';
  math(L);
  corrections = corr ? fragment(corr) : null;
  const list = document.getElementById('qlist');
  setScale();
  data.questions.forEach((q, i) => list.appendChild(renderQuestion(q, i, data)));
  refreshHeader(data);
  const pager = document.getElementById('pager');
  const prev = chapters.chapters.find(c => c.n === C - 1);
  const next = chapters.chapters.find(c => c.n === C + 1);
  pager.innerHTML = (prev ? `<a class="btn ghost" href="chapter.html?c=${prev.n}">← ${prev.n}. ${prev.title}</a>` : '<span></span>') +
    (next ? `<a class="btn ghost" href="chapter.html?c=${next.n}">${next.n}. ${next.title} →</a>` : '<span></span>');
  if (location.hash) { const t = document.querySelector(location.hash); if (t) t.scrollIntoView(); }
});

setLang(P2MM.lang());
document.querySelectorAll('.lang button').forEach(b => b.addEventListener('click', () => { setLang(b.dataset.lang); track(`lang-${b.dataset.lang}`); }));
