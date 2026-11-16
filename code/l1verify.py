import os,sys,subprocess,hashlib,json,re,shutil,tempfile,time
import numpy as np, pandas as pd

"""INDEPENDENT DOUBLE-CHECK OF THE LAYER 1 CLOSE-OUT (16 Nov).

Runs against a FRESH CLONE of github.com/Jackscuster/fx-data -- the exact state
the Layer 2 rebuild will inherit -- and trusts nothing the close-out chain said.
Every check is recomputed from the clone's own files. The chain's own
LAYER1_CLOSEOUT_AUDIT.csv is compared against these results at the end, and any
disagreement between the two audits is itself a FAIL.

    python3 code/l1verify.py --out results/LAYER1_VERIFY_<stamp>.csv

Nothing is fixed here. Failures are reported.
"""

REPO = 'https://github.com/Jackscuster/fx-data.git'
SEAL = pd.Timestamp('2020-12-31')
SPLIT = pd.Timestamp('2016-01-01')
ROWS = []


def row(n, check, status, detail=''):
    ROWS.append(dict(n=n, check=check, status=status, detail=str(detail)[:400]))
    print('%-4s %-2s %s%s' % (status, n, check[:78], ('  -- ' + str(detail)[:120]) if detail else ''), flush=True)


def run(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)


