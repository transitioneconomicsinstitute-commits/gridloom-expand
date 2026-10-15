"""Generates the SYNTHETIC expansion example. Invented numbers; not a real system."""
import os, json, numpy as np, pandas as pd, shutil, subprocess, sys
# Reuse dispatch synthetic base, then add candidates
root=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
disp=os.path.join(root,'..','gridloom-dispatch','scripts','make_synthetic_case.py')
# Prefer sibling path used after install layout; else generate locally
O=os.path.join(root,'examples','synthetic_4node'); os.makedirs(O,exist_ok=True)
rng=np.random.default_rng(42); h=np.arange(8760); hod=h%24; doy=h//24
load=0.65+0.2*np.sin((hod-8)/24*2*np.pi).clip(0)+0.1*np.sin((hod-19)/24*2*np.pi).clip(0)+0.05*np.cos((doy-200)/365*2*np.pi)
load=load*(1+0.02*rng.standard_normal(8760)); load/=load.max()
sol=np.clip(np.sin((hod-6)/12*np.pi),0,None)*(0.85+0.15*rng.random(8760))*(0.9+0.1*np.cos((doy-172)/365*2*np.pi))
wind=np.clip(0.35+0.25*np.sin(doy/365*2*np.pi+1)+0.15*rng.standard_normal(8760).cumsum()/60,0.02,0.95)
pd.DataFrame(dict(hour=h,load=load.round(4),solar=sol.round(4),wind=wind.round(4))).to_csv(f'{O}/profiles.csv',index=False)
pd.DataFrame(dict(node=[1,2,3,4],name=['North','East','South','West'],peak_MW=[400,250,600,150])).to_csv(f'{O}/nodes.csv',index=False)
pd.DataFrame([
 dict(name='Gas CC A',node=3,type='thermal',mw=450,heat_rate=7.0,fuel_usd_mmbtu=6.0,vom=3,profile=''),
 dict(name='Gas peaker B',node=1,type='thermal',mw=200,heat_rate=10.5,fuel_usd_mmbtu=6.0,vom=6,profile=''),
 dict(name='Oil engines C',node=4,type='thermal',mw=120,heat_rate=9.8,fuel_usd_mmbtu=16.0,vom=9,profile=''),
 dict(name='Solar E',node=4,type='solar',mw=100,heat_rate=0,fuel_usd_mmbtu=0,vom=0,profile='solar'),
 dict(name='Wind F',node=1,type='wind',mw=80,heat_rate=0,fuel_usd_mmbtu=0,vom=0,profile='wind'),
]).to_csv(f'{O}/generators.csv',index=False)
pd.DataFrame([dict(name='L12',**{'from':1,'to':2},MVA=250,x_pu=0.10,loss_pct=1.5),
              dict(name='L23',**{'from':2,'to':3},MVA=300,x_pu=0.08,loss_pct=1.5),
              dict(name='L34',**{'from':3,'to':4},MVA=150,x_pu=0.12,loss_pct=2.0),
              dict(name='L14',**{'from':1,'to':4},MVA=100,x_pu=0.15,loss_pct=2.0)]).to_csv(f'{O}/branches.csv',index=False)
pd.DataFrame([dict(name='new_solar_4',node=4,type='solar',capex_usd_kw=900,life=25,max_mw=800,profile='solar'),
              dict(name='new_wind_1',node=1,type='wind',capex_usd_kw=1400,life=25,max_mw=400,profile='wind'),
              dict(name='new_ccgt_3',node=3,type='thermal',capex_usd_kw=1100,life=30,max_mw=600,heat_rate=6.5,fuel_usd_mmbtu=6.0,vom=3)]).to_csv(f'{O}/candidates_gen.csv',index=False)
pd.DataFrame([dict(name='new_L24',**{'from':2,'to':4},max_mw=300,x_pu=0.12,capex_usd_mw=250000,life=40),
              dict(name='new_L13',**{'from':1,'to':3},max_mw=300,x_pu=0.10,capex_usd_mw=300000,life=40)]).to_csv(f'{O}/candidates_lines.csv',index=False)
json.dump(dict(description='SYNTHETIC 4-node test system. Invented numbers; not a real power system.',
               base_year=2026,discount_rate=0.08,voll_usd_mwh=1500,ref_node=3),
          open(f'{O}/case.json','w'),indent=1)
open(f'{O}/README.md','w').write('# Synthetic 4-node example\n\nSYNTHETIC DATA. Invented by `scripts/make_synthetic_case.py` (seed 42). Not a real power system.\n')
print('wrote',O)
