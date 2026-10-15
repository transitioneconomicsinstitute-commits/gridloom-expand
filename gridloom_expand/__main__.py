"""Command line: python -m gridloom_expand CASE_DIR OUT_DIR --year Y"""
import argparse, os
from . import Case, expand_year

def main():
    a=argparse.ArgumentParser(prog='gridloom-expand')
    a.add_argument('case'); a.add_argument('out'); a.add_argument('--year',type=int,required=True)
    A=a.parse_args(); C=Case(A.case); os.makedirs(A.out,exist_ok=True)
    expand_year(C,A.year).to_csv(os.path.join(A.out,'builds.csv'),index=False)
    print('done')

if __name__=='__main__':
    main()
