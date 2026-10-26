#!/usr/bin/env python3
"""Generate data/chapters.json and data/chNN.json from the author sources:
data/selection.json (which questions), tools/meta.json (crop info written by extract.py)
and tools/answers.json (official answer letter + flags). Author tool only."""
import json, os, random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LETTERS = 'אבגדהו'
CHAPTERS = [
    (1, 'Electrostatics', 'Coulomb, fields of distributions, flux, Gauss'),
    (2, 'Electric potential', 'Potential, energy, work, gradient / divergence / curl'),
    (3, 'Conductors, images, capacitors', 'Concentric shells, method of images, capacitance'),
    (4, 'Current and circuits', 'Current density, Ohm, Kirchhoff, RC circuits'),
    (5, 'Moving charges and relativity of fields', 'Information sphere, Lorentz transformation of E and B, invariants'),
    (6, 'Magnetic field', 'Lorentz force, Ampère, Biot-Savart, forces on currents, Gauss for B'),
    (7, 'Electromagnetic induction', 'Faraday, motional EMF, self-inductance, RL circuits'),
    (8, 'Maxwell equations', 'Displacement current, induced electric field'),
    (9, 'Mechanical waves', 'Wave equation, strings, standing waves'),
    (10, 'Electromagnetic waves', 'E, B and k, Poynting vector, power'),
    (11, 'Interference', "Young's double slit, coherent sources"),
]
SEASON = {'sp': 'Spring', 'wn': 'Winter'}
MOED = {'A': 'Moed A', 'B': 'Moed B', 'C': 'Moed C', 'M': 'Reserve-duty Moed'}


def label(exam):
    return f'{SEASON[exam[2:4]]} 20{exam[:2]} · {MOED[exam[4]]}'


def main():
    sel = json.load(open(os.path.join(ROOT, 'data/selection.json')))
    meta = json.load(open(os.path.join(ROOT, 'tools/meta.json')))
    ans = json.load(open(os.path.join(ROOT, 'tools/answers.json')))
    N = sum(len(v) for v in sel.values())
    chapters = []
    for n, title, topics in CHAPTERS:
        items = sel[str(n)]
        ids = [f"{it['exam']}-q{it['q']:02d}" for it in items]
        ready = all(i in ans for i in ids) and os.path.exists(os.path.join(ROOT, f'corrections/ch{n:02d}.html'))
        chapters.append(dict(n=n, title=title, topics=topics, ids=ids if ready else [], count=len(ids)))
        if not ready:
            continue
        rng = random.Random(f'p2mm-{n}')
        # balanced target positions for the correct answer within the chapter
        targets = [i % 6 for i in range(len(items))]
        rng.shuffle(targets)
        qs = []
        for it, qid, tgt in zip(items, ids, targets):
            m, a = meta[qid], ans[qid]
            nopt = a.get('n', m['n'])
            orig = LETTERS.index(a['ans'])
            order = list(range(nopt))
            if m['split']:
                rng.shuffle(order)
                tgt = tgt % nopt
                order.remove(orig)
                order.insert(tgt, orig)
            qs.append(dict(id=qid, exam=it['exam'], examLabel=label(it['exam']), num=it['q'], n=nopt,
                           split=m['split'], answer=orig, order=order, officialSol=m['sol'],
                           alsoIn=[dict(exam=x['exam'], q=x['q'], label=f"{label(x['exam'])} Q{x['q']}"
                                       + ('' if x.get('sameOptions', True) else ' (same statement, other answer choices)'))
                                  for x in it['alsoIn']],
                           toVerify=a.get('toVerify', False), differs=a.get('differs', False)))
        json.dump(dict(chapter=n, title=title, questions=qs), open(os.path.join(ROOT, f'data/ch{n:02d}.json'), 'w'),
                  ensure_ascii=False, indent=1)
        pos = [q['order'].index(q['answer']) for q in qs]
        print(f'ch{n:02d}: {len(qs)} questions, correct displayed at', ''.join(LETTERS[p] for p in pos))
    json.dump(dict(N=N, chapters=chapters), open(os.path.join(ROOT, 'data/chapters.json'), 'w'), ensure_ascii=False, indent=1)
    print('N =', N)


if __name__ == '__main__':
    main()
