import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""HEAD THE SUPERSEDED LAYER 2 SELECTION FILES (HANDOFF 0l, 16 Nov).

NOTHING IS DELETED. Each file keeps its name and every byte of its data; a
single `#` comment line is prepended saying what superseded it and why, the
same convention the 170 contaminated files got on 16 Sep.

The header is only safe if every reader passes `comment='#'` -- that is exactly
how `freshness.py` broke on the Layer 1 interface -- so this module REFUSES to
head a file until it has checked every `read_csv` of that filename under code/
and found the flag. A reader without it is reported, not worked around.

    python3 code/l2r2supersede.py            # check and head
    python3 code/l2r2supersede.py --check    # report only, write nothing
"""
import re, glob

NOTE = ('# SUPERSEDED BY HANDOFF 0l (16 Nov 2026) -- %s. '
        'Kept in full, nothing deleted; quote as history only. '
        'The replacement carries the suffix _r2.')

TARGETS = [
    ('gate1_survivors_modeA.csv', 'the gate 1 cut score was W2+W3 pooled = 2011-2020, the very years Layer 2 then called blind (faults #1 and #4), and it was charged no costs'),
    ('gate1_survivors_modeB.csv', 'the gate 1 cut score was W2+W3 pooled = 2011-2020, the very years Layer 2 then called blind (faults #1 and #4), and it was charged no costs'),
    ('gate1_survivors_modeC.csv', 'the gate 1 cut score was W2+W3 pooled = 2011-2020, the very years Layer 2 then called blind (faults #1 and #4), and it was charged no costs'),
    ('gate1_survivors.csv', 'the first sweep, which ran the exit indicator and the baseline cross simultaneously with the C1-flip exit off (fault #2), on top of the 2011-2020 cut score'),
    ('gate1_survivors_v1.csv', 'the first sweep, which ran the exit indicator and the baseline cross simultaneously with the C1-flip exit off (fault #2), on top of the 2011-2020 cut score'),
    ('gate1_mode_runs.csv', 'the run record of a gate 1 whose cut score was the blind years'),
    ('gate2_tuned_modeA_trend.csv', 'tuned from a field selected on 2011-2020'),
    ('gate2_tuned_modeA_chop.csv', 'tuned from a field selected on 2011-2020'),
    ('gate2_tuned_modeB.csv', 'tuned from a field selected on 2011-2020'),
    ('refit_candidates_full.csv', 'the parked 45,139-strategy field: selected on 2011-2020, and 100 mode-A-trend combinations short of its own gate 1 (all c1=waddah_attar_explosion_signals, lost with an unfinished tuning shard)'),
]


def readers(name):
    """Every place under code/ that reads this file, and whether it passes
    comment='#'."""
    out = []
    for f in sorted(glob.glob(os.path.join(ROOTLIB, '*.py'))):
        src = open(f).read()
        if name.replace('.csv', '') not in src:
            continue
        for m in re.finditer(r'read_csv\(([^\n]*)', src):
            seg = m.group(1)
            line = src[:m.start()].count('\n') + 1
            ctx = src[max(0, m.start() - 220):m.start() + 220]
            if name.replace('.csv', '') not in ctx:
                continue
            out.append(dict(file=os.path.basename(f), line=line,
                            has_comment_flag=("comment='#'" in seg or 'comment="#"' in seg
                                              or "comment='#'" in ctx or 'comment="#"' in ctx)))
    return out


def main(check_only=False):
    import pandas as pd
    rows, blocked = [], []
    for name, why in TARGETS:
        p = os.path.join(ROOTOUT, name)
        if not os.path.exists(p):
            rows.append(dict(file=name, status='absent')); continue
        with open(p) as fh:
            first = fh.readline()
        if first.startswith('# SUPERSEDED BY HANDOFF 0l'):
            rows.append(dict(file=name, status='already headed')); continue
        rs = readers(name)
        bad = [r for r in rs if not r['has_comment_flag']]
        if bad:
            blocked.append((name, bad))
            rows.append(dict(file=name, status='BLOCKED: reader without comment=#',
                             detail='; '.join('%s:%d' % (b['file'], b['line']) for b in bad)))
            continue
        if check_only:
            rows.append(dict(file=name, status='would head', detail='%d readers checked' % len(rs)))
            continue
        with open(p) as fh:
            body = fh.read()
        with open(p, 'w') as fh:
            fh.write((NOTE % why) + '\n' + body)
        rows.append(dict(file=name, status='headed', detail='%d readers checked' % len(rs)))
    D = pd.DataFrame(rows)
    print(D.to_string(index=False), flush=True)
    D.to_csv(os.path.join(ROOTOUT, 'r2_superseded_files.csv'), index=False)
    if blocked:
        print('\n!! NOT HEADED -- these readers would break on a comment line:', flush=True)
        for name, bad in blocked:
            for b in bad:
                print('   %-34s <- code/%s line %d' % (name, b['file'], b['line']), flush=True)
        print('   Reported, not worked around. Fix the reader, then rerun.', flush=True)
    print('SUPERSEDE %s' % ('CHECK COMPLETE' if check_only else 'COMPLETE'), flush=True)
    return D


if __name__ == '__main__':
    main(check_only='--check' in sys.argv)
