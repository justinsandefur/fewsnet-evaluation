"""Ethiopia US-aid-cut data assembly (inventory only, no econometrics).

Builds tidy files in input/ethiopia/tidy/:
  eth_4w_rows.parquet        harmonised OCHA Ethiopia 4W rows, Jan 2022 - Mar 2026 (woreda x partner x activity x month, donor)
  exposure_4w_zone_month.csv zone x month counts: activities, partners, US-funded activities/partners, by sector group
  exposure_4w_zone_2024.csv  pre-cut (2024) zone exposure summary + 2025 change
  exposure_cbpf_zone_year.csv  EHF (CBPF) budget by zone x year x cluster group
  smart_surveys.csv          one row per SMART/SMART+ survey (SMART+ platform + ENCU registry 2017-2024)
  hno_pin_zone.csv           HNO people in need by zone/woreda (2024, 2025 if available)

Run: .venv/bin/python -I code/77_ethiopia_assemble.py
"""
import glob, json, os, re, sys
import pandas as pd
import numpy as np

ROOT = str(__import__('pathlib').Path(__file__).resolve().parents[1])
TIDY = f'{ROOT}/input/ethiopia/tidy'
os.makedirs(TIDY, exist_ok=True)
W4 = f'{ROOT}/input/subnational_aid/hdx_3w/eth/ethiopia-operational-presence'

MONTHS = {m: i for i, m in enumerate(
    ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
     'september', 'october', 'november', 'december'], 1)}


def norm(s):
    return re.sub(r'[^a-z0-9]', '', str(s).lower())


# column role -> list of normalised header patterns (first match wins)
ROLES = {
    'month': ['reportingmonth', 'month', 'datereported'],
    'status': ['projectstatus', 'activitystatus', 'status'],
    'donor': ['donorname', 'donor', 'orgfunder'],
    'donor_acr': ['donoracronym'],
    'prog_org': ['programpartnername', 'programmeorganizationorrapidresponsemechanism',
                 'programmeorganization', 'orgprog'],
    'impl_org': ['implementingpartnername', 'implementingagencyfullname', 'implementingagencyname', 'orgimpl'],
    'impl_acr': ['implementingpartneracronym', 'implementingagencyacronym'],
    'impl_type': ['implementingpartnertype', 'implementingagencytype', 'orgimpltype'],
    'region': ['region', 'adm1name'],
    'zone': ['zone', 'adm2name'],
    'woreda': ['woreda', 'adm3name'],
    'woreda_pcode': ['hnoworedapcode', 'woredapcod', 'woredapcode', 'adm3code'],
    'sector': ['sector', 'cluster', 'sectorcluster'],
    'activity': ['clusteractivities', 'activity'],
}


def pick_sheet(path):
    if path.endswith('.csv'):
        return pd.read_csv(path, encoding='latin1', low_memory=False)
    xl = pd.read_excel(path, sheet_name=None)
    best = None
    for name, d in xl.items():
        cols = {norm(c) for c in d.columns}
        if not any(c in cols for c in ['woreda', 'adm3name']):
            continue
        if not any(c in cols for c in ['donor', 'donorname', 'orgfunder']):
            continue
        if best is None or len(d) > len(best):
            best = d
    return best


def harmonise(d):
    cols = {norm(c): c for c in d.columns}
    out = {}
    for role, pats in ROLES.items():
        for p in pats:
            if p in cols:
                out[role] = d[cols[p]]
                break
        else:
            out[role] = pd.Series([np.nan] * len(d), index=d.index)
    return pd.DataFrame(out)


def file_period(fn):
    """year and month(s) from file name"""
    y = int(re.search(r'(20\d\d)', fn).group(1))
    ms = [MONTHS[m] for m in MONTHS if m in fn.lower()]
    return y, ms


US_PAT = re.compile(r'usaid|\bbha\b|ofda|\bffp\b|united states|\bus government|\busg\b|u\.s\.|\bprm\b|'
                    r'state department|\bpepfar|\bus\b|american people|bureau for humanitarian|'
                    r'population, refugees|bureau of humanitarian', re.I)


