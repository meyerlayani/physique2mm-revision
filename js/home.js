fetch('data/chapters.json').then(r => r.json()).then(data => {
  const all = data.chapters.flatMap(c => c.ids);
  const g = P2MM.stats(all);
  document.getElementById('global-pct').textContent = pct(g.done, data.N) + '%';
  document.getElementById('global-bar').style.width = pct(g.done, data.N) + '%';
  document.getElementById('global-detail').textContent =
    `${g.done} / ${data.N} questions done · score ${g.good} / ${g.done} correct`;
  const ol = document.getElementById('chapters');
  data.chapters.forEach(c => {
    const s = P2MM.stats(c.ids);
    const li = document.createElement('li');
    li.className = 'card chapter' + (c.ids.length ? '' : ' soon');
    const ready = c.ids.length > 0;
    li.innerHTML = `
      <a ${ready ? `href="chapter.html?c=${c.n}"` : ''} class="ch-link">
        <span class="ch-num">${c.n}</span>
        <span class="ch-body">
          <span class="ch-title">${c.title}</span>
          <span class="ch-topics muted small">${c.topics}</span>
          <span class="bar thin"><span class="fill" style="width:${pct(s.done, s.total)}%"></span></span>
          <span class="muted small">${ready ? `${s.done} / ${s.total} done · score ${s.good} / ${s.done}` : 'Coming soon'}</span>
        </span>
      </a>`;
    ol.appendChild(li);
  });
});

document.getElementById('reset').addEventListener('click', () => {
  if (confirm('Reset all your progress? This cannot be undone.')) { P2MM.reset(); location.reload(); }
});
