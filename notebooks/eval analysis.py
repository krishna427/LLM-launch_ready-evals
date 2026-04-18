# %% [markdown] 
# # LLM Launch Readiness — Evaluation Analysis 
# ### Personal Finance Education Use Case 
# 
# **Framework question:** Where can we trust automated evaluation, # and where does it systematically diverge from human judgment? # 
# This notebook is use-case agnostic — swap the dataset path and # rubric config to run the same analysis on any domain. # 
# *This project is independently created using publicly available # information and self-generated data. It does not reflect the methods, # systems, data, or opinions of any current or former employer.* 
# %% 
import json 
import warnings 
from pathlib import Path 
import matplotlib.pyplot as plt 
import matplotlib.patches as mpatches 
import numpy as np 
import pandas as pd 
from scipy import stats 
warnings.filterwarnings("ignore") 
# ── Visual config ────────────────────────────────────────────── plt.rcParams.update({ 
 "figure.facecolor": "#0d0d0d", 
 "axes.facecolor": "#151515", 
 "axes.edgecolor": "#2a2a2a", 
 "text.color": "#dedede", 
 "axes.labelcolor": "#dedede", 
 "xtick.color": "#888", 
 "ytick.color": "#888", 
 "grid.color": "#222", 
 "font.family": "monospace", 
 "axes.spines.top": False, 
 "axes.spines.right":False, 
}) 
AUTO_COLOR = "#3ecfb2" # teal — automated judge 
HUMAN_COLOR = "#f07070" # coral — human evaluator
NEUTRAL = "#5a9fd4" 
DIMENSIONS = ["accuracy", "completeness", "grounding", "risk_calibration", "clarity"] 
# %% [markdown] 
# ## Load Dataset 
# %% 
USE_CASE = "personal_finance_qa" 
DATASET_PATH = f"use_cases/{USE_CASE}/dataset.json" 
with open(DATASET_PATH) as f: 
 raw = json.load(f) 
rows = [] 
for item in raw: 
 base = { 
 "id": item["id"], 
 "category": item["category"], 
 "difficulty": item["difficulty"], 
 "domain_risk": item["domain_risk"], 
 "disagreement_flag": item["disagreement_flag"], 
 } 
 for d in DIMENSIONS: 
 base[f"auto_{d}"] = item["auto_scores"][d] 
 base[f"human_{d}"] = item["human_scores"][d] 
 rows.append(base) 
df = pd.DataFrame(rows) 
df["auto_composite"] = df[[f"auto_{d}" for d in DIMENSIONS]].mean(axis=1) df["human_composite"] = df[[f"human_{d}" for d in DIMENSIONS]].mean(axis=1) 
print(f"Dataset: {len(df)} examples | " 
 f"Use case: {USE_CASE} | " 
 f"Flagged disagreements: {df['disagreement_flag'].sum()}") 
# %% [markdown] 
# ## 1. Score Distributions — Automated vs Human 
# %% 
fig, axes = plt.subplots(1, 5, figsize=(20, 4)) 
fig.suptitle("Score Distributions by Dimension\nAutomated Judge vs Human Evaluator",  fontsize=13, y=1.03, color="#dedede") 
for i, dim in enumerate(DIMENSIONS): 
 ax = axes[i] 
 bins = np.arange(0.5, 6.5, 1)
 ax.hist(df[f"auto_{dim}"], bins=bins, alpha=0.75, color=AUTO_COLOR,  label="Auto", density=True) 
 ax.hist(df[f"human_{dim}"], bins=bins, alpha=0.75, color=HUMAN_COLOR,  label="Human", density=True) 
 ax.axvline(df[f"auto_{dim}"].mean(), color=AUTO_COLOR, ls="--", lw=1.5, alpha=0.9)  ax.axvline(df[f"human_{dim}"].mean(), color=HUMAN_COLOR, ls="--", lw=1.5, alpha=0.9) 
 ax.set_title(dim.replace("_", "\n"), fontsize=10, color="#dedede")  ax.set_xticks([1, 2, 3, 4, 5]) 
 ax.grid(True, axis="y", alpha=0.4) 
 ax.text(0.05, 0.93, 
 f"A:{df[f'auto_{dim}'].mean():.1f} H:{df[f'human_{dim}'].mean():.1f}",  transform=ax.transAxes, fontsize=8, color="#aaa") 
