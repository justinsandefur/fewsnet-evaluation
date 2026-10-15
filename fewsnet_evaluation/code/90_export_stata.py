"""Export analysis-ready CSVs for the Stata replication (stata/).

Python keeps the jobs Stata is bad at: fetching, panel building, polygon overlays, text
extraction, gradient-boosted predictions (exported as out-of-sample predictions, not models)
and figures. Each module in code/export_stata/ writes the plain CSVs one group of do-files
needs into stata/data/; see each module's docstring for its files.

This script also writes:
  python_numbers.csv   every \\newcommand in output/cgd_paper/numbers.tex (name, printed value,
                       in_paper = printed in the paper or its tables)
  python_tables.csv    reference values for table cells (name, value), appended by the modules

Run after the Python pipeline (code/40_paper.py and 41_paper_tables.py):
    ../.venv/bin/python code/90_export_stata.py            # all modules
    ../.venv/bin/python code/90_export_stata.py errors     # one module
"""
import importlib.util
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "stata" / "data"
OUT.mkdir(parents=True, exist_ok=True)


def python_numbers():
    s = (ROOT / "output" / "cgd_paper" / "numbers.tex").read_text()
    rows = re.findall(r"\\newcommand\{\\(\w+)\}\{(.*)\}\s*$", s, re.M)
    d = pd.DataFrame(rows, columns=["name", "value"])
    d["value"] = (d.value.str.replace(r"\\textminus\{\}", "-", regex=True).str.replace(r"\\[,!]", "", regex=True)
                  .str.replace(r"\\%", "", regex=True).str.replace("$", "", regex=False).str.strip())
    # in_paper = 1 if the macro is printed in the paper or its tables (numbers.tex also holds
    # macros for material moved to the companion papers)
    tex = (ROOT / "output" / "cgd_paper" / "fewsnet_evaluation.tex").read_text()
    tex += "".join(f.read_text() for f in (ROOT / "output" / "cgd_paper" / "tables").glob("*.tex"))
    d["in_paper"] = [int(bool(re.search(r"\\" + n + r"(?![A-Za-z])", tex))) for n in d.name]
    # ranges ("44 to 115", "2014--2025") become NAME_lo and NAME_hi
    rng = d.value.str.fullmatch(r"(-?[\d.,]+)\s*(?:to|--)\s*(-?[\d.,]+)")
    lohi = d[rng].value.str.extract(r"(-?[\d.,]+)\s*(?:to|--)\s*(-?[\d.,]+)")
    extra = pd.concat([d[rng].assign(name=d[rng].name + "_lo", value=lohi[0]),
                       d[rng].assign(name=d[rng].name + "_hi", value=lohi[1])])
    d = pd.concat([d, extra], ignore_index=True)
    d.to_csv(OUT / "python_numbers.csv", index=False)
    print(f"python_numbers.csv: {len(d)} macros")


def main(only=None):
    python_numbers()
    for f in sorted((ROOT / "code" / "export_stata").glob("[!_]*.py")):
        if only and f.stem != only:
            continue
        spec = importlib.util.spec_from_file_location(f.stem, f)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        print(f"-- {f.stem}")
        m.export(OUT)
    parts = sorted(OUT.glob("python_tables_*.csv"))
    if parts:
        pd.concat([pd.read_csv(p) for p in parts]).to_csv(OUT / "python_tables.csv", index=False)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
