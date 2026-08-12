import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""The magnitude axis against its OWN null. A correction.

'The magnitude reading survives at 0.881 and 0.976 against nulls of 0.378 and
0.020' was stated three times and it was not a matched comparison. The two real
values are the NINE-STATE GRID's. The two null values are from
classifier_validation.csv and belong to the THREE-STATE WEIGHTED classifier --
a different classifier, and a single pooled scalar rather than a per-property
null. The grid's magnitude separation had never been nulled at all.

This file does it properly: same classifier, same properties, its own surrogates.

AND THE SIGN SURROGATE IS NEARLY DEGENERATE HERE, which has to be said before
its numbers are read. Sign randomisation keeps every |r_t| exactly in place, so
mean absolute move is EXACTLY invariant under it and realised vol is invariant
up to a mean-squared term. The grid's scale axis is path/(vol*sqrt(L)) with
path = sum|r|, so it barely moves either. A test that cannot move the statistic
is not a test. For the magnitude axis only the IID surrogate is informative --
and beating IID mostly establishes that volatility clusters, which was never in
question.

Writes results/magnitude_null.csv.
"""
import numpy as np, pandas as pd
from structval import properties, separation, surrogate
from combined import layers, product, confirm, DWELL
from ninestate import nine
SPLIT=pd.Timestamp('2016-01-01'); MAGP=['realised_vol','avg_abs_move']
px=pd.read_csv(os.path.join(ROOTDATA,'px28.csv'),index_col=0,parse_dates=True)
fit=px.index<SPLIT; P=properties(px); sh,act=layers(px,fit)
LAB={'grid':nine(px,fit)[0],'product M=5':product(sh,act,DWELL),
     'structural M=5':confirm(sh,DWELL)}
real={k:separation(v,P).gap_sd.reindex(MAGP) for k,v in LAB.items()}
N=int(os.environ.get('FX_NSHUF',60)); rng=np.random.default_rng(11235); rows=[]
for kind in ('sign','iid'):
    acc={k:[] for k in LAB}
    for _ in range(N):
        px2=surrogate(px,kind,rng); P2=properties(px2); s2,a2=layers(px2,fit)
        for k in LAB:
            l2=(nine(px2,fit)[0] if k=='grid' else product(s2,a2,DWELL)
                if k.startswith('product') else confirm(s2,DWELL))
            acc[k].append(separation(l2,P2).gap_sd.reindex(MAGP).values)
    for k in LAB:
        A=np.array(acc[k],float)
        for i,c in enumerate(MAGP):
            v=A[:,i]; v=v[np.isfinite(v)]; r=real[k][c]
            p=(1+int((v>=r).sum()))/(len(v)+1)
            print('  %-5s %-15s %-13s real %.3f  surrogate %.3f +/- %.3f  corrected %+.3f  p=%.3f'
                  %(kind,k,c,r,v.mean(),v.std(),r-v.mean(),p))
            rows.append(dict(classifier=k,null=kind,prop=c,real=r,surrogate=v.mean(),
                             sd=v.std(),corrected=r-v.mean(),p=p))
pd.DataFrame(rows).to_csv(os.path.join(ROOTOUT,'magnitude_null.csv'),index=False)
print('wrote magnitude_null.csv')