def sector_group(s):
    s = str(s).lower()
    if 'food' in s and 'secur' not in s:
        return 'food'
    if 'food' in s or 'fsl' in s:
        return 'food'
    if 'nutri' in s:
        return 'nutrition'
    if 'health' in s:
        return 'health'
    if 'wash' in s or 'water' in s:
        return 'wash'
    if 'agri' in s:
        return 'agriculture'
    return 'other'


def build_4w():
    rows = []
    for f in sorted(glob.glob(f'{W4}/*4W*')):
        fn = os.path.basename(f)
        y, ms = file_period(fn)
        if y < 2022:
            continue
        d = pick_sheet(f)
        if d is None:
            print('no sheet', fn)
            continue
        h = harmonise(d)
        h = h[(h['woreda'].notna() | h['woreda_pcode'].notna()) & ~h['woreda'].astype(str).str.startswith('#')]
        # month: within-file month column for multi-month files, else file month
        mm = h['month'].astype(str).str.lower().str.strip().str[:3]
        m3 = {k[:3]: v for k, v in MONTHS.items()}
        mnum = mm.map(m3)
        if mnum.isna().all() or len(ms) == 1:
            mnum = pd.Series(ms[0] if len(ms) == 1 else np.nan, index=h.index)
        h['year'] = y
        h['month'] = mnum
        h['file'] = fn
        rows.append(h)
        print(f'{fn}: {len(h)} rows, months {sorted(h.month.dropna().unique().astype(int).tolist())}')
    r = pd.concat(rows, ignore_index=True)
    r['woreda_pcode'] = r['woreda_pcode'].astype(str).str.strip().str.upper().replace({'NAN': np.nan})
    r['zone_pcode_raw'] = r['woreda_pcode'].str[:6].where(r['woreda_pcode'].str.match(r'^ET\d{6}$', na=False))
    for c in ['region', 'zone', 'woreda']:
        r[c] = r[c].astype(str).str.strip()
    a2, a3 = cod_tables()
    r['zone_pcode'] = add_cod_zone(r, a2, a3)   # COD-AB v04 adm2
    print('4W rows matched to COD-AB v04 zone:', r.zone_pcode.notna().groupby(r.year).mean().round(3).to_dict())
    r['region_pcode'] = r['zone_pcode'].str[:4]
    donor = r['donor'].fillna('').astype(str) + ' ' + r['donor_acr'].fillna('').astype(str)
    r['donor_missing'] = donor.str.strip().isin(['', 'nan', 'nan nan']) | donor.str.lower().str.contains(
        r'^\s*(nan|n/?a|-|0)?\s*(nan)?\s*$', regex=True)
    r['us_funded'] = donor.str.contains(US_PAT)
    r['sector_group'] = r['sector'].map(sector_group)
    r['ym'] = pd.to_datetime(dict(year=r.year, month=r.month.fillna(1).astype(int), day=1))
    r['status'] = r['status'].astype(str)
    r['impl_org'] = r['impl_org'].astype(str).str.strip()
    r['prog_org'] = r['prog_org'].astype(str).str.strip()
    for c in ['donor', 'donor_acr', 'impl_acr', 'impl_type', 'region', 'zone', 'woreda', 'sector', 'activity']:
        r[c] = r[c].astype(str)
    r.to_parquet(f'{TIDY}/eth_4w_rows.parquet', index=False)

    # zone x month
    g = r.dropna(subset=['zone_pcode']).groupby(['zone_pcode', 'ym'])
    z = pd.DataFrame({
        'n_rows': g.size(),
        'n_partners': g['impl_org'].nunique(),
        'n_woredas': g['woreda_pcode'].nunique(),
        'n_rows_us': g['us_funded'].sum(),
        'n_rows_donor_missing': g['donor_missing'].sum(),
        'n_partners_us': r[r.us_funded].dropna(subset=['zone_pcode']).groupby(['zone_pcode', 'ym'])['impl_org'].nunique(),
    }).fillna({'n_partners_us': 0})
    for sg in ['food', 'nutrition', 'health', 'wash']:
        sub = r[r.sector_group == sg].dropna(subset=['zone_pcode']).groupby(['zone_pcode', 'ym'])
        z[f'n_rows_{sg}'] = sub.size()
        z[f'n_partners_{sg}'] = sub['impl_org'].nunique()
        z[f'n_rows_{sg}_us'] = r[(r.sector_group == sg) & r.us_funded].dropna(subset=['zone_pcode']).groupby(
            ['zone_pcode', 'ym']).size()
    z = z.fillna(0).reset_index()
    names = a2.set_index('adm2_pcode')[['adm1_name', 'adm2_name']].rename_axis('zone_pcode')
    z = z.merge(names, on='zone_pcode', how='left')
    z.to_csv(f'{TIDY}/exposure_4w_zone_month.csv', index=False)

    # 2024 exposure summary + 2025 change
    z['year'] = z.ym.dt.year
    nmon = z.groupby('year').ym.nunique()
    a = z.groupby(['zone_pcode', 'year']).sum(numeric_only=True).drop(columns='year', errors='ignore')
    a = a.div(nmon, level='year', axis=0)  # mean per reported month (zones absent = 0 implicitly)
    w = a.unstack('year')
    keep = ['n_rows', 'n_partners', 'n_rows_us', 'n_partners_us', 'n_rows_food', 'n_rows_nutrition',
            'n_rows_food_us', 'n_rows_nutrition_us', 'n_rows_health', 'n_rows_wash', 'n_rows_donor_missing']
    out = pd.DataFrame(index=w.index)
    for k in keep:
        for y in [2023, 2024, 2025, 2026]:
            if (k, y) in w.columns:
                out[f'{k}_{y}'] = w[(k, y)]
    out = out.fillna(0)
    donor_known_24 = out['n_rows_2024'] - out['n_rows_donor_missing_2024']
    out['us_share_rows_2024'] = out['n_rows_us_2024'] / donor_known_24.replace(0, np.nan)
    out['us_share_rows_2024_alldenom'] = out['n_rows_us_2024'] / out['n_rows_2024'].replace(0, np.nan)
    out['dlog_rows_2025_vs_2024'] = np.log1p(out['n_rows_2025']) - np.log1p(out['n_rows_2024'])
    out['dlog_partners_2025_vs_2024'] = np.log1p(out['n_partners_2025']) - np.log1p(out['n_partners_2024'])
    out = out.join(names)
    out.reset_index().to_csv(f'{TIDY}/exposure_4w_zone_2024.csv', index=False)
    print('4W months per year:', nmon.to_dict())
    return r