def main():
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); ap.add_argument('--keep', action='store_true')
    a = ap.parse_args()
    t0 = time.time()
    tmp = tempfile.mkdtemp(prefix='l1verify_')
    clone = os.path.join(tmp, 'fx-data')
    print('=== INDEPENDENT LAYER 1 VERIFICATION, fresh clone in %s ===' % tmp, flush=True)
    sha = ''
    try:
        # ---- 1. fresh clone
        r = run(['git', 'clone', '--depth', '1', REPO, clone])
        if r.returncode != 0:
            row(1, 'fresh clone of %s' % REPO, 'FAIL', (r.stderr or '')[-200:])
            raise SystemExit(1)
        sha = run(['git', 'rev-parse', 'HEAD'], cwd=clone).stdout.strip()
        subj = run(['git', 'log', '-1', '--format=%s'], cwd=clone).stdout.strip()
        row(1, 'fresh clone, this is what the world sees', 'PASS', '%s  %s' % (sha[:12], subj[:70]))

        # ---- 2. the contract and every file it names
        doc = os.path.join(clone, 'LAYER1_INTERFACE.md')
        if not os.path.exists(doc):
            row(2, 'LAYER1_INTERFACE.md exists at the clone root', 'FAIL',
                'absent -- the close-out has not been pushed to origin/main')
            named = []
        else:
            txt = open(doc).read()
            row(2, 'LAYER1_INTERFACE.md exists at the clone root', 'PASS', '%d bytes' % len(txt))
            named = sorted(set(re.findall(r'`(results/[A-Za-z0-9_./-]+\.csv)`', txt)))
            row('2a', 'the contract names interface files', 'PASS' if named else 'FAIL', '%d files named' % len(named))
            man = os.path.join(clone, 'results', 'layer1_interface_manifest_2026-11-16.csv')
            M = pd.read_csv(man) if os.path.exists(man) else pd.DataFrame()
            bad = []
            for p in named:
                fp = os.path.join(clone, p)
                if not os.path.exists(fp):
                    bad.append('%s MISSING' % p); continue
                try:
                    d = pd.read_csv(fp, comment='#', low_memory=False)
                except Exception as e:
                    bad.append('%s unreadable (%s)' % (p, str(e)[:40])); continue
                if len(M) and (M.path == p).any():
                    m = M[M.path == p].iloc[0]
                    if pd.notna(m.get('rows')) and int(m['rows']) != len(d):
                        bad.append('%s rows %d != manifest %d' % (p, len(d), int(m['rows'])))
                    if pd.notna(m.get('pairs')) and 'pair' in d.columns and int(m['pairs']) != d.pair.nunique():
                        bad.append('%s pairs %d != manifest %d' % (p, d.pair.nunique(), int(m['pairs'])))
                    if 'date' in d.columns and isinstance(m.get('date_max'), str) and m['date_max']:
                        got = str(pd.to_datetime(d.date).max().date())
                        if got != m['date_max']:
                            bad.append('%s date_max %s != manifest %s' % (p, got, m['date_max']))
            row('2b', 'every named file exists, loads and matches its claimed counts/spans',
                'PASS' if (named and not bad) else 'FAIL', '; '.join(bad[:4]) if bad else '%d files verified' % len(named))

        # ---- 3. independent recomputation of the quality series
        qp = os.path.join(clone, 'results', 'layer1_trend_quality_series.csv')
        if not os.path.exists(qp):
            row(3, 'quality series recomputed independently in the clone', 'FAIL', 'shipped CSV absent from the clone')
        else:
            env = dict(os.environ); env['PYTHONPATH'] = os.path.join(clone, 'code')
            code = (
                "import os,sys; sys.path.insert(0,'code');\n"
                "import numpy as np, pandas as pd, trendqual as TQ;\n"
                "px=pd.read_csv('data/px28.csv',index_col=0,parse_dates=True).astype(float);\n"
                "SEAL=pd.Timestamp('2020-12-31');\n"
                "_,rd=TQ.build_all(px);\n"
                "st=pd.read_csv('results/layer1_states.csv',comment='#',parse_dates=['date'],usecols=['date','pair','shape2']);\n"
                "s2=st.pivot(index='date',columns='pair',values='shape2').reindex(px.index);\n"
                "E,thr=TQ.episodes_and_truth(px[px.index<=SEAL], s2[s2.index<=SEAL]);\n"
                "E=TQ.attach(E,rd);\n"
                "cut=float(E[E.era=='is'].A3_currency_leg_gap.median());\n"
                "E['tag']=np.where(E.A3_currency_leg_gap>=cut,'high','low');\n"
                "g=E[E.era=='holdout'].groupby('tag').true_trend.agg(['size','mean']);\n"
                "print('CUT %.6f' % cut);\n"
                "print('HIGH %d %.4f' % (g.loc['high','size'], g.loc['high','mean']));\n"
                "print('LOW %d %.4f' % (g.loc['low','size'], g.loc['low','mean']));\n"
                "q=rd['A3_currency_leg_gap'];\n"
                "rows=[];\n"
                "for p in s2.columns:\n"
                "    v=s2[p]; qq=q[p] if p in q.columns else pd.Series(np.nan,index=s2.index);\n"
                "    for d in s2.index:\n"
                "        lab=v.get(d,'')\n"
                "        if not isinstance(lab,str) or lab=='': continue\n"
                "        x=float(qq.get(d,np.nan));\n"
                "        rows.append((d,p,lab,float(x) if np.isfinite(x) else np.nan,\n"
                "          '' if not (lab=='trending' and np.isfinite(x)) else ('high' if x>=cut else 'low')))\n"
                "R=pd.DataFrame(rows,columns=['date','pair','shape2','quality_reading','quality_tag']);\n"
                "R.to_csv('/tmp/_l1v_recomputed.csv',index=False);\n"
                "print('ROWS %d' % len(R));\n")
            r = run([sys.executable, '-c', code], cwd=clone, env=env)
            o = r.stdout
            cut = float(re.search(r'CUT ([\d.]+)', o).group(1)) if 'CUT' in o else np.nan
            hi = re.search(r'HIGH (\d+) ([\d.]+)', o); lo = re.search(r'LOW (\d+) ([\d.]+)', o)
            nrw = int(re.search(r'ROWS (\d+)', o).group(1)) if 'ROWS' in o else -1
            if not np.isfinite(cut):
                row(3, 'quality series recomputed independently in the clone', 'FAIL', (r.stderr or o)[-220:])
            else:
                # the claim is whatever the SHIPPED file states, never a literal in this
                # script -- a hardcoded number here just re-asserts yesterday's answer
                hdr = open(qp).readline()
                m_cut = re.search(r'cut ([\d.]+)', hdr)
                claim = float(m_cut.group(1)) if m_cut else float('nan')
                row(3, 'tuning-window cut re-derived independently (shipped header claims %.6f)' % claim,
                    'PASS' if (np.isfinite(claim) and abs(cut - claim) < 1e-6) else 'FAIL', 'recomputed %.6f' % cut)
                if hi and lo:
                    nh, rh = int(hi.group(1)), float(hi.group(2)); nl, rl = int(lo.group(1)), float(lo.group(2))
                    txtp = qp.replace('.csv', '.txt')
                    cl = {}
                    if os.path.exists(txtp):
                        for ln in open(txtp):
                            mm = re.match(r'\s*(?:holdout\s+)?(high|low)\s+(\d+)\s+([\d.]+)', ln)
                            if mm and 'holdout' in ln or (mm and cl.get('seen_holdout')):
                                cl[mm.group(1)] = (int(mm.group(2)), float(mm.group(3)))
                            if 'holdout' in ln and mm:
                                cl['seen_holdout'] = True
                    ch, clo = cl.get('high'), cl.get('low')
                    ok = bool(ch and clo and ch[0] == nh and abs(ch[1] - rh) < 0.0015
                              and clo[0] == nl and abs(clo[1] - rl) < 0.0015)
                    row('3a', 'holdout rates re-derived (shipped .txt claims high %s / low %s)'
                        % (('%d@%.3f' % ch) if ch else '?', ('%d@%.3f' % clo) if clo else '?'),
                        'PASS' if ok else 'FAIL', 'recomputed high %.1f%% n=%d, low %.1f%% n=%d'
                        % (100 * rh, nh, 100 * rl, nl))
                S = pd.read_csv(qp, comment='#', parse_dates=['date'])
                RC = pd.read_csv('/tmp/_l1v_recomputed.csv', parse_dates=['date'])
                j = S.merge(RC, on=['date', 'pair'], how='outer', suffixes=('_ship', '_re'), indicator=True)
                only = int((j._merge != 'both').sum())
                tag_mis = int((j.quality_tag_ship.fillna('') != j.quality_tag_re.fillna('')).sum())
                val = (j.quality_reading_ship - j.quality_reading_re).abs()
                val_mis = int((val > 1e-9).sum())
                row('3b', 'shipped CSV matches the independent recomputation row for row',
                    'PASS' if (only == 0 and tag_mis == 0 and val_mis == 0) else 'FAIL',
                    '%d rows one-sided, %d tag mismatches, %d reading mismatches (of %d)'
                    % (only, tag_mis, val_mis, len(j)))

        # ---- 4. the seal, through every public loader, in the clone
        code = (
            "import os,sys; sys.path.insert(0,'code');\n"
            "os.environ.pop('FX_ALLOW_W4',None);\n"
            "import pandas as pd, l2sweep as S, l2route as R;\n"
            "d=S.load_pair('EURUSD'); print('LOADPAIR %s' % d.index.max().date());\n"
            "sh,ac=R.load_states('results/layer1_states.csv'); print('LOADSTATES %s' % sh.index.max().date());\n"
            "q=pd.read_csv('results/layer1_trend_quality_series.csv',comment='#',parse_dates=['date']);\n"
            "sealed=q[q.date>pd.Timestamp('2020-12-31')];\n"
            "print('QSEALED %d %s' % (len(sealed), 'all' if (len(sealed)==0 or (sealed['sample']=='sealed').all()) else 'MIXED'));\n"
            "st=pd.read_csv('results/layer1_states.csv',comment='#',parse_dates=['date']);\n"
            "ss=st[st.date>pd.Timestamp('2020-12-31')];\n"
            "print('SSEALED %d %s' % (len(ss), 'all' if (len(ss)==0 or (ss['sample']=='sealed').all()) else 'MIXED'));\n")
        r = run([sys.executable, '-c', code], cwd=clone)
        o = r.stdout
        if 'LOADPAIR' not in o:
            row(4, 'loader seal test in the clone', 'FAIL', (r.stderr or o)[-220:])
        else:
            lp = pd.Timestamp(re.search(r'LOADPAIR (\S+)', o).group(1))
            ls = pd.Timestamp(re.search(r'LOADSTATES (\S+)', o).group(1))
            row(4, 'l2sweep.load_pair refuses bars after 2020-12-31', 'PASS' if lp <= SEAL else 'FAIL', 'max %s' % lp.date())
            row('4a', 'l2route.load_states refuses bars after 2020-12-31', 'PASS' if ls <= SEAL else 'FAIL', 'max %s' % ls.date())
            m = re.search(r'QSEALED (\d+) (\S+)', o)
            if m:
                row('4b', 'quality series rows after the seal are tagged sample=sealed',
                    'PASS' if m.group(2) == 'all' else 'FAIL', '%s rows, %s tagged' % (m.group(1), m.group(2)))
            m = re.search(r'SSEALED (\d+) (\S+)', o)
            if m:
                row('4c', 'states rows after the seal are tagged sample=sealed',
                    'PASS' if m.group(2) == 'all' else 'FAIL', '%s rows, %s tagged' % (m.group(1), m.group(2)))

        # ---- 5. sanity constants from the clone's own panel
        # THE CONSTANTS BELONG TO THE PANEL THAT ASSERTS THEM. 1.6010 / 0.7296 are the
        # H.10 NOON extremes asserted by build.py on data/px28_h10.csv. The live 5pm
        # panel is 1.5991 / 0.7209 -- documented in build5pm.py lines 26-29, because the
        # SNB-era low printed after noon. Checking the brief's numbers against px28.csv
        # was MY error on the first pass; both panels are checked here against their own
        # documented values.
        h10 = pd.read_csv(os.path.join(clone, 'data', 'px28_h10.csv'), index_col=0, parse_dates=True)
        pk = float(h10['EURUSD'].max()); lo_ = float(h10['USDCHF'].min())
        row(5, 'H.10 panel: EURUSD peak 1.6010, USDCHF low 0.7296 (build.py asserts these)',
            'PASS' if (abs(pk - 1.6010) < 5e-4 and abs(lo_ - 0.7296) < 5e-4) else 'FAIL',
            'EURUSD %.4f, USDCHF %.4f' % (pk, lo_))
        px = pd.read_csv(os.path.join(clone, 'data', 'px28.csv'), index_col=0, parse_dates=True)
        pk5 = float(px['EURUSD'].max()); lo5 = float(px['USDCHF'].min())
        row('5a', '5pm panel: EURUSD peak 1.5991, USDCHF low 0.7209 (build5pm.py documents these)',
            'PASS' if (abs(pk5 - 1.5991) < 5e-4 and abs(lo5 - 0.7209) < 5e-4) else 'FAIL',
            'EURUSD %.4f, USDCHF %.4f' % (pk5, lo5))

        # ---- 6. the app, from clone files only
        r = run(['node', '--check', os.path.join(clone, 'app_ui.js')])
        row(6, 'node --check app_ui.js in the clone', 'PASS' if r.returncode == 0 else 'FAIL', (r.stderr or '')[:140])
        ad = os.path.join(clone, 'app_data.json')
        if os.path.exists(ad):
            D = json.load(open(ad)); ui = open(os.path.join(clone, 'app_ui.js')).read()
            miss = []
            for sec, fn, tab in (('dc_axis', 'dcFill', 'dc'), ('trend_round2', 'tr2Fill', 'tr2'),
                                 ('trend_quality', 'tqFill', 'tq'), ('crisis_witnesses', 'cwFill', 'cw')):
                if sec not in D:
                    miss.append('%s section' % sec)
                if fn + '(' not in ui:
                    miss.append('%s()' % fn)
                if ("data-t=\"%s\"" % tab) not in ui:
                    miss.append('%s nav button' % tab)
                if ("id=\"%s\"" % tab) not in ui:
                    miss.append('%s section div' % tab)
            row('6a', 'every Layer 1 tab has its data section, renderer, nav button and div in the clone',
                'PASS' if not miss else 'FAIL', '; '.join(miss[:6]) if miss else 'dc, tr2, tq, cw all complete')
            # headless boot: the renderers must run against the clone's own app_data
            boot = os.path.join(tmp, 'boot.js')
            # A REAL LOAD, not a regex extract. The first pass eval'd the four functions
            # out of the file and they were not defined in the eval scope -- a harness
            # bug that reported a working app as broken. Here app_ui.js is loaded whole
            # into a vm context with the DOM stubs the renderers touch, which is as close
            # to a headless boot as this app gets without a browser.
            open(boot, 'w').write(
                "const fs=require('fs'), vm=require('vm');\n"
                "const src=fs.readFileSync(%r,'utf8');\n"
                "const D=JSON.parse(fs.readFileSync(%r,'utf8'));\n"
                "const mk=()=>({innerHTML:'',hidden:false,setAttribute(){},dataset:{},"
                "  appendChild(){},addEventListener(){},classList:{add(){},remove(){}},style:{},value:''});\n"
                "const ctx={D:D,console:console,Math:Math,JSON:JSON,Date:Date,isNaN:isNaN,parseFloat:parseFloat,\n"
                "  setTimeout(){},fetch(){return Promise.resolve({json:()=>({}),text:()=>''})},\n"
                "  document:{getElementById:mk,querySelector:mk,querySelectorAll:()=>[],createElement:mk,\n"
                "    addEventListener(){},body:mk()}};\n"
                "ctx.window=ctx; ctx.globalThis=ctx;\n"
                "vm.createContext(ctx);\n"
                "try{ new vm.Script(src).runInContext(ctx); }catch(e){ console.log('LOADFAIL '+e.message); }\n"
                "const ok=[];\n"
                "for(const n of ['dcFill','tr2Fill','tqFill','cwFill']){\n"
                "  if(typeof ctx[n]!=='function'){ console.log('MISSING '+n); continue; }\n"
                "  try{ ctx[n](); ok.push(n); }catch(e){ console.log('BOOTFAIL '+n+' '+e.message); }\n"
                "}\n"
                "console.log('BOOTOK '+ok.join(','));\n" % (os.path.join(clone, 'app_ui.js'), ad))
            r = run(['node', boot])
            okl = re.search(r'BOOTOK (\S*)', r.stdout)
            got = okl.group(1).split(',') if okl and okl.group(1) else []
            row('6b', 'headless boot: all four renderers execute against clone app_data.json',
                'PASS' if len([x for x in got if x]) == 4 else 'FAIL',
                'ran %s%s' % (','.join(got), ('; ' + r.stdout.strip().splitlines()[0]) if 'BOOTFAIL' in r.stdout else ''))
        else:
            row('6a', 'app_data.json in the clone', 'FAIL', 'absent')

        # ---- 7. every number in the contract against its named source
        if os.path.exists(doc):
            txt = open(doc).read()
            checks = []
            def src(p):
                fp = os.path.join(clone, p)
                return pd.read_csv(fp, comment='#', low_memory=False) if os.path.exists(fp) else None
            V = src('results/trend_quality_verdict_2026-11-11.csv')
            if V is not None and (V.candidate == 'A3_currency_leg_gap').any():
                a3 = V[V.candidate == 'A3_currency_leg_gap'].iloc[0]
                for pat, val, name in ((r'p=([\d.]+) sign', a3.null_p_sign, 'quality null p sign'),
                                       (r'/ ([\d.]+) permutation', a3.null_p_perm, 'quality null p perm'),
                                       (r'AUC ([\d.]+)', a3.auc_holdout, 'quality AUC holdout')):
                    m = re.search(pat, txt)
                    if m:
                        checks.append((name, float(m.group(1)), float(val), 'results/trend_quality_verdict_2026-11-11.csv'))
            W = src('results/witness_validation_2026-11-15.csv')
            if W is not None:
                ac = W[W.witness == 'ACUTE_maxabsmove'].iloc[0]; mv = W[W.witness == 'MOVE_rel'].iloc[0]
                m = re.search(r'acute \(maxabsmove\) \| (\d+) of (\d+) \| ([\d.]+) \| ([\d.]+)x', txt)
                if m:
                    checks += [('acute caught', float(m.group(1)), float(ac.caught), 'results/witness_validation_2026-11-15.csv'),
                               ('acute n_events', float(m.group(2)), float(ac.n_events), 'results/witness_validation_2026-11-15.csv'),
                               ('acute recall', float(m.group(3)), float(ac.recall), 'results/witness_validation_2026-11-15.csv'),
                               ('acute lift', float(m.group(4)), float(ac.lift), 'results/witness_validation_2026-11-15.csv')]
                m = re.search(r'MOVE \(relative level\) \| (\d+) of (\d+) \| ([\d.]+) \| ([\d.]+)x', txt)
                if m:
                    checks += [('MOVE caught', float(m.group(1)), float(mv.caught), 'results/witness_validation_2026-11-15.csv'),
                               ('MOVE lift', float(m.group(4)), float(mv.lift), 'results/witness_validation_2026-11-15.csv')]
            qt = os.path.join(clone, 'results', 'layer1_trend_quality_series.txt')
            if os.path.exists(qt):
                o = open(qt).read()
                m = re.search(r'holdout high\s+(\d+)\s+([\d.]+)', o)
                if m:
                    d2 = re.search(r'true-trend rate ([\d.]+)% \(n=(\d+)\) for high', txt) or \
                         re.search(r'rate ([\d.]+)% \(n=(\d+)\) for high', txt)
                    if d2:
                        checks += [('quality high rate', float(d2.group(1)) / 100, float(m.group(2)),
                                    'results/layer1_trend_quality_series.txt'),
                                   ('quality high n', float(d2.group(2)), float(m.group(1)),
                                    'results/layer1_trend_quality_series.txt')]
            A = src('results/trend_anatomy_truth_table_2026-11-10.csv')
            if A is not None:
                for era, pat in (('is', r'true-trend share ([\d.]+)% tuning'), ('holdout', r'([\d.]+)% holdout')):
                    m = re.search(pat, txt)
                    if m:
                        checks.append(('true-trend share %s' % era, float(m.group(1)) / 100,
                                       float(A[A.era == era].true_trend.mean()),
                                       'results/trend_anatomy_truth_table_2026-11-10.csv'))
            det = []
            nbad = 0
            for name, claimed, actual, f in checks:
                ok = abs(claimed - actual) <= max(0.002, abs(actual) * 0.01)
                det.append('%s %s (doc %.4g vs %s %.4g)' % (name, 'MATCH' if ok else 'MISMATCH', claimed, os.path.basename(f), actual))
                nbad += (not ok)
            row(7, 'every number in LAYER1_INTERFACE.md matches its named source file',
                'PASS' if (checks and nbad == 0) else 'FAIL',
                '%d checked, %d mismatched | %s' % (len(checks), nbad, ' | '.join(det[:6])))
            pd.DataFrame([dict(number=n, doc_value=c, source_value=v, source_file=f,
                               verdict='MATCH' if abs(c - v) <= max(0.002, abs(v) * 0.01) else 'MISMATCH')
                          for n, c, v, f in checks]).to_csv(a.out.replace('.csv', '_numbers.csv'), index=False)

        # ---- 8. the two audits must agree
        ca = os.path.join(clone, 'results', 'LAYER1_CLOSEOUT_AUDIT.csv')
        if not os.path.exists(ca):
            row(8, 'chain audit LAYER1_CLOSEOUT_AUDIT.csv present in the clone', 'FAIL',
                'absent -- the chain has not pushed it')
        else:
            C = pd.read_csv(ca)
            mine = pd.DataFrame(ROWS)
            chain_fail = C[C.status != 'PASS']
            my_fail = mine[mine.status != 'PASS']
            agree = (len(chain_fail) == 0) == (len(my_fail) == 0)
            row(8, 'chain audit and this independent audit agree',
                'PASS' if agree else 'FAIL',
                'chain %d/%d PASS, independent %d/%d PASS'
                % (int((C.status == 'PASS').sum()), len(C), int((mine.status == 'PASS').sum()), len(mine)))

        # ---- 9. git alignment
        loc = run(['git', 'rev-parse', 'HEAD'], cwd='/Users/jackcuster/fx-data').stdout.strip()
        orig = run(['git', 'rev-parse', 'origin/main'], cwd='/Users/jackcuster/fx-data').stdout.strip()
        row(9, 'local ~/fx-data HEAD == origin/main == clone HEAD',
            'PASS' if (loc == orig == sha) else 'FAIL',
            'local %s, origin %s, clone %s' % (loc[:10], orig[:10], sha[:10]))
        un = run(['git', 'status', '--short'], cwd='/Users/jackcuster/fx-data').stdout.strip().splitlines()
        unt = [x for x in un if x.startswith('??')]
        row('9a', 'nothing untracked locally that is work product',
            'PASS' if all('px28_5pm_to2020' in x or '.claude' in x for x in unt) else 'FAIL',
            '; '.join(unt) if unt else 'clean')
    finally:
        A = pd.DataFrame(ROWS)
        A['clone_sha'] = sha
        A.to_csv(a.out, index=False)
        n = int((A.status == 'PASS').sum())
        print('\n%d of %d PASS -> %s   clone %s   %.1f min'
              % (n, len(A), a.out, sha[:12], (time.time() - t0) / 60), flush=True)
        if n < len(A):
            print('FAILURES:', flush=True)
            print(A[A.status != 'PASS'][['n', 'check', 'detail']].to_string(index=False), flush=True)
        if not a.keep:
            shutil.rmtree(tmp, ignore_errors=True)
            print('temp clone deleted (%s)' % tmp, flush=True)
        else:
            print('temp clone KEPT at %s' % clone, flush=True)


if __name__ == '__main__':
    main()
