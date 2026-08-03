import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTDATA,exist_ok=True); os.makedirs(ROOTOUT,exist_ok=True)
sys.path.insert(0,ROOTLIB)
import json, pandas as pd, numpy as np, os
R=os.path.join(ROOTOUT,'/'.lstrip('/'))
def rd(f,**k):
    try: return pd.read_csv(R+f,**k)
    except Exception: return pd.DataFrame()
def cl(d): return json.loads(d.replace({np.nan:None}).to_json(orient='records'))
sig=json.load(open(R+'app_data.json'))
out=dict(
 signals=sig,
 sweep=cl(rd('strategy_sweep.csv')),
 ladder=cl(rd('detector_ladder.csv')),
 logic=cl(rd('logic_summary.csv')),
 duration=cl(rd('duration_stats.csv')),
 funnel=cl(rd('dsr_funnel.csv')),
 audit=cl(rd('lookahead_audit.csv')),
 meta=dict(built=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M'),
           pairs=28,split='2016-01-01',
           variants=int(len(rd('logic_results.csv'))),
           dsr_pass=0, emax=1.076))
json.dump(out,open(R+'app_data.json','w'),separators=(',',':'))
print({k:(len(v) if isinstance(v,list) else 'meta') for k,v in out.items()})
print('%.0f KB'%(os.path.getsize(R+'app_data.json')/1024))