# ---------------------------------------------------------------- geography
COD = f'{ROOT}/input/ethiopia/hdx_cod_ab/eth_admin_boundaries.xlsx'


def cod_tables():
    a2 = pd.read_excel(COD, sheet_name='eth_admin2')[['adm1_name', 'adm1_pcode', 'adm2_name', 'adm2_pcode']]
    a3 = pd.read_excel(COD, sheet_name='eth_admin3')[['adm1_name', 'adm2_name', 'adm2_pcode', 'adm3_name', 'adm3_pcode']]
    return a2, a3


# raw zone spellings -> COD-AB v04 adm2 name (normalised keys)
ZONE_ALIAS = {
    'easternzone': 'eastern', 'southernzone': 'southern', 'northwesternzone': 'northwestern', 'northwest': 'northwestern',
    'southeastern': 'southeastern', 'centraltigray': 'central', 'easterntigray': 'eastern', 'southtigray': 'southern',
    'dollo': 'doolo', 'dolo': 'doolo', 'liben': 'liban', 'sitti': 'siti', 'shebelle': 'shabelle',
    'zonekilbetrasu': 'kilbatizone', 'zonegabirasu': 'gabizone', 'zonefantirasu': 'fantizone', 'zone': 'awsizone',
    'zoneawsirasu': 'awsizone', 'zonehari': 'harizone', 'zonemahi': 'mahizone',
    'waghemra': 'waghamra', 'waghimra': 'waghamra', 'northwollo': 'northwello', 'southwollo': 'southwello',
    'northshewa': 'northshewaam', 'eastharerge': 'easthararge', 'eastharerghe': 'easthararge', 'easthararghe': 'easthararge',
    'westhararge': 'westhararge', 'westharerge': 'westhararge', 'kelamwelega': 'kelemwellega', 'kelemwelega': 'kelemwellega',
    'eastwelega': 'eastwellega', 'westwelega': 'westwellega', 'asosa': 'assosa', 'guraghe': 'guraghe', 'gurage': 'guraghe',
    'southomo': 'southomo', 'agnuak': 'agnewak', 'nuer': 'nuwer', 'gedio': 'gedeo', 'kemashi': 'kamashi',
    'northshewar4': 'northshewaor', 'northshewar3': 'northshewaam', 'southgonder': 'southgondar',
    'northgonder': 'northgondar', 'kt': 'kembata', 'kembatatembaro': 'kembata', 'kembatatibaro': 'kembata',
    'alaba': 'halaba', 'halabaspecial': 'halaba', 'bahirdarcityadmin': 'bahirdartownadmin',
    'northwollo': 'northwello', 'northwelo': 'northwello', 'oromon': 'oromonationalityadministration',
    'itang': 'itangspecial', 'itangspecialworeda': 'itangspecial', 'maokomospecial': 'maokomospecial',
    'diredawa': 'diredawaurban', 'hawasatownadmin': 'hawassatownadmin',
}
REGION_ALIAS = {'ሶማሌ': 'Somali', 'ሶማሌክልል': 'Somali', 'ኦሮሚያ': 'Oromia', 'አማራ': 'Amhara',
                'southernnationsnationalitiesandpeoples': 'SNNP', 'snnpr': 'SNNP'}
