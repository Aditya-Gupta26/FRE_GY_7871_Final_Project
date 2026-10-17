"""Build analysis.ipynb: the report's sections (verbatim from REPORT.md) + code cells that recompute and
show every table and figure. Then run:
    jupyter nbconvert --to notebook --execute --inplace analysis.ipynb
    python scripts/make_notebook.py --strip-times     # drop the run-time stamps Jupyter writes into each cell
"""
import _bootstrap  # noqa: F401
import re
import sys

import nbformat as nbf

from src.config import ROOT

if "--strip-times" in sys.argv:
    nb = nbf.read(ROOT / "analysis.ipynb", as_version=4)
    for cell in nb.cells:
        cell.metadata.pop("execution", None)
    nbf.write(nb, ROOT / "analysis.ipynb")
    print("stripped run-time stamps from analysis.ipynb")
    sys.exit(0)

from notebook_text import MD, PLAN

report = (ROOT / "REPORT.md").read_text()
parts = re.split(r"(?m)^(?=## )", report)
head, sections = parts[0], {re.match(r"## (\d+)", p).group(1): p for p in parts[1:] if re.match(r"## (\d+)", p)}

C = {}
C["setup"] = """import sys, json, warnings, subprocess
sys.path.insert(0, '.'); sys.path.insert(0, 'scripts')
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from IPython.display import Image, display
pd.set_option('display.width', 200); pd.set_option('display.max_columns', 40); pd.set_option('display.max_colwidth', 80)
from src.config import TABLES, FIGURES, OUTPUTS, PREREG, PREREG_NOTES
# recompute every result from the saved data and codes, exactly as for the report. Steps that need the
# collected text (not redistributed: headline and post text) are skipped when it is absent, and the committed
# outputs of those steps are used instead.
from pathlib import Path
needs = {'scripts/04_econ_baseline.py': [], 'scripts/08_validation.py': ['data/labels/gold_sheet.csv', 'data/coded/codes.parquet'],
         'scripts/09_media_measures.py': ['data/interim/news.parquet', 'data/coded/codes.parquet'],
         'scripts/09b_tierc_realtime.py': ['data/interim/news.parquet', 'data/coded/codes.parquet'],
         'scripts/09c_tierc_checks.py': ['data/interim/news.parquet', 'data/coded/codes.parquet'],
         'scripts/10_analysis.py': [],
         'scripts/10b_reddit_exploratory.py': ['data/interim/reddit.parquet', 'data/labels/gold_sheet.csv'],
         'scripts/11_make_figures.py': []}
for s, req in needs.items():
    missing = [f for f in req if not Path(f).exists()]
    if missing:
        print(s, 'skipped (needs', ', '.join(missing), '); using the committed outputs')
        continue
    r = subprocess.run([sys.executable, s], capture_output=True, text=True)
    print(s, 'exit', r.returncode)
    assert r.returncode == 0, r.stderr[-3000:]
E = json.loads((OUTPUTS / 'results_econ.json').read_text())
V = json.loads((OUTPUTS / 'results_validation.json').read_text())
MED = json.loads((OUTPUTS / 'results_media.json').read_text())
R = json.loads((OUTPUTS / 'results.json').read_text())
TC = json.loads((OUTPUTS / 'results_tierc.json').read_text())
RD = json.loads((OUTPUTS / 'results_reddit.json').read_text())"""
C["data"] = """display(pd.read_csv(TABLES / 'corpus_waterfall_news.csv'))
display(pd.read_csv(TABLES / 'corpus_waterfall_reddit.csv'))
print(json.dumps(json.load(open(TABLES / 'corpus_summary.json')), indent=1))
display(pd.read_csv(TABLES / 'corpus_outlet_year_counts.csv', index_col=0))
display(pd.read_csv(TABLES / 'data_revisions.csv', index_col=0).round(3))
print(json.dumps(json.load(open(TABLES / 'data_course_file_check.json')), indent=1))"""
C["method"] = """print(json.dumps(PREREG, indent=1)[:6000])
for t, n in PREREG_NOTES: print(t, '|', n)
display(pd.read_csv(TABLES / 'val_agreement_models_prereview.csv').round(3))   # Table 3: Sonnet vs Haiku before my corrections
display(pd.read_csv(TABLES / 'val_agreement_AB.csv').round(3))                 # the two passes after my corrections
v = pd.read_csv(TABLES / 'val_tools_vs_gold.csv')
display(v[v.subset == 'all'].pivot_table(index='field', columns='tool', values='macro_f1').round(3))
display(v[v.tool == 'opus'].pivot_table(index='field', columns='subset', values='macro_f1').round(3))
display(pd.read_csv(TABLES / 'val_per_class.csv').query("tool == 'opus'").round(3))
display(pd.read_csv(TABLES / 'val_swaps.csv').round(3))
print('test-retest kappa:', {k: round(x['kappa'], 3) for k, x in V['test_retest'].items()})
print('minimal pairs:', V['minimal_pairs'])
print(json.dumps(MED, indent=1)[:3000])
display(Image(filename=str(FIGURES / 'fig1_media.png'), width=950))
# Tier C: fit on its training labels vs unseen items, learning curve, agreement with Opus by quarter
display(pd.read_csv(TABLES / 'tierc_training.csv').round(3))
display(pd.read_csv(TABLES / 'tierc_learning_curve.csv').round(3))
print(json.dumps(TC['agreement_with_opus_quarterly'], indent=1))
display(Image(filename=str(FIGURES / 'fig2_tierc.png'), width=950))"""
C["baseline"] = """print('Model E (ICS):'); display(pd.DataFrame(E['E_ICS']['coef']).T.round(4))
for k in ['ICS', 'ICC', 'ICE', 'X1_fin_now', 'X2_fin_exp', 'X3_bus_1y', 'X4_bus_5y', 'X5_durables']:
    e = E[f'E_{k}']; d = e['decomposition_2019_to_2026']
    print(f"{k:12s} R2 {e['R2_train']:.3f} | 2026 gap {e['mean_gap_2026']:.1f} (null band {e['mean_gap_2026_test']['null_lo']:.1f} to {e['mean_gap_2026_test']['null_hi']:.1f}, p {e['mean_gap_2026_test']['p_text']}) | share explained {d['share_explained']:.3f} [{d['share_lo']:.3f}, {d['share_hi']:.3f}]")
print('coverage check:', E['coverage_check_2017_19'])
display(Image(filename=str(FIGURES / 'fig3_baseline_gap.png'), width=950))"""
C["rq1"] = """print(json.dumps(R['rq1']['asymmetry'], indent=1)[:4000])
print(json.dumps(R['rq1']['selection'], indent=1))
display(pd.read_csv(TABLES / 'rq1_release_bins.csv').round(3))
print(json.dumps(R['rq1']['release_days'], indent=1)); print(json.dumps(R['rq1']['calibration'], indent=1))
display(pd.read_csv(TABLES / 'rq1_attribution.csv', header=[0, 1], index_col=0).round(3))
display(pd.read_csv(TABLES / 'rq1_by_source_group.csv', index_col=0).round(3))
print(json.dumps(R['rq1']['neg_by_lean_and_president'], indent=1)); print(json.dumps(R['rq1']['lpm_negative_by_group'], indent=1))
display(Image(filename=str(FIGURES / 'fig4_bias_tests.png'), width=950))"""
C["rq2"] = """display(pd.read_csv(TABLES / 'rq2_family.csv').round(4))
display(pd.read_csv(TABLES / 'rq2_toda_yamamoto.csv').round(4))
print('claim rule (Tier C):', R['rq2']['claim_rule_TC_NEGNET']); print('MDE:', R['rq2']['mde'])
print('own-Opus quarterly (the original measure at its fallback frequency):', R['rq2']['quarterly_own_opus'])
print({k: v for k, v in R['rq2'].items() if k.startswith('oos_gap') or k == 'reddit_demand'})
print(json.dumps(R['rq2']['party_timing'], indent=1)[:3000])"""
C["rq3"] = """display(pd.read_csv(TABLES / 'rq3_h1_controls_2010_19.csv').round(3))
display(pd.read_csv(TABLES / 'rq3_h1_controls_long.csv').round(3))
print(json.dumps(E['variants'], indent=1)); print('revision effect share:', E['h3_revision_effect_share'])
print('seasonality:', E['seasonality']); print('rolling sign changes:', E['rolling_sign_changes'], E['expanding_vs_fixed_rmse_post'])
display(pd.read_csv(TABLES / 'rq3_group_gaps.csv', index_col=0).round(2))"""
C["rq4"] = """print(json.dumps(R['rq4'], indent=1)[:5000])
display(Image(filename=str(FIGURES / 'fig5_mechanisms.png'), width=950))"""
C["rq5"] = """a = pd.read_csv(TABLES / 'rq5_accuracy.csv'); display(a.pivot_table(index=['dynamic', 'subperiod'], columns='model', values='rmse').round(2))
display(pd.read_csv(TABLES / 'rq5_clark_west.csv').round(4))
display(pd.DataFrame(R['rq5']['grid']).round(4)); print('grid hits:', R['rq5']['grid_hits_p_lt_0.10'], 'joint null:', R['rq5']['joint_null_hits'])
display(pd.DataFrame(R['rq5']['non_nested']).round(4))
print('EXPLORATORY (not pre-registered) m1 vs m1b:', json.dumps(R['rq5_exploratory_m1_vs_m1b'], indent=1))
display(Image(filename=str(FIGURES / 'fig6_prediction.png'), width=950))"""
C["rq6"] = """print(json.dumps(R['rq6'], indent=1)); print(json.dumps(R['scorecard'], indent=1)); print(json.dumps(R['shapley'], indent=1))"""
C["monitor"] = """print(json.dumps(R['monitoring'], indent=1, default=str)[:5000])
display(Image(filename=str(FIGURES / 'fig7_monitoring.png'), width=950))"""
C["extras"] = """print(json.dumps(R['extras'], indent=1))
# E3 (exploratory): Reddit tone scored by Tier C, through the RQ2 tests
print(json.dumps({k: RD[k] for k in ['reddit_gold', 'corpus', 'reddit_change_2019_2026', 'changes', 'toda_yamamoto']}, indent=1))
display(pd.read_csv(TABLES / 'e3_reddit_level_models.csv').round(3))"""

nb = nbf.v4.new_notebook()
cells = [nbf.v4.new_markdown_cell(MD["intro"]), nbf.v4.new_code_cell(C["setup"]), nbf.v4.new_markdown_cell(head.strip())]
for sec, extra in PLAN:
    if sec not in sections:
        continue
    cells.append(nbf.v4.new_markdown_cell(sections[sec].strip()))
    for e in extra:
        cells.append(nbf.v4.new_markdown_cell(MD[e[1]]) if isinstance(e, tuple) else nbf.v4.new_code_cell(C[e]))
nb["cells"] = cells
nb["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nbf.write(nb, ROOT / "analysis.ipynb")
print("wrote analysis.ipynb with", len(cells), "cells")
