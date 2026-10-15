import os, numpy as np, pytest
import gridloom_expand as P
CASE=os.path.join(os.path.dirname(__file__),'..','examples','synthetic_4node')

@pytest.fixture(scope='module')
def case(): return P.Case(CASE)

def test_rep_days():
    H,seg,w=P.rep_days(); assert len(H)==288 and abs(w.sum()/24-365)<1e-9

def test_expansion_builds(case):
    b=P.expand_year(case,2027,log=lambda s:None)
    assert set(b.kind)<={'gen','line'} and b.MW.min()>=-1e-6 and b.MW.sum()>1
    assert (b.year==2027).all()

def test_case_files_are_synthetic():
    import json
    assert 'SYNTHETIC' in json.load(open(os.path.join(CASE,'case.json')))['description']