ZONE_AM = {'ሸለቆ': 'Shabelle', 'ጃራር።': 'Jarar', 'ጃራር': 'Jarar', 'አፍስስ': 'Afder', 'ጉጂ': 'Guji', 'ሰሜን ወሎ': 'North Wello'}


def zone_to_pcode(region, zone, a2, region_name=None):
    """match a zone name to COD-AB adm2 within region (falls back to all regions if unique)"""
    if zone is None or (isinstance(zone, float) and np.isnan(zone)):
        return None
    zone = ZONE_AM.get(str(zone).strip(), zone)
    z = norm(zone)
    z = ZONE_ALIAS.get(z, z)
    reg0 = norm(region) if region is not None else ''
    mz = re.search(r'zone\s*(\d)', str(zone).lower())
    if mz and (reg0 == 'afar' or 'rasu' in str(zone).lower()):
        return f'ET020{mz.group(1)}'
    if reg0 == 'amhara' and z == 'oromia':
        return 'ET0310'
    a2 = a2.assign(k=a2.adm2_name.map(norm))
    reg = norm(REGION_ALIAS.get(str(region).strip(), region)) if region is not None else ''
    # Afar zones: compare on the ethnic name part
    cand = a2[a2.k == z]
    if len(cand) == 0:
        cand = a2[a2.k.str.startswith(z) | a2.k.map(lambda k: z.startswith(k) and len(k) > 3)]
    if len(cand) > 1 and reg:
        c2 = cand[cand.adm1_name.map(norm) == reg]
        if len(c2) == 0 and reg == 'snnp':
            c2 = cand[cand.adm1_name.isin(['Central Ethiopia', 'South Ethiopia', 'South West Ethiopia', 'Sidama'])]
        cand = c2 if len(c2) else cand
    return cand.adm2_pcode.iat[0] if len(cand) == 1 else None


def add_cod_zone(r, a2, a3):
    """4W rows -> COD-AB v04 adm2 pcode: woreda pcode if valid in v04, else woreda name, else zone name"""
    p3 = a3.set_index('adm3_pcode').adm2_pcode
    out = r['woreda_pcode'].map(p3)
    a3k = a3.assign(k=a3.adm3_name.map(norm))
    uniq = a3k.drop_duplicates('k', keep=False).set_index('k').adm2_pcode
    out = out.fillna(r['woreda'].map(norm).map(uniq))
    zz = r.loc[out.isna(), ['region', 'zone']].drop_duplicates()
    zmap = {(a, b): zone_to_pcode(a, b, a2) for a, b in zz.itertuples(index=False)}
    fill = pd.Series([zmap.get((a, b)) for a, b in r[['region', 'zone']].itertuples(index=False)], index=r.index)
    return out.fillna(fill)