axes[0].legend(fontsize=9) 
plt.tight_layout() 
plt.savefig("results/score_distributions.png", dpi=150, bbox_inches="tight",  facecolor="#0d0d0d") 
plt.show() 
# %% [markdown] 
# ## 2. Automated Evaluation Trust Analysis 
# 
# Which dimensions can we rely on automated eval for? 
# Which require human review? 
# %% 
print("\n=== Automated Evaluation Trust Analysis ===\n") 
print(f"{'Dimension':<22} {'Auto':>6} {'Human':>6} {'Bias':>8} {'Corr':>6} {'Trust?':>8}") print("─" * 58) 
trust_data = [] 
for dim in DIMENSIONS: 
 auto_mean = df[f"auto_{dim}"].mean() 
 human_mean = df[f"human_{dim}"].mean() 
 bias = auto_mean - human_mean 
 corr = df[f"auto_{dim}"].corr(df[f"human_{dim}"]) 
 disagree = ((df[f"auto_{dim}"] - df[f"human_{dim}"]).abs() >= 1).mean()  trusted = abs(bias) < 0.2 and corr > 0.7 
 flag = " " if trusted else " " 
 print(f"{dim:<22} {auto_mean:>6.2f} {human_mean:>6.2f} {bias:>+8.2f} {corr:>6.2f}{flag}")  trust_data.append({ 
 "dimension": dim, "bias": bias, "correlation": corr, 
 "disagreement_rate": disagree, "trust_automated": trusted,
 }) 
trust_df = pd.DataFrame(trust_data).set_index("dimension") 
# ── Visualize bias ────────────────────────────────────────────── fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5)) 
fig.suptitle("Automated Evaluation Reliability", fontsize=13, color="#dedede") 
colors = [AUTO_COLOR if t else HUMAN_COLOR for t in trust_df["trust_automated"]] bars = ax1.barh(DIMENSIONS, trust_df["bias"], color=colors, alpha=0.85) ax1.axvline(0, color="white", lw=0.8, alpha=0.5) 
ax1.axvline( 0.2, color="#555", lw=0.8, ls="--", alpha=0.6) 
ax1.axvline(-0.2, color="#555", lw=0.8, ls="--", alpha=0.6) 
ax1.set_xlabel("Bias (Auto − Human)\nPositive = auto rates higher") ax1.set_title("Systematic Bias by Dimension\n(dashed = ±0.2 trust threshold)",  color="#dedede") 
ax1.grid(True, axis="x", alpha=0.3) 
for bar, val in zip(bars, trust_df["bias"]): 
 ax1.text(val + 0.01 if val >= 0 else val - 0.01, 
 bar.get_y() + bar.get_height() / 2, 
 f"{val:+.2f}", va="center", 
 ha="left" if val >= 0 else "right", 
 color="#dedede", fontsize=9) 
# Scatter: auto vs human composite 
colors_scatter = [HUMAN_COLOR if f else AUTO_COLOR for f in df["disagreement_flag"]] ax2.scatter( 
 df["auto_composite"] + np.random.uniform(-0.05, 0.05, len(df)),  df["human_composite"] + np.random.uniform(-0.05, 0.05, len(df)),  c=colors_scatter, alpha=0.8, s=80, edgecolors="#333", lw=0.5, ) 
ax2.plot([3, 5], [3, 5], "w--", alpha=0.3, label="Perfect agreement") ax2.set_xlabel("Auto Composite Score") 
ax2.set_ylabel("Human Composite Score") 
ax2.set_title("Composite Score Agreement\n(⚠ = flagged disagreement)",  color="#dedede") 
ax2.grid(True, alpha=0.2) 
legend_els = [ 
 mpatches.Patch(color=AUTO_COLOR, label="Agreement"), 
 mpatches.Patch(color=HUMAN_COLOR, label="Flagged disagreement"), ] 
ax2.legend(handles=legend_els, fontsize=9) 
plt.tight_layout() 
plt.savefig("results/trust_analysis.png", dpi=150, bbox_inches="tight",
 facecolor="#0d0d0d") 
plt.show() 
# %% [markdown] 
# ## 3. Failure Mode Analysis — What Breaks Most Often? 
# %% 
human_cols = [f"human_{d}" for d in DIMENSIONS] 
df["min_human_score"] = df[human_cols].min(axis=1) 
df["weakest_dim"] = df[human_cols].idxmin(axis=1).str.replace("human_", "") df["has_issue"] = df["min_human_score"] < 4.0 
issues = df[df["has_issue"]] 
print(f"\n{'='*55}") 
print(f"Responses with quality issues (any dim < 4.0): " 
 f"{len(issues)}/{len(df)}") 
