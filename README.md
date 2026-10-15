# Gridloom Expand

Gridloom Expand finds least-cost builds of new generators and transmission lines for a power system. Builds are co-optimised with hourly operations on 12 representative days (the 15th of each month, weighted by the days in that month). Capital costs enter as a one-year annuity.

It is built on [Gridloom Dispatch](https://github.com/transitioneconomicsinstitute-commits/gridloom-dispatch), which supplies the case reader and the LP solver wrapper.

This is the **v0.1.0** core: a single planning year, thermal/solar/wind candidates, and transport-style candidate lines. Multi-year rolling plans, storage, checkpoints and full-year dispatch checks live in later releases.

## Install

```
pip install -e ../gridloom-dispatch
pip install -e .[test]
```

## Quick start

```
python -m gridloom_expand examples/synthetic_4node out --year 2027
```

Writes `out/builds.csv` with columns `year,name,kind,MW`.

From Python:

```python
import gridloom_expand as ge
case = ge.Case('examples/synthetic_4node')
builds = ge.expand_year(case, 2027)
```

## Example data

`examples/synthetic_4node` is a **synthetic** four-node system made by `scripts/make_synthetic_case.py` (seed 42), with candidate plants and lines. The numbers are invented for testing and do not describe any real power system.

## Case format

Same as Gridloom Dispatch, plus:

| File | Columns |
|---|---|
| `candidates_gen.csv` | `name`, `node`, `type` (`thermal`, `solar`, `wind`), `capex_usd_kw`, `life`, `max_mw`, plus operating fields as in generators.csv |
| `candidates_lines.csv` | `name`, `from`, `to`, `max_mw`, `x_pu`, `capex_usd_mw`, `life` |

## Tests

```
python -m pytest -q
```

## Licence

MIT. Copyright (c) 2026 Transition Economics Institute. See `LICENSE`. Please cite using `CITATION.cff`.