def food_operator(row_prog, row_donor):
    s = f'{row_prog} {row_donor}'.lower()
    if 'jeop' in s or 'joint emergency' in s or 'catholic' in s or re.search(r'\bcrs\b', s):
        return 'JEOP'
    if 'wfp' in s or 'world food' in s:
        return 'WFP'
    if any(k in s for k in ['edrmc', 'ndrmc', 'rdmc', 'drmc', 'disaster risk', 'government', 'governmnet']):
        return 'GOV'
    if 'world bank' in s or 'ministry of finance' in s or s.endswith(' wb'):
        return 'GOV_WB'
    return 'OTHER'


def build_food_operator():
    """food-cluster rows of the 4W: which operator (JEOP / WFP / government) served each woreda, by month"""
    r = pd.read_parquet(f'{TIDY}/eth_4w_rows.parquet')
    f = r[(r.sector_group == 'food') & r.sector.str.lower().str.startswith('food')].copy()
    f['operator'] = [food_operator(a, b) for a, b in f[['prog_org', 'donor']].itertuples(index=False)]
    a2, a3 = cod_tables()
    p3 = a3.set_index('adm3_pcode')
    f['woreda_cod'] = f.woreda_pcode.where(f.woreda_pcode.isin(p3.index))
    w = (f.groupby(['zone_pcode', 'woreda_cod', 'woreda', 'ym', 'operator']).size().unstack('operator', fill_value=0) > 0).astype(int)
    w = w.reset_index()
    w.to_csv(f'{TIDY}/food_operator_woreda_month.csv', index=False)
    # zone x year: share of food-served woredas by operator (2024 = pre-cut exposure)
    f['year'] = f.ym.dt.year
    g = f.groupby(['zone_pcode', 'year'])
    z = pd.DataFrame({'food_woredas_any': g['woreda'].nunique()})
    for op in ['JEOP', 'WFP', 'GOV']:
        z[f'food_woredas_{op}'] = f[f.operator == op].groupby(['zone_pcode', 'year'])['woreda'].nunique()
        z[f'food_rows_{op}'] = f[f.operator == op].groupby(['zone_pcode', 'year']).size()
    z = z.fillna(0)
    z['jeop_share_woredas'] = z.food_woredas_JEOP / z.food_woredas_any.replace(0, np.nan)
    z = z.reset_index().merge(a2[['adm2_pcode', 'adm1_name', 'adm2_name']].rename(columns={'adm2_pcode': 'zone_pcode'}),
                              on='zone_pcode', how='left')
    # woreda totals for denominators
    nw = a3.groupby('adm2_pcode').size().rename('n_woredas_cod')
    z = z.merge(nw, left_on='zone_pcode', right_index=True, how='left')
    z.to_csv(f'{TIDY}/exposure_food_operator_zone_year.csv', index=False)
    print('food operator rows:', f.groupby(['year', 'operator']).size().unstack(fill_value=0).to_string())
    print('zones with any JEOP by year:', z[z.food_woredas_JEOP > 0].groupby('year').size().to_dict())
    return z


