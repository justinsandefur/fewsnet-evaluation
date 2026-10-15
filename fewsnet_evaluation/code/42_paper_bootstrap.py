"""Wild cluster bootstrap p-values (country clusters, Rademacher, null imposed) for the paper's headline
coefficients, where few countries make cluster-robust standard errors unreliable."""
import importlib.util, json, warnings
from pathlib import Path
import pandas as pd
warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fr", ROOT / "code" / "28_flag_release.py")
FR = importlib.util.module_from_spec(spec); spec.loader.exec_module(FR)
INP = ROOT / "input" / "panel"
out = {}
d = pd.read_parquet(INP / "official_projections.parquet")
for samp, dd in [("all", d), ("new", d[d.last3 == 0])]:
    xs = ["proj3", "fews_fc3"] + (["last3"] if samp == "all" else [])
    dd = dd.dropna(subset=xs)
    for t in ["proj3", "fews_fc3"]:
        out[f"official_{samp}_{t}"] = FR.wild_p(dd, "next3", xs, t, ["cell"], reps=1999)
p = pd.read_parquet(INP / "fewsnet_contribution_panel.parquet")
print(json.dumps(out, indent=1))
(ROOT / "output" / "cgd_paper" / "bootstrap.json").write_text(json.dumps(out, indent=1))
