"""Helpers shared by the export modules (imported by file path)."""
import importlib.util
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
INP, TAB = ROOT / "input", ROOT / "output" / "tables"


def load(name, file):
    """Import a numbered pipeline script (e.g. '12_errors.py') as a module."""
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def periods_to_str(d):
    """Pandas monthly periods -> 'YYYY-MM' strings, which Stata reads with monthly(x, "YM")."""
    d = d.copy()
    for c in d.columns:
        if isinstance(d[c].dtype, pd.PeriodDtype):
            d[c] = d[c].astype(str)
    return d


def table_refs(out, block, rows):
    """Write reference values for table cells: rows = [(name, value), ...]."""
    pd.DataFrame(rows, columns=["name", "value"]).to_csv(out / f"python_tables_{block}.csv", index=False)