# ---------------------------------------------------------------- SMART surveys
def build_smart():
    a2, a3 = cod_tables()
    A = json.load(open(f'{ROOT}/input/smartplus/anthropometry.json'))['surveys']
    M = {s['id']: s for s in json.load(open(f'{ROOT}/input/smartplus/mortality.json'))['surveys']}
    rows = []
    for s in A:
        if s['countryCode'] != 'ET':
            continue
        k = s.get('keystats') or {}
        g = lambda ind, meth: (((k.get(ind) or {}).get(meth) or {}).get('all') or {}).get('prop')
        m = (M.get(s['id']) or {}).get('keystats') or {}
        cdr = ((m.get('crudeMortalityRate') or {}).get('all') or {}).get('stat')
        u5 = (m.get('under5MortalityRate') or {}).get('stat')
        rows.append(dict(
            source='SMART+ platform', survey_id=f"smartplus_{s['id']}", survey_name=s['surveyName'],
            organization=s['organizationName'], survey_type=s['surveyType'],
            region_raw=s['administrative_area_level_1'], zone_raw=s['administrative_area_level_2'],
            woreda_raw=s['administrative_area_level_3'], coverage=None,
            year=s['surveyYear'], month=s['surveyMonth'], lat=s.get('latitude'), lon=s.get('longitude'),
            gam_whz=None if g('gam', 'whz') is None else 100 * g('gam', 'whz'),
            sam_whz=None if g('sam', 'whz') is None else 100 * g('sam', 'whz'),
            gam_muac=None if g('gam', 'muac') is None else 100 * g('gam', 'muac'),
            sam_muac=None if g('sam', 'muac') is None else 100 * g('sam', 'muac'),
            stunting=None if g('stunting', 'haz') is None else 100 * g('stunting', 'haz'),
            cdr=cdr, u5dr=u5, woreda_pcodes=None))
    sp = pd.DataFrame(rows)
    sp['zone_pcode'] = [zone_to_pcode(a, b, a2) for a, b in sp[['region_raw', 'zone_raw']].itertuples(index=False)]
    # survey-name based flags
    sp['idp_or_camp'] = sp.survey_name.str.contains('IDP|camp|refugee|UNHCR', case=False) | sp.organization.str.contains('UNHCR')

    # ENCU registry (HDX, 2017-Mar 2024): one row per woreda; collapse to surveys
    f = f'{ROOT}/input/subnational_aid/hdx_response/eth/ethiopia-malnutrition-prevalence/ENCU_Assessment_registry_2024.xlsx'
    e = pd.read_excel(f)
    e['date'] = pd.to_datetime(e['Conducted'], errors='coerce')
    e = e[e.date.notna()].copy()
    e['Pcode'] = e['Pcode'].astype(str).str.upper().str.strip()
    gcols = ['Region', 'Zone', 'Partner', 'Coverage (Livelyhood , Zone)', 'date', 'Type of Assessment',
             'Children - GAM % (WFH)', 'Children -  SAM % (WFH)', 'Children - GAM % (MUAC)',
             'CMR/10000 persons/day', 'U5MR/10000 persons/day']
    e[gcols] = e[gcols].astype(object).where(e[gcols].notna(), '')
    E = e.groupby(gcols, dropna=False).agg(woreda_raw=('Woreda', lambda s: '; '.join(map(str, s))),
                                           woreda_pcodes=('Pcode', lambda s: ';'.join(sorted(set(s))))).reset_index()
    num = lambda v: pd.to_numeric(v, errors='coerce')
    er = pd.DataFrame(dict(
        source='ENCU assessment registry (HDX, to Mar 2024)', survey_id=[f'encu_{i}' for i in range(len(E))],
        survey_name=None, organization=E['Partner'], survey_type=E['Type of Assessment'],
        region_raw=E['Region'], zone_raw=E['Zone'], woreda_raw=E['woreda_raw'], coverage=E['Coverage (Livelyhood , Zone)'],
        year=E.date.dt.year, month=E.date.dt.month, lat=None, lon=None,
        gam_whz=num(E['Children - GAM % (WFH)']), sam_whz=num(E['Children -  SAM % (WFH)']),
        gam_muac=num(E['Children - GAM % (MUAC)']), sam_muac=None, stunting=None,
        cdr=num(E['CMR/10000 persons/day']), u5dr=num(E['U5MR/10000 persons/day']), woreda_pcodes=E['woreda_pcodes']))
    # GAM recorded as a fraction in some rows (e.g. Somali 2023: 0.15)
    frac = er.gam_whz < 1
    er['flag'] = np.where(frac, 'GAM<1 in registry: probably a fraction or placeholder; not rescaled', '')
    p3 = a3.set_index('adm3_pcode').adm2_pcode
    def zp(pc):
        zs = {p3.get(p) for p in str(pc).split(';')} - {None}
        if not zs:
            zs = {p[:6] for p in str(pc).split(';') if re.match(r'^ET\d{6}$', p)}
        return ';'.join(sorted(zs)) if zs else None
    er['zone_pcode'] = er.woreda_pcodes.map(zp)
    er['idp_or_camp'] = er.woreda_raw.astype(str).str.contains('IDP|camp', case=False)
    sp['flag'] = ''
    out = pd.concat([sp, er], ignore_index=True)
    out.insert(0, 'country', 'Ethiopia')
    zname = a2.set_index('adm2_pcode')
    out['zone_cod'] = out.zone_pcode.map(lambda z: '; '.join(zname.adm2_name.get(p, '?') for p in str(z).split(';')) if z else None)
    out['region_cod'] = out.zone_pcode.map(lambda z: zname.adm1_name.get(str(z).split(';')[0]) if z else None)
    # possible duplicates between the two sources (same zone & year-month)
    key = out.zone_pcode.astype(str) + '|' + out.year.astype(str) + '|' + out.month.astype(str)
    out['possible_duplicate'] = key.duplicated(keep=False) & out.zone_pcode.notna()
    out['post_cut'] = (out.year > 2025) | ((out.year == 2025) & (out.month >= 2))
    cols = ['country', 'source', 'survey_id', 'survey_name', 'organization', 'survey_type', 'region_raw', 'zone_raw',
            'woreda_raw', 'coverage', 'region_cod', 'zone_cod', 'zone_pcode', 'woreda_pcodes', 'year', 'month', 'post_cut',
            'idp_or_camp', 'gam_whz', 'sam_whz', 'gam_muac', 'sam_muac', 'stunting', 'cdr', 'u5dr', 'lat', 'lon',
            'possible_duplicate', 'flag']
    out = out[cols].sort_values(['year', 'month', 'region_cod'])
    out.to_csv(f'{TIDY}/smart_surveys.csv', index=False)
    print(out.groupby(['source', 'year']).size().to_string())
    print('zone pcode matched:', out.zone_pcode.notna().mean().round(2))
    return out


