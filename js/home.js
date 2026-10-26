const EXAM = new Date('2026-10-30T09:00:00+03:00');

function countdown() {
  const el = document.getElementById('countdown');
  const ms = EXAM - new Date();
  if (ms <= 0) { el.innerHTML = '<span class="cd-big">Exam day</span><span>בהצלחה!</span>'; return; }
  const d = Math.floor(ms / 864e5), h = Math.floor(ms / 36e5) % 24;
  el.innerHTML = `<span class="cd-big">${d}<small>d</small> ${h}<small>h</small></span><span>until the exam · Friday 30/10</span>`;
}

function motivation(p) {
  if (p === 0) return 'Start with chapter 1: one question at a time.';
  if (p < 25) return 'Good start! Keep the rhythm going.';
  if (p < 50) return 'Nice work, you are building momentum.';
  if (p < 75) return 'More than halfway there. Keep pushing!';
  if (p < 100) return 'Almost done. Finish strong!';
  return 'Everything done. You are ready! בהצלחה';
}

fetch(`data/chapters.json?v=${Date.now()>>20}`).then(r => r.json()).then(data => {
  const all = data.chapters.flatMap(c => c.ids);
  const g = P2MM.stats(all);
  const p = pct(g.done, data.N);
  document.getElementById('global-pct').textContent = p + '%';
  document.getElementById('ring').style.setProperty('--p', p);
  document.getElementById('global-bar').style.width = p + '%';
  document.getElementById('global-detail').textContent =
    `${g.done} / ${data.N} questions done · score ${g.good} / ${g.done} correct`;
  document.getElementById('motivation').textContent = motivation(p);
  if (p >= 100) track('all-done');
  const ol = document.getElementById('chapters');
  data.chapters.forEach(c => {
    const s = P2MM.stats(c.ids);
    const li = document.createElement('li');
    const done = s.total && s.done === s.total;
    li.className = 'card chapter' + (done ? ' complete' : '');
    li.style.setProperty('--c', `var(--c${c.n})`);
    li.innerHTML = `
      <a href="chapter.html?c=${c.n}" class="ch-link">
        <span class="ch-num">${done ? '✓' : c.n}</span>
        <span class="ch-body">
          <span class="ch-title">${c.title}</span>
          <span class="ch-topics muted small">${c.topics}</span>
          <span class="bar thin"><span class="fill" style="width:${pct(s.done, s.total)}%"></span></span>
          <span class="muted small">${s.done} / ${s.total} done · score ${s.good} / ${s.done}</span>
        </span>
        <span class="ch-go" aria-hidden="true">›</span>
      </a>`;
    ol.appendChild(li);
  });
});

countdown();
setInterval(countdown, 60000);
document.getElementById('reset').addEventListener('click', () => {
  if (confirm('Reset all your progress? This cannot be undone.')) { P2MM.reset(); location.reload(); }
});
