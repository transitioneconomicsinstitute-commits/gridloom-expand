"""Single-year economic expansion of generators and transmission on representative days."""
import numpy as np, pandas as pd
from gridloom_dispatch.lp import LP
from gridloom_dispatch.case import crf, num, CAL

def rep_days():
    """12 representative days (15th of each month), weighted by days in month."""
    H=[]; seg=[]; wt=[]
    for m in range(1,13):
        i0=CAL.get_loc(CAL[(CAL.month==m)&(CAL.day==15)&(CAL.hour==0)][0]); s=len(H)
        H+=list(range(i0,i0+24)); seg.append((s,s+24)); wt+=[CAL[CAL.month==m].day.nunique()]*24
    return np.array(H), seg, np.array(wt,float)

def _candidates(case):
    K=[]
    cg=getattr(case,'cand_gen',None); cl=getattr(case,'cand_lines',None)
    if cg is not None:
        for r in cg.to_dict('records'):
            K.append(dict(kind='gen',name=r['name'],type=r['type'],bus=int(r['node']),
                capex=r['capex_usd_kw']*1e3,life=int(r['life']),mx=num(r.get('max_mw'),np.inf),
                hr=num(r.get('heat_rate'),0),fp=num(r.get('fuel_usd_mmbtu'),0),vom=num(r.get('vom'),0),
                profile=r.get('profile')))
    if cl is not None:
        for r in cl.to_dict('records'):
            K.append(dict(kind='line',name=r['name'],frm=int(r['from']),to=int(r['to']),
                capex=r['capex_usd_mw'],life=int(r['life']),mx=float(r['max_mw']),x=float(r['x_pu'])))
    return K

def expand_year(case, year, log=print):
    """Co-optimise new generators and lines for one year on 12 representative days.
    Capital cost is the first-year annuity (CRF). Returns a DataFrame of builds."""
    H,seg,wd=rep_days(); c=case.cfg; DISC=c['discount_rate']
    nodes=case.nodes; nid=nodes.node.values.astype(int); ni={b:i for i,b in enumerate(nid)}; N=len(nid)
    K=_candidates(case); lp=LP(); NV={}
    for k in K:
        NV[k['name']]=lp.var((),k['capex']*crf(DISC,k['life']),0,k['mx'])
    T=len(H); w=wd; L=case.load(year,H); bal=lp.rows((N,T),L,L)
    # existing generators
    for g in case.generators.to_dict('records'):
        b=ni[int(g['node'])]; cap=float(g['mw']); t=g['type']
        if t=='thermal':
            cost=(num(g.get('heat_rate'),0)*num(g.get('fuel_usd_mmbtu'),0)+num(g.get('vom'),0))*w
            gen=lp.var((T,),cost,0,cap)
        elif t in ('solar','wind'):
            cf=case.profiles[g['profile']].values[H]
            gen=lp.var((T,),num(g.get('vom'),0)*w,0,cap*cf)
        else:
            raise ValueError(f'core expand supports thermal, solar and wind existing plant; got {t!r}')
        lp.a(bal[b],gen)
    # candidate generators
    for k in K:
        if k['kind']!='gen': continue
        b=ni[k['bus']]; inv=NV[k['name']]
        if k['type']=='thermal':
            cost=(k['hr']*k['fp']+k['vom'])*w; gen=lp.var((T,),cost)
            r=lp.rows((T,),-np.inf,0); lp.a(r,gen); lp.a(r,inv,-1)
        elif k['type'] in ('solar','wind'):
            cf=case.profiles[k['profile']].values[H]; gen=lp.var((T,),k['vom']*w)
            r=lp.rows((T,),-np.inf,0); lp.a(r,gen); lp.a(r,inv,-cf)
        else:
            raise ValueError(f'core expand supports thermal, solar and wind candidates; got {k["type"]!r}')
        lp.a(bal[b],gen)
    # existing lines (DC)
    th=lp.var((N,T),0,-np.inf,np.inf)
    for r in case.branches.to_dict('records'):
        a_,b_=int(r['from']),int(r['to']); mva=float(r['MVA']); x=float(r['x_pu'])
        loss=float(r.get('loss_pct',c['line_loss_frac']*100))/100
        ia,ib=ni[a_],ni[b_]
        fp=lp.var((T,),c['flow_cost_usd_mwh']*w,0,mva); fm=lp.var((T,),c['flow_cost_usd_mwh']*w,0,mva)
        row=lp.rows((T,),0,0); lp.a(row,fp); lp.a(row,fm,-1); lp.a(row,th[ia],-1/x); lp.a(row,th[ib],1/x)
        lp.a(bal[ia],fp,-1); lp.a(bal[ia],fm,1-loss); lp.a(bal[ib],fp,1-loss); lp.a(bal[ib],fm,-1)
    rr=lp.rows((T,),0,0); lp.a(rr,th[ni[int(c['ref_node'])]])
    # candidate lines as transport links
    loss=c['line_loss_frac']
    for k in K:
        if k['kind']!='line': continue
        ia,ib=ni[k['frm']],ni[k['to']]; inv=NV[k['name']]
        fp=lp.var((T,),c['flow_cost_usd_mwh']*w); fm=lp.var((T,),c['flow_cost_usd_mwh']*w)
        for f in (fp,fm):
            row=lp.rows((T,),-np.inf,0); lp.a(row,f); lp.a(row,inv,-1)
        lp.a(bal[ia],fp,-1); lp.a(bal[ia],fm,1-loss); lp.a(bal[ib],fp,1-loss); lp.a(bal[ib],fm,-1)
    use=lp.var((N,T),c['voll_usd_mwh']*w[None,:],0,L); lp.a(bal,use)
    st,x,_=lp.solve()
    if st!='Optimal': raise RuntimeError(f'expansion {year}: {st}')
    log(f'expansion {year} {st}')
    kinds={k['name']:k['kind'] for k in K}
    rows=[dict(year=year,name=nm,kind=kinds[nm],MW=float(x[v])) for nm,v in NV.items()]
    return pd.DataFrame(rows)

class Case:
    """Case folder reader that also loads candidate CSVs for expansion."""
    def __init__(s,path):
        from gridloom_dispatch.case import Case as Base
        import os
        base=Base(path)
        s.path=path; s.cfg=base.cfg; s.nodes=base.nodes; s.generators=base.generators
        s.branches=base.branches; s.profiles=base.profiles
        def r(f):
            p=os.path.join(path,f)
            return pd.read_csv(p) if os.path.exists(p) else None
        s.cand_gen=r('candidates_gen.csv'); s.cand_lines=r('candidates_lines.csv')
    def load(s,year,hours):
        from gridloom_dispatch.case import Case as Base
        return Base.load(s,year,hours)