# ---------------------------------------------------------------- CBPF (EHF)
CLUST = {6: 'food', 9: 'nutrition', 7: 'health', 11: 'wash', 15: 'mpc'}


def build_cbpf():
    a2, a3 = cod_tables()
    a = pd.read_csv(f'{ROOT}/input/subnational_aid/cbpf/ProjectSummaryAggV2.csv', low_memory=False)
    a = a[a.PFId == 53]
    p = pd.read_csv(f'{ROOT}/input/subnational_aid/cbpf/ProjectSummaryV2.csv', low_memory=False)[['PrjCode', 'AStrDt', 'ApprDt']]
    a = a.merge(p, on='PrjCode', how='left')
    a['start'] = pd.to_datetime(a.AStrDt, errors='coerce').fillna(pd.to_datetime(a.ApprDt, errors='coerce'))
    rows = []
    for r in a.dropna(subset=['AdmLoc2']).itertuples():
        cl, bd = str(r.ClstAgg).split('|||'), str(r.AdmLocClustBdg2).split('|||')
        if len(cl) != len(bd):
            continue
        for c, b in zip(cl, bd):
            try:
                rows.append((r.AYr, r.start, r.AdmLoc1, r.AdmLoc2, r.AdmLoc3, int(float(c)), float(b), r.PrjCode))
            except ValueError:
                pass
    x = pd.DataFrame(rows, columns=['alloc_year', 'start', 'adm1', 'adm2', 'adm3', 'clust', 'usd', 'prj'])
    x['sector'] = x.clust.map(CLUST).fillna('other')
    zz = x[['adm1', 'adm2']].drop_duplicates()
    zmap = {(a_, b_): zone_to_pcode(a_, b_, a2) for a_, b_ in zz.itertuples(index=False)}
    x['zone_pcode'] = [zmap[(a_, b_)] for a_, b_ in x[['adm1', 'adm2']].itertuples(index=False)]
    print('CBPF ETH rows matched to zone:', x.zone_pcode.notna().mean().round(3),
          'US$ share', (x.usd[x.zone_pcode.notna()].sum() / x.usd.sum()).round(3))
    x.to_csv(f'{TIDY}/cbpf_eth_location_rows.csv', index=False)
    g = x.dropna(subset=['zone_pcode']).pivot_table(index=['zone_pcode', 'alloc_year'], columns='sector',
                                                    values='usd', aggfunc='sum', fill_value=0)
    g.columns = [f'cbpf_usd_{c}' for c in g.columns]
    g['cbpf_usd_all'] = g.sum(axis=1)
    g = g.reset_index()
    g.to_csv(f'{TIDY}/exposure_cbpf_zone_year.csv', index=False)
    return g


