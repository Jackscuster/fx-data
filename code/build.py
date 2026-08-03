import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA=os.path.join(_R,'data'); os.makedirs(DATA,exist_ok=True)
import pandas as pd, numpy as np, itertools, urllib.request
URL='https://raw.githubusercontent.com/datasets/exchange-rates/main/data/daily.csv'
ex=os.path.join(DATA,'ex.csv')
urllib.request.urlretrieve(URL,ex)
M={'Euro':'EUR','United Kingdom':'GBP','Australia':'AUD','New Zealand':'NZD',
   'Canada':'CAD','Switzerland':'CHF','Japan':'JPY'}
d=pd.read_csv(ex); d=d[d.Country.isin(M)].copy()
d['C']=d.Country.map(M); d['Date']=pd.to_datetime(d.Date)
d['Exchange rate']=pd.to_numeric(d['Exchange rate'],errors='coerce')
w=d.pivot_table(index='Date',columns='C',values='Exchange rate')
u=1.0/w; u['USD']=1.0; u=u.loc['1999-01-04':].dropna()
PRI=['EUR','GBP','AUD','NZD','USD','CAD','CHF','JPY']
px=pd.DataFrame(index=u.index)
for a,b in itertools.combinations(PRI,2): px[a+b]=u[a]/u[b]
px.to_csv(os.path.join(DATA,'px28.csv'))
print('px28',px.shape,px.index.max().date())
assert abs(px.EURUSD.max()-1.601)<.01 and abs(px.USDCHF.min()-0.7296)<.01, 'data sanity check failed'
print('sanity checks passed')
