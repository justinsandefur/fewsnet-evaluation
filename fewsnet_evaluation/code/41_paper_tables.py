"""LaTeX tables for the CGD working paper (output/cgd_paper/tables/)."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "output" / "tables"
OUT = ROOT / "output" / "cgd_paper" / "tables"
OUT.mkdir(parents=True, exist_ok=True)


def cell(b, se, scale=1.0, d=3):
    if pd.isna(b):
        return "", ""
    b, se = b * scale, se * scale
    t = abs(b / se) if se > 0 else 0
    star = "^{***}" if t > 2.576 else "^{**}" if t > 1.96 else "^{*}" if t > 1.645 else ""
    return f"${b:.{d}f}{star}$", f"$({se:.{d}f})$"


def official():
    R = pd.read_csv(TAB / "official_projections.csv")
    specs = ["official projection only", "FEWS NET forecast only", "both", "both + last official analysis",
             "both + last analysis + FEWS NET current map"]
    rows = [("proj3", "Official projection: Crisis or worse"), ("fews_fc3", "FEWS NET forecast: share of area in Crisis or worse"),
            ("last3", "Latest official analysis: Crisis or worse"), ("fews_cur3", "FEWS NET current map: share of area in Crisis or worse")]
    out = [r"\begin{tabular}{l" + "c" * len(specs) + "}", r"\toprule",
           " & " + " & ".join(f"({i + 1})" for i in range(len(specs))) + r" \\", r"\midrule"]
    for samp, lab in [("all areas", "A. All areas"), ("not in Crisis at the last analysis", "B. Areas not in Crisis at the latest official analysis")]:
        out.append(r"\multicolumn{" + str(len(specs) + 1) + r"}{l}{\textit{" + lab + r"}} \\")
        d = R[R["sample"] == samp]
        for term, name in rows:
            if samp != "all areas" and term == "last3":
                continue
            c, s = [], []
            for sp in specs:
                r = d[(d.spec == sp) & (d.term == term)]
                a, b = cell(r.coef.iloc[0], r.se.iloc[0]) if len(r) else ("", "")
                c.append(a)
                s.append(b)
            out.append(name + " & " + " & ".join(c) + r" \\")
            out.append(" & " + " & ".join(s) + r" \\")
        n = [f"{int(d[d.spec == sp].n.iloc[0]):,}" for sp in specs]
        g = [str(int(d[d.spec == sp].countries.iloc[0])) for sp in specs]
        out += ["Observations & " + " & ".join(n) + r" \\", "Countries & " + " & ".join(g) + r" \\", r"\midrule"]
    out[-1] = r"\bottomrule"
    out.append(r"\end{tabular}")
    (OUT / "official.tex").write_text("\n".join(out))


def contribution():
    R = pd.read_csv(TAB / "fewsnet_contribution.csv")
    R = R[R.block.str.startswith("accuracy") & (R["sample"] == "areas not in Crisis at last analysis")]
    A = pd.read_csv(TAB / "fewsnet_contribution_auc.csv")
    A = A[A["sample"] == "areas not in Crisis at last analysis"]
    cols = [("raw data", "current map"), ("raw data", "forecast"), ("raw data", "both"),
            ("raw data + latest Cadre Harmonise / IPC", "current map"), ("raw data + latest Cadre Harmonise / IPC", "forecast"),
            ("raw data + latest Cadre Harmonise / IPC", "both")]
    out = [r"\begin{tabular}{lcccccc}", r"\toprule",
           r" & \multicolumn{3}{c}{Without FEWS NET: rainfall,} & \multicolumn{3}{c}{Without FEWS NET: rainfall, conflict,} \\",
           r" & \multicolumn{3}{c}{conflict and prices} & \multicolumn{3}{c}{prices and latest official analysis} \\",
           r"\cmidrule(lr){2-4}\cmidrule(lr){5-7}",
           " & " + " & ".join(f"({i + 1})" for i in range(6)) + r" \\", r"\midrule"]
    for term, name in [("c_cur3", "FEWS NET current map, beyond the baseline"), ("c_fc3", "FEWS NET forecast, beyond the baseline")]:
        c, s = [], []
        for bl, sp in cols:
            r = R[(R.baseline == bl) & (R.spec == sp) & (R.term == term)]
            a, b = cell(r.coef.iloc[0], r.se.iloc[0]) if len(r) else ("", "")
            c.append(a)
            s.append(b)
        out += [name + " & " + " & ".join(c) + r" \\", " & " + " & ".join(s) + r" \\"]
    qrow = []
    for bl, sp in cols:
        r = R[(R.baseline == bl) & (R.spec == sp)]
        qrow.append(f"${r.q_coef.iloc[0]:.2f}$")
    out.append(r"Baseline's own prediction (coefficient) & " + " & ".join(qrow) + r" \\")
    n = [f"{int(R[(R.baseline == bl) & (R.spec == sp)].n.iloc[0]):,}" for bl, sp in cols]
    g = [str(int(R[(R.baseline == bl) & (R.spec == sp)].countries.iloc[0])) for bl, sp in cols]
    out += [r"\midrule", "Observations & " + " & ".join(n) + r" \\", "Countries & " + " & ".join(g) + r" \\"]
    au = []
    for bl in ["raw data", "raw data + latest Cadre Harmonise / IPC"]:
        b0 = A[(A.baseline == bl) & (A.model == "baseline")].auc.iloc[0]
        b1 = A[(A.baseline == bl) & (A.model == "baseline + FEWS NET")].auc.iloc[0]
        au.append(r"\multicolumn{3}{c}{" + f"{b0:.2f} $\\rightarrow$ {b1:.2f}" + "}")
    out += [r"AUC: baseline $\rightarrow$ adding FEWS NET & " + " & ".join(au) + r" \\", r"\bottomrule", r"\end{tabular}"]
    (OUT / "contribution.tex").write_text("\n".join(out))


def money():
    P = pd.read_csv(TAB / "aid_response_pooled.csv")
    P = P[(P.vars == "together") & (P.spec == "+ country FE (within-country)") & (P.phase == "3+")]
    C = pd.read_csv(TAB / "fewsnet_contribution.csv")
    C = C[(C.block == "funding") & (C.spec == "forecast") & C["sample"].str.contains("within country")]
    out = [r"\begin{tabular}{lcccccc}", r"\toprule",
           r" & \multicolumn{2}{c}{Map vs forecast} & \multicolumn{2}{c}{Beyond rainfall,} & \multicolumn{2}{c}{Beyond rainfall, conflict,} \\",
           r" & \multicolumn{2}{c}{} & \multicolumn{2}{c}{conflict and prices} & \multicolumn{2}{c}{prices and official analysis} \\",
           r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(lr){6-7}",
           r" & All & Food & All & Food & All & Food \\",
           " & " + " & ".join(f"({i + 1})" for i in range(6)) + r" \\", r"\midrule"]
    def get(df, **kw):
        q = df
        for k, v in kw.items():
            q = q[q[k] == v]
        return q.iloc[0] if len(q) else None
    lines = {
        "Share of areas in Crisis+, current map": [get(P, funding="all", term="current"), get(P, funding="food", term="current"), None, None, None, None],
        "Share of areas forecast in Crisis+": [get(P, funding="all", term="forecast"), get(P, funding="food", term="forecast"), None, None, None, None],
        "Forecast: part predictable from country, season and shocks": [None, None,
            get(C, baseline="raw data", term="base_fc3", sample="all funding, within country"),
            get(C, baseline="raw data", term="base_fc3", sample="food funding, within country"),
            get(C, baseline="raw data + latest Cadre Harmonise / IPC", term="base_fc3", sample="all funding, within country"),
            get(C, baseline="raw data + latest Cadre Harmonise / IPC", term="base_fc3", sample="food funding, within country")],
        "Forecast: FEWS NET's own contribution": [None, None,
            get(C, baseline="raw data", term="contrib_fc3", sample="all funding, within country"),
            get(C, baseline="raw data", term="contrib_fc3", sample="food funding, within country"),
            get(C, baseline="raw data + latest Cadre Harmonise / IPC", term="contrib_fc3", sample="all funding, within country"),
            get(C, baseline="raw data + latest Cadre Harmonise / IPC", term="contrib_fc3", sample="food funding, within country")],
    }
    for name, rs in lines.items():
        c, s = [], []
        for r in rs:
            a, b = cell(r.coef, r.se, scale=10, d=1) if r is not None else ("", "")
            c.append(a)
            s.append(b)
        out += [name + " & " + " & ".join(c) + r" \\", " & " + " & ".join(s) + r" \\"]
    nn = [get(P, funding="all", term="current").n, get(P, funding="food", term="current").n] + \
         [get(C, baseline=b, term="contrib_fc3", sample=f"{f} funding, within country").n
          for b in ["raw data", "raw data + latest Cadre Harmonise / IPC"] for f in ["all", "food"]]
    out += [r"\midrule", "Country $\\times$ map rounds & " + " & ".join(f"{int(x):,}" for x in nn) + r" \\",
            r"Countries & " + " & ".join(str(int(x)) for x in
                                         [get(P, funding="all", term="current").countries] * 2 +
                                         [get(C, baseline="raw data", term="contrib_fc3", sample="all funding, within country").countries] * 4) + r" \\",
            r"\bottomrule", r"\end{tabular}"]
    (OUT / "money.tex").write_text("\n".join(out))


def benefit():
    """Benefit-cost, crediting FEWS NET only with its distinctive information."""
    R = pd.read_csv(TAB / "benefit_cost.csv")
    R = R[(R.budget == "central") & R.attribution.isin(["A1", "A2", "A3"])]
    lab = {"A1": "All humanitarian funding; beyond data and official analyses",
           "A2": "All humanitarian funding; beyond data",
           "A3": "Food and nutrition funding; beyond data"}
    def r2(v):
        from math import floor, log10
        if pd.isna(v) or v <= 0:
            return "--"
        d = -int(floor(log10(abs(v)))) + 1
        return f"{round(v, d):,.0f}"
    def rng(v):
        """Range across mortality scenarios, smallest first (scenarios need not be monotonic)."""
        return f"{r2(v.min())}--{r2(v.max())}"
    out = [r"\begin{tabular}{lrrrrrr}", r"\toprule",
           r" & Share of aid & \multicolumn{3}{c}{Deaths averted per year} & Person-years out of & Child-years of acute \\",
           r"\cmidrule(lr){3-5}",
           r"FEWS NET credited with its distinctive information on: & attributed & Low & Central & High & Emergency+ per year & malnutrition per year \\", r"\midrule"]
    costs = []
    for a, h in lab.items():
        x = R[R.attribution == a].set_index("mortality")
        sh = x.loc["central", "mean_share_attributed"]
        dd = [r2(x.loc[m, "deaths_per_year"]) for m in ["low", "central", "high"]]
        out.append(f"{h} & {100 * sh:.1f}\\% & " + " & ".join(dd) + f" & {r2(x.loc['central', 'emergency_person_years'])}"
                   + f" & {rng(x.child_wasting_years)}" + r" \\")
        cc = [r2(x.loc[m, "cost_per_death"]) for m in ["low", "central", "high"]]
        costs.append(f"\\quad {h} & & " + " & ".join(cc) + f" & {r2(x.loc['central', 'budget_usd'] / x.loc['central', 'emergency_person_years'])}"
                     + f" & {rng(x.budget_usd / x.child_wasting_years)}" + r" \\")
    out += [r"\midrule", r"\multicolumn{7}{l}{\textit{Cost per outcome averted (US\$, budget \$45 million a year)}} \\"] + costs
    out += [r"\bottomrule", r"\end{tabular}"]
    (OUT / "benefit.tex").write_text("\n".join(out))


if __name__ == "__main__":
    benefit()
    official()
    contribution()
    money()
    for f in sorted(OUT.glob("*.tex")):
        print("=====", f.name)
        print(f.read_text())