# ---------------------------------------------------------------- HNO
def build_hno():
    f = f'{ROOT}/input/ethiopia/hdx_hno/ethiopia-2024-humanitairan-needs-overview_hxl.xlsx'
    d = pd.read_excel(f, sheet_name='Overall PIN').iloc[1:]
    for c in d.columns[6:]:
        d[c] = pd.to_numeric(d[c], errors='coerce')
    d['year'] = 2024
    d.to_csv(f'{TIDY}/hno_pin_woreda_2024.csv', index=False)
    a2, a3 = cod_tables()
    p3 = a3.set_index('adm3_pcode').adm2_pcode
    d['zone_pcode'] = d.admin3Pcode.map(p3).fillna(d.admin2Pcode)
    z = d.groupby('zone_pcode')[[c for c in d.columns if 'PIN' in c]].sum().reset_index()
    z['year'] = 2024
    z.to_csv(f'{TIDY}/hno_pin_zone_2024.csv', index=False)
    print('HNO 2024 woredas', len(d), 'PIN total', round(d['Overall PIN'].sum() / 1e6, 2), 'm')
    # cluster PiN / targeted by woreda (HPC API extract)
    c = pd.read_csv(f'{ROOT}/input/ethiopia/hdx_hno/eth_hpc_needs_api_2024.csv', skiprows=[1], low_memory=False)
    c = c[c['Admin 3 PCode'].notna() & (c.Category == 'total')]
    c['zone_pcode'] = c['Admin 3 PCode'].map(p3).fillna(c['Admin 2 PCode'])
    w = c.pivot_table(index=['zone_pcode', 'Admin 3 PCode'], columns='Cluster', values=['In Need', 'Targeted'], aggfunc='sum')
    w.columns = [f"{'pin' if a == 'In Need' else 'tgt'}_{b.lower()}" for a, b in w.columns]
    w.reset_index().to_csv(f'{TIDY}/hno_cluster_pin_woreda_2024.csv', index=False)
    zz = w.groupby('zone_pcode').sum().reset_index()
    z = z.merge(zz, on='zone_pcode', how='outer')
    z.to_csv(f'{TIDY}/hno_pin_zone_2024.csv', index=False)
    print('zone PiN cols:', [k for k in z.columns][:30])


# ---------------------------------------------------------------- humanitarian access (OCHA, woreda, bi-monthly)
def build_access():
    f = f'{ROOT}/input/ethiopia/hdx_access/eth_national-access-map-data_december_2025.xlsx'
    d = pd.read_excel(f, sheet_name='ETH Accessibility Perworeda2025')
    acc = [c for c in d.columns if c.startswith('Accessibility')]
    L = d.melt(id_vars=['Admin1Name', 'Admin2Name', 'Admin2PCode', 'Admin3Name', 'Admin3PCode'], value_vars=acc,
               var_name='round', value_name='access')
    L['access'] = L['access'].astype(str).str.strip()
    L.loc[L.access.str.startswith('Accessibility'), 'access'] = np.nan   # spreadsheet artefact in Sept 2024 column
    a = L.access.fillna('').str.lower()
    L['access_cat'] = np.select([a.str.contains('hard'), a.str.contains('ar?t', regex=True) & a.str.startswith('pa'),
                                 a.str.contains('restrict'), a.str.contains('acces')],
                                ['hard_to_reach', 'partial', 'restrictions', 'accessible'], default=None)
    L.loc[L.access.isna(), 'access_cat'] = None
    L.to_csv(f'{TIDY}/access_woreda_bimonthly_2024_2025.csv', index=False)
    print(L.groupby('round').access_cat.value_counts().unstack(fill_value=0).to_string())


if __name__ == '__main__':
    what = sys.argv[1:] or ['4w', 'food', 'smart', 'cbpf', 'hno', 'access']
    if '4w' in what:
        build_4w()
    if 'food' in what:
        build_food_operator()
    if 'smart' in what:
        build_smart()
    if 'cbpf' in what:
        build_cbpf()
    if 'hno' in what:
        build_hno()
    if 'access' in what:
        build_access()
