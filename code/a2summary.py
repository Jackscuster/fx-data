import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE A2 DEFAULTS SUMMARY, COMMITTED IN PLACE OF A 654 MB CSV.

Jack, 24 Nov, step 4 of the push decision: "The files stay on disk, gitignored,
under MANIFEST.sha256 like the banks. Write a small summary csv (per mode, per
stream: counts, means, the numbers the A2 report quotes) that is committed in
their place."

WHAT THE BIG FILES ARE. mode<M>_a2_defaults.csv holds one row per
(bank_row, stream, step, role, year) -- 10,736,759 rows for mode A and about
the same for mode B, at 654 and 655 MB. They are the DEFAULT-configuration
scoring pass, and they exist to be read once by r2reads.stage_a2_compare, which
subtracts them from the tuned pass and writes the numbers the A2 report
actually quotes. They are intermediate data of exactly the kind guard 28
already keeps on disk under a manifest rather than in git.

WHAT THIS SUMMARY PRESERVES. Everything a reader needs to check the A2 report
without the raw file, and enough to notice if the raw file is ever regenerated
differently: per (mode, role, stream, step) and per (mode, role, year), the
number of rows, the number of distinct bank rows, total trades, total R, and R
per trade. A regeneration that changed any conclusion would move one of these.

IT IS NOT A SUBSTITUTE FOR THE FILE. stage_a2_compare needs the per-bank_row
detail and will still read the raw csv from disk. If the raw file is missing,
that stage must say so rather than run on the summary -- the summary cannot
reconstruct a per-strategy array.
"""
import time, hashlib, glob
import numpy as np, pandas as pd

OUT = os.path.join(ROOTOUT, 'r2reads')
CHUNK = 2_000_000

DT = {'bank_row': np.int64, 'stream': 'category', 'step': 'category',
      'role': 'category', 'year': np.int32, 'n': np.float64,
      'sum_r': np.float64}


def summarise(path, mode):
    """-> (by_stream_step, by_year). Chunked, so a 654 MB csv costs no RAM."""
    acc_ss, acc_y, seen = {}, {}, {}
    nrows = 0
    for ch in pd.read_csv(path, dtype=DT, chunksize=CHUNK):
        nrows += len(ch)
        g = ch.groupby(['role', 'stream', 'step'], observed=True)
        for k, sub in g:
            a = acc_ss.setdefault(k, [0, 0.0, 0.0])
            a[0] += len(sub); a[1] += float(sub.n.sum())
            a[2] += float(sub.sum_r.sum())
            seen.setdefault(k, set()).update(sub.bank_row.unique().tolist())
        for k, sub in ch.groupby(['role', 'year'], observed=True):
            a = acc_y.setdefault(k, [0, 0.0, 0.0])
            a[0] += len(sub); a[1] += float(sub.n.sum())
            a[2] += float(sub.sum_r.sum())
    rows = []
    for (role, stream, step), (nr, nn, rr) in sorted(acc_ss.items()):
        rows.append(dict(mode=mode, role=role, stream=stream, step=step,
                         rows=nr, bank_rows=len(seen[(role, stream, step)]),
                         trades=nn, sum_R=rr,
                         R_per_trade=(rr / nn if nn else np.nan)))
    rows2 = []
    for (role, year), (nr, nn, rr) in sorted(acc_y.items()):
        rows2.append(dict(mode=mode, role=role, year=int(year), rows=nr,
                          trades=nn, sum_R=rr,
                          R_per_trade=(rr / nn if nn else np.nan)))
    return pd.DataFrame(rows), pd.DataFrame(rows2), nrows


def manifest_for(paths, out):
    """file, bytes, sha256 -- the same shape bankcheck.py writes for a bank."""
    rows = []
    for p in paths:
        if not os.path.exists(p):
            continue
        h = hashlib.sha256()
        with open(p, 'rb') as fh:
            for b in iter(lambda: fh.read(1 << 22), b''):
                h.update(b)
        rows.append(dict(file=os.path.relpath(p, _R),
                         bytes=os.path.getsize(p), sha256=h.hexdigest()))
    D = pd.DataFrame(rows)
    D.to_csv(out, index=False)
    return D


def run(modes=('A', 'B'), verbose=True):
    ss, yy, paths = [], [], []
    for m in modes:
        p = os.path.join(OUT, 'mode%s_a2_defaults.csv' % m)
        if not os.path.exists(p):
            if verbose:
                print('  a2 summary: mode %s raw file absent, skipped' % m,
                      flush=True)
            continue
        t0 = time.time()
        A, B, nr = summarise(p, m)
        ss.append(A); yy.append(B); paths.append(p)
        if verbose:
            print('  a2 summary [mode %s]: %s rows summarised in %.1f min '
                  '(%.0f MB on disk)'
                  % (m, f'{nr:,}', (time.time() - t0) / 60,
                     os.path.getsize(p) / 1048576), flush=True)
    if not ss:
        return None
    f1 = os.path.join(OUT, 'a2_defaults_summary.csv')
    f2 = os.path.join(OUT, 'a2_defaults_by_year.csv')
    f3 = os.path.join(OUT, 'a2_defaults_MANIFEST.sha256')
    pd.concat(ss, ignore_index=True).to_csv(f1, index=False)
    pd.concat(yy, ignore_index=True).to_csv(f2, index=False)
    M = manifest_for(paths, f3)
    if verbose:
        print('  a2 summary -> %s (%d rows), %s, and a manifest of %d file(s), '
              '%.1f GB total'
              % (os.path.relpath(f1, _R), sum(len(x) for x in ss),
                 os.path.relpath(f2, _R), len(M),
                 M.bytes.sum() / 1024 ** 3), flush=True)
    return f1


# ---- NOTHING IS DEFINED BELOW THIS POINT (preflight guard 29)
if __name__ == '__main__':
    run()
