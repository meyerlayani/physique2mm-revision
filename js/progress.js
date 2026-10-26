// Progress stored per visitor in localStorage: { id: { pick: displayIndex, correct: bool } }
const P2MM = (() => {
  const KEY = 'p2mm-v1';
  let state = {};
  try { state = JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { state = {}; }
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* private mode */ } };
  return {
    get: id => state[id],
    record(id, pick, correct) {
      if (!state[id]) { state[id] = { pick, correct }; save(); }  // first answer counts
    },
    reset() { state = {}; save(); },
    stats(ids) {
      let done = 0, good = 0;
      ids.forEach(id => { const s = state[id]; if (s) { done++; if (s.correct) good++; } });
      return { done, good, total: ids.length };
    },
    lang() { try { return localStorage.getItem('p2mm-lang') || 'fr'; } catch (e) { return 'fr'; } },
    setLang(l) { try { localStorage.setItem('p2mm-lang', l); } catch (e) { /* ignore */ } },
  };
})();

// Anonymous event counter (GoatCounter); silently does nothing if the script is blocked
function track(name) {
  try { if (window.goatcounter && window.goatcounter.count) window.goatcounter.count({ path: name, event: true }); } catch (e) { /* ignore */ }
}

const pct = (a, b) => (b ? Math.round(1000 * a / b) / 10 : 0);