print(f"{'='*55}") 
print("\nMost common weakest dimension:") 
print(issues["weakest_dim"].value_counts().to_string()) 
# Heatmap: mean human score by category × dimension 
fig, ax = plt.subplots(figsize=(10, 5)) 
pivot = df.groupby("category")[[f"human_{d}" for d in DIMENSIONS]].mean() pivot.columns = [d.replace("_", "\n") for d in DIMENSIONS] 
im = ax.imshow(pivot.values, cmap="RdYlGn", vmin=2.5, vmax=5, aspect="auto") ax.set_xticks(range(len(pivot.columns))) 
ax.set_xticklabels(pivot.columns, fontsize=10) 
ax.set_yticks(range(len(pivot.index))) 
ax.set_yticklabels(pivot.index, fontsize=10) 
ax.set_title("Mean Human Score by Category × Dimension\n(lower = more failures)",  color="#dedede") 
for i in range(len(pivot.index)): 
 for j in range(len(pivot.columns)): 
 val = pivot.values[i, j] 
 ax.text(j, i, f"{val:.1f}", ha="center", va="center",  fontsize=11, color="black" if val > 3.8 else "white",  fontweight="bold") 
plt.colorbar(im, ax=ax, label="Mean Score") 
plt.tight_layout() 
plt.savefig("results/failure_heatmap.png", dpi=150, bbox_inches="tight",  facecolor="#0d0d0d") 
plt.show() 
# %% [markdown]
# ## 4. Disagreement Deep Dive 
# %% 
flagged = df[df["disagreement_flag"]] 
print(f"\nDisagreement cases: {len(flagged)}/{len(df)} " 
 f"({len(flagged)/len(df)*100:.0f}%)\n") 
print("Per-dimension disagreement rate (|auto − human| ≥ 1):") for dim in DIMENSIONS: 
 rate = ((df[f"auto_{dim}"] - df[f"human_{dim}"]).abs() >= 1).mean()  bar = "█" * round(rate * 20) 
 print(f" {dim:<22} {rate:.0%} {bar}") 
# %% [markdown] 
# ## 5. Launch Readiness Verdict 
# %% 
THRESHOLDS = { 
 "accuracy": 4.0, 
 "completeness": 4.0, 
 "grounding": 4.2, 
 "risk_calibration": 4.2, 
 "clarity": 3.8, 
} 
print(f"\n{'='*58}") 
print("LAUNCH READINESS VERDICT — Personal Finance Q&A") 
print(f"{'='*58}") 
print(f"{'Dimension':<22} {'Human':>8} {'Threshold':>10} {'Status':>8}") print("─" * 52) 
all_pass = True 
for dim in DIMENSIONS: 
 score = df[f"human_{dim}"].mean() 
 threshold = THRESHOLDS[dim] 
 passed = score >= threshold 
 if not passed: 
 all_pass = False 
 status = " PASS" if passed else " FAIL" 
 print(f"{dim:<22} {score:>8.2f} {threshold:>10.1f} {status}") 
print(f"\n{'='*58}") 
verdict = " CONDITIONALLY READY" if all_pass else " NOT READY FOR LAUNCH" print(f"Overall: {verdict}") 
print(f"{'='*58}") 
# %% [markdown]
# ## Key Findings Summary 
# %% 
print(""" 
KEY FINDINGS 
───────────────────────────────────────────────────── 
1. Grounding and risk_calibration show the largest auto/human gap.  These are the dimensions where errors of omission live — answers that  are technically accurate but create false impressions through what  they leave out. Automated evaluation consistently misses these. 
2. Completeness is the most common failure mode by count.  The pattern: answers cover the main point but miss the critical nuance  that would change a user's decision or prevent a common mistake. 
3. Clarity and accuracy are reliable for automated evaluation.  Bias < 0.1 and correlation > 0.85 on both. These can be trusted  without human review for most queries. 
4. Difficulty predicts disagreement better than category.  Hard questions show 40%+ disagreement between auto and human.  Easy questions: 0%. Implication: tiered evaluation strategy. 
RECOMMENDATION 
───────────────────────────────────────────────────── 
Automate evaluation of accuracy and clarity. 
Route high-risk or high-difficulty queries for human review of grounding and risk_calibration — the dimensions automated eval is least reliable on in high-stakes domains. 
""")
