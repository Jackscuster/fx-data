import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""results/r2gate2/MODEA_TOP30.md -- REPORTED, NOTHING SELECTED (Jack, 18 Nov).

Read-only off the mode A gate 2 bank. No tuning, no engine pass: every number
comes out of results/r2gate2/modeA_full/ and is named in the report.

WHAT IS IN HERE AND WHY IT IS NOT A SELECTION. A top-30 list is a description
of the field's shape, not a roster. HANDOFF 0l's rule stands: everyone who
enters tuning trades, equal weight, no picking and no weighting by past record.
Nothing in this file feeds a book.

THE BANK IS STREAMED. W is (273,780 x 4 streams x 5 steps x 10 years x 5 stats)
which is 2.2 GB in float64; the per-strategy role aggregates are 394 MB, so the
part files are read one at a time and reduced as they come.
"""
import glob, time, json
import numpy as np, pandas as pd
import l2sweep as S
import l2r2gate1 as G
import l2r2gate2 as G2

NS, NST = 4, 5          # streams, steps
ROLES = ('tune', 'grade', 'trade')


def reduce_bank(mode='A', tag='full'):
    """-> (n, combos, tune_score, agg) where agg[role] is (n, 4, 5, 3):
    expectancy, trade count, profit factor. Streamed, float32 stored."""
    outdir, fs = G2.bank_files(mode, tag)
    ST = G2.steps()
    idxs, combos = [], []
    out = {r: [] for r in ROLES}
    tsc = []
    t0 = time.time()
    for q, f in enumerate(fs, 1):
        z = np.load(f, allow_pickle=True)
        w = z['win'].astype(np.float64)          # (m, 4, 5, NYEAR, 5)
        idxs.append(z['idx']); combos.append(z['combo']); tsc.append(z['tune_score'])
        m = w.shape[0]
        for r in ROLES:
            a = np.zeros((m, NS, NST, 3), np.float32)
            for si, stp in enumerate(ST):
                y0, y1 = stp[r]
                blk = G2.role_sum(w[:, :, si], y0, y1)      # (m, 4, 5stats)
                n, e, pf = G2.objective(blk)
                a[:, :, si, 0] = e; a[:, :, si, 1] = n; a[:, :, si, 2] = pf
            out[r].append(a)
        del z, w
        if q % 2 == 0:
            print('    reduced %d/%d part files (%.0f s)' % (q, len(fs), time.time() - t0), flush=True)
    ix = np.concatenate(idxs)
    o = np.argsort(ix, kind='stable')
    uniq = np.concatenate(([True], ix[o][1:] != ix[o][:-1]))
    o = o[uniq]
    agg = {r: np.concatenate(out[r])[o] for r in ROLES}
    CB = np.concatenate(combos)[o]
    TS = np.concatenate(tsc)[o].astype(np.float64)
    print('  bank reduced: %s strategies, %.0f s' % (f'{len(o):,}', time.time() - t0), flush=True)
    return len(o), CB, TS, agg


def main(mode='A', tag='full', topn=30):
    G.manifest_check()
    n, CB, TS, agg = reduce_bank(mode, tag)
    ST = G2.steps()
    tune_e = agg['tune'][:, :, :, 0]; tune_n = agg['tune'][:, :, :, 1]
    gr_e = agg['grade'][:, :, :, 0]; gr_n = agg['grade'][:, :, :, 1]
    tr_e = agg['trade'][:, :, :, 0]; tr_n = agg['trade'][:, :, :, 1]
    tr_pf = agg['trade'][:, :, :, 2]
    sid = np.array(['|'.join(r) for r in CB])

    rows_top, rows_field, rows_pers, rows_all5, rows_rank = [], [], [], [], []

    # ---- 3. the share of the field positive on the trade year, per step/stream
    for si, stp in enumerate(ST):
        for st in range(NS):
            ok = (tr_n[:, st, si] > 0) & np.isfinite(tr_e[:, st, si])
            if not ok.any():
                continue
            rows_field.append(dict(step=stp['name'], stream=G2.STREAMS[st],
                                   n_with_trades=int(ok.sum()),
                                   share_positive_pct=100.0 * float((tr_e[ok, st, si] > 0).mean()),
                                   field_mean_trade_R=float(tr_e[ok, st, si].mean()),
                                   field_median_trade_R=float(np.median(tr_e[ok, st, si]))))

    # ---- 1. top 30 by what the tuner saw, and top 30 by the blind grade
    for si, stp in enumerate(ST):
        for st in range(NS):
            ok = (tune_n[:, st, si] >= G2.MIN_TUNE_TRADES) & np.isfinite(tune_e[:, st, si])
            if ok.sum() < topn:
                continue
            idx = np.flatnonzero(ok)
            for basis, key in (('tune-year objective', tune_e), ('blind grade (year 5)', gr_e)):
                v = key[idx, st, si]
                good = np.isfinite(v)
                pick = idx[good][np.argsort(-v[good])[:topn]]
                tv = tr_e[pick, st, si]; tn = tr_n[pick, st, si]
                # FINITE ONLY. objective() returns -inf for a role with no
                # trades, and one such pick took the whole top-30 mean to -inf.
                fin = np.isfinite(tv) & (tn > 0)
                tvf = tv[fin]
                fm = float(tr_e[ok, st, si][np.isfinite(tr_e[ok, st, si])].mean())
                pf_ = tr_pf[pick, st, si]
                rows_top.append(dict(
                    step=stp['name'], stream=G2.STREAMS[st], basis=basis, n_top=len(pick),
                    n_top_with_trade_year_trades=int(fin.sum()),
                    top_mean_trade_R=(float(tvf.mean()) if fin.any() else np.nan),
                    top_median_trade_R=(float(np.median(tvf)) if fin.any() else np.nan),
                    top_mean_trade_PF=float(np.mean(pf_[np.isfinite(pf_)])) if np.isfinite(pf_).any() else np.nan,
                    top_mean_trade_count=float(tn[fin].mean()) if fin.any() else np.nan,
                    n_top_positive=int((tvf > 0).sum()),
                    field_mean_trade_R=fm,
                    top_minus_field=(float(tvf.mean()) - fm) if fin.any() else np.nan))

    # ---- 2. persistence across the five steps
    for st in range(NS):
        pos = np.zeros(n, np.int64); have = np.zeros(n, np.int64)
        for si in range(NST):
            ok = (tr_n[:, st, si] > 0) & np.isfinite(tr_e[:, st, si])
            have += ok.astype(np.int64)
            pos += (ok & (tr_e[:, st, si] > 0)).astype(np.int64)
        full = have == NST
        if not full.any():
            continue
        base = float(np.mean([ (tr_e[(tr_n[:, st, si] > 0), st, si] > 0).mean()
                               for si in range(NST) ]))
        from math import comb
        for k in (5, 4, 3):
            obs = int(((pos >= k) & full).sum())
            expect = sum(comb(NST, j) * base ** j * (1 - base) ** (NST - j) for j in range(k, NST + 1))
            rows_pers.append(dict(stream=G2.STREAMS[st], k_of_5=k, n_eligible=int(full.sum()),
                                  observed=obs, base_rate_pct=100.0 * base,
                                  coin_flip_expected=float(expect * full.sum()),
                                  ratio_obs_over_expected=(obs / (expect * full.sum())
                                                           if expect * full.sum() > 0 else np.nan)))
        # ---- the all-5 names, with settings, per-year R, and tune-rank percentile
        a5 = np.flatnonzero((pos == NST) & full)
        # RANK EVERY STRATEGY ONCE per (stream, step). The first version scanned
        # the whole field per name per step -- 9.4 billion comparisons for the
        # ~7,500 all-5 names -- so it was capped at 400 and the list was
        # truncated without saying so.
        rankpct = np.full((n, NST), np.nan)
        for si in range(NST):
            okv = (tune_n[:, st, si] >= G2.MIN_TUNE_TRADES) & np.isfinite(tune_e[:, st, si])
            iv = np.flatnonzero(okv)
            if not len(iv):
                continue
            order = iv[np.argsort(-tune_e[iv, st, si], kind='stable')]
            rr = np.empty(len(order)); rr[np.arange(len(order))] = np.arange(len(order))
            rankpct[order, si] = 100.0 * rr / max(len(order) - 1, 1)
        for i in a5:
            d = dict(stream=G2.STREAMS[st], sid=sid[i])
            for si, stp in enumerate(ST):
                d['trade_R_%s' % stp['trade'][0]] = float(tr_e[i, st, si])
                d['trades_%s' % stp['trade'][0]] = int(tr_n[i, st, si])
            rows_all5.append(d)
            # ---- 4. was anything known in advance?
            for si, stp in enumerate(ST):
                pct = rankpct[i, si]
                band = ('not eligible' if not np.isfinite(pct) else
                        'top 1%' if pct <= 1 else 'top 10%' if pct <= 10
                        else 'top 50%' if pct <= 50 else 'bottom 50%')
                rows_rank.append(dict(stream=G2.STREAMS[st], sid=sid[i], step=stp['name'],
                                      tune_rank_pct=(float(pct) if np.isfinite(pct) else np.nan),
                                      band=band))

    RD = os.path.join(ROOTOUT, 'r2gate2')
    outs = {}
    for nm, rws in (('top30', rows_top), ('fieldshare', rows_field),
                    ('persistence', rows_pers), ('all5', rows_all5), ('all5_rank', rows_rank)):
        D = pd.DataFrame(rws)
        p = os.path.join(RD, 'mode%s_top30_%s.csv' % (mode, nm))
        D.to_csv(p, index=False)
        outs[nm] = (p, D)
        print('  %-12s %6d rows -> %s' % (nm, len(D), os.path.relpath(p, _R)), flush=True)
    return outs




# ==========================================================================
# the markdown, every number read back out of the csvs just written
# ==========================================================================
def write_md(mode='A', out=None):
    import hashlib
    RD = os.path.join(ROOTOUT, 'r2gate2')
    F = {k: os.path.join(RD, 'mode%s_top30_%s.csv' % (mode, k))
         for k in ('top30', 'fieldshare', 'persistence', 'all5', 'all5_rank')}
    L = []
    A = L.append
    A('# MODE %s — TOP 30, PERSISTENCE AND WHAT WAS KNOWN IN ADVANCE\n' % mode)
    A(('Generated %s by `code/l2r2top30.py`, read-only off the mode %s gate 2 bank. '
       '**No tuning and no engine pass.** Every number below is read back out of the '
       'CSV named beside it. **Everything here is reported; nothing is selected for a '
       'book** -- HANDOFF 0l\'s rule stands that everyone who enters tuning trades, at '
       'equal weight, with no picking and no weighting by past record.\n')
      % (time.strftime('%F %H:%M'), mode))
    A('\n## Sources\n')
    rows = []
    for k, p in F.items():
        if os.path.exists(p):
            rows.append(dict(section=k, file=os.path.relpath(p, _R),
                             rows=len(pd.read_csv(p)),
                             md5=hashlib.md5(open(p, 'rb').read()).hexdigest()[:12]))
    A(_tbl(pd.DataFrame(rows), ['section', 'file', 'rows', 'md5']))

    A('\n## 3. The share of the field positive on the trade year\n')
    Fs = pd.read_csv(F['fieldshare'])
    A(_tbl(Fs.sort_values(['stream', 'step']),
           ['stream', 'step', 'n_with_trades', 'share_positive_pct',
            'field_mean_trade_R', 'field_median_trade_R']))
    A('\nMean over the five steps:\n')
    A(_tbl(Fs.groupby('stream', as_index=False)[['share_positive_pct', 'field_mean_trade_R']].mean(),
           ['stream', 'share_positive_pct', 'field_mean_trade_R']))

    A('\n## 1. Top 30 by what the tuner saw, and by the blind grade\n')
    T = pd.read_csv(F['top30'])
    A('Per step and stream, then pooled. `top_minus_field` is the top 30\'s mean '
      'trade-year R per trade minus the whole eligible field\'s.\n')
    A(_tbl(T.groupby(['basis', 'stream'], as_index=False)[
        ['top_mean_trade_R', 'field_mean_trade_R', 'top_minus_field',
         'n_top_positive', 'top_mean_trade_PF', 'top_mean_trade_count']].mean(),
           ['basis', 'stream', 'top_mean_trade_R', 'field_mean_trade_R', 'top_minus_field',
            'n_top_positive', 'top_mean_trade_PF', 'top_mean_trade_count']))
    A('\nEvery step, by basis and stream:\n')
    A(_tbl(T.sort_values(['basis', 'stream', 'step']),
           ['basis', 'stream', 'step', 'n_top_with_trade_year_trades', 'top_mean_trade_R',
            'top_median_trade_R', 'n_top_positive', 'field_mean_trade_R', 'top_minus_field']))

    A('\n## 2. Persistence across the five steps, against a coin flip\n')
    P = pd.read_csv(F['persistence'])
    A('`base_rate_pct` is that stream\'s own share of positive trade years, averaged '
      'over the five steps; `coin_flip_expected` is the binomial count at that rate.\n')
    A(_tbl(P, ['stream', 'k_of_5', 'n_eligible', 'observed', 'base_rate_pct',
               'coin_flip_expected', 'ratio_obs_over_expected']))
    Al = pd.read_csv(F['all5'])
    A('\n### The strategies positive on the trade year in all five steps\n')
    A('%s in total, listed in full in `%s` with their settings and per-year R. '
      'Count by stream:\n' % (f'{len(Al):,}', os.path.relpath(F['all5'], _R)))
    A(_tbl(Al.groupby('stream', as_index=False).size().rename(columns={'size': 'n_all_five'}),
           ['stream', 'n_all_five']))
    cols = ['stream', 'sid'] + [c for c in Al.columns if c.startswith('trade_R_')]
    A('\nThe first 15 of them, with per-year R:\n')
    A(_tbl(Al.head(15), cols))

    A('\n## 4. Was anything known in advance about the all-five names?\n')
    Rk = pd.read_csv(F['all5_rank'])
    A('Each all-five name\'s tune-year rank percentile in its own stream and step. '
      'If the tuner could see them coming, they would sit in the top bands.\n')
    bands = Rk.groupby(['stream', 'band'], as_index=False).size().rename(columns={'size': 'n'})
    tot = Rk.groupby('stream', as_index=False).size().rename(columns={'size': 'total'})
    bands = bands.merge(tot, on='stream')
    bands['pct_of_name_steps'] = 100.0 * bands.n / bands.total
    A(_tbl(bands.sort_values(['stream', 'band']), ['stream', 'band', 'n', 'total', 'pct_of_name_steps']))
    A('\nPooled over streams:\n')
    b2 = Rk.groupby('band', as_index=False).size().rename(columns={'size': 'n'})
    b2['pct'] = 100.0 * b2.n / len(Rk)
    A(_tbl(b2.sort_values('n', ascending=False), ['band', 'n', 'pct']))
    A('\nA uniform draw would put 1%% of name-steps in "top 1%%", 10%% in "top 10%%" '
      'and 50%% in "top 50%%". Compare those against the table above.\n')

    txt = '\n'.join(L)
    out = out or os.path.join(RD, 'MODE%s_TOP30.md' % mode)
    open(out, 'w').write(txt)
    print('  MODE%s_TOP30.md: %d lines -> %s' % (mode, len(txt.splitlines()),
                                                os.path.relpath(out, _R)), flush=True)
    return out


def _tbl(d, cols):
    cols = [c for c in cols if c in d.columns]
    if not len(d) or not cols:
        return '_no rows_\n'
    o = ['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)]
    for _, r in d[cols].iterrows():
        cs = []
        for c in cols:
            v = r[c]
            if isinstance(v, (int, np.integer)):
                cs.append(f'{v:,}')
            elif isinstance(v, (float, np.floating)):
                cs.append('' if not np.isfinite(v) else ('%.4g' % v))
            else:
                cs.append(str(v))
        o.append('| ' + ' | '.join(cs) + ' |')
    return '\n'.join(o) + '\n'


if __name__ == '__main__':
    main(G.opt('--mode', str, 'A'), G.opt('--tag', str, 'full'), topn=G.opt('--top', int, 30))
    write_md(G.opt('--mode', str, 'A'))
