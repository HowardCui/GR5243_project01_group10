#!/usr/bin/env python 3.12
# -*- coding: utf-8 -*-
# time: 2026/02/13
# name: Haowen Cui, Yuhan Guo, Selina Peng(sp4550)，Shengbo, Yi

import warnings
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import numpy as np
import os
import seaborn as sns
from scipy import stats
from acquire import get_dataset

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams["figure.dpi"] = 120


def EDA():
	"""
	Main EDA pipeline: loads cleaned COPD data and generates all analysis plots.
	Uses age-adjusted data only and produces visualizations across four analysis parts.
	"""
	# Load and filter data
	df = pd.read_csv("data/cdc_cleaned_copd.csv")
	df = df[df["datavaluetype"].str.startswith("Age-adjusted")].copy()
	df["datavalue"] = pd.to_numeric(df["datavalue"], errors="coerce")

	# Question mappings
	Q_SHORT = {
		"Chronic obstructive pulmonary disease among adults":
			"COPD Prevalence (%)",
		"Current smoking among adults with chronic obstructive pulmonary disease":
			"Smoking Rate (%)",
		"Chronic obstructive pulmonary disease mortality among adults aged 45 years and older, underlying cause":
			"Mortality (underlying, /100k)",
		"Chronic obstructive pulmonary disease mortality among adults aged 45 years and older, underlying or contributing cause":
			"Mortality (any cause, /100k)",
		"Hospitalization for chronic obstructive pulmonary disease as any diagnosis, Medicare-beneficiaries aged 65 years and older":
			"Hosp Any Dx (/1000)",
		"Hospitalization for chronic obstructive pulmonary disease as principal diagnosis, Medicare-beneficiaries aged 65 years and older":
			"Hosp Principal Dx (/1000)",
	}
	Q_UNIT = {
		"Chronic obstructive pulmonary disease among adults": "%",
		"Current smoking among adults with chronic obstructive pulmonary disease": "%",
		"Chronic obstructive pulmonary disease mortality among adults aged 45 years and older, underlying cause": "cases per 100,000",
		"Chronic obstructive pulmonary disease mortality among adults aged 45 years and older, underlying or contributing cause": "cases per 100,000",
		"Hospitalization for chronic obstructive pulmonary disease as any diagnosis, Medicare-beneficiaries aged 65 years and older": "cases per 1,000",
		"Hospitalization for chronic obstructive pulmonary disease as principal diagnosis, Medicare-beneficiaries aged 65 years and older": "cases per 1,000",
	}

	df["q_short"] = df["question"].map(Q_SHORT)
	df["q_unit"]  = df["question"].map(Q_UNIT)

	# Create output directory
	os.makedirs("eda_png", exist_ok=True)

	# Run analysis parts
	_part1_individual_indicators(df, Q_SHORT, Q_UNIT)
	_part2_correlation_analysis(df, Q_SHORT)
	_part3_smoking_mortality_analysis(df, Q_SHORT)
	_part4_hierarchical_analysis(df)

	print("\n" + "="*65)
	print("done:")
	print("  P1A P1B P1C P1D P1E P1F  ← Part 1")
	print("  P2A P2B                  ← Part 2")
	print("  P3A P3B                  ← Part 3")
	print("  P4A P4B                  ← Part 4")
	print("="*65)


def _part1_individual_indicators(df, Q_SHORT, Q_UNIT):
	"""Plot distributions, trends, and stratified comparisons for each indicator."""
	print("\n" + "="*65)
	print("PART 1:")
	print("="*65)

	questions = list(Q_SHORT.keys())

	# Function to shorten race names (removes ", non-Hispanic" except for "Multiracial, non-Hispanic")
	def shorten_race_name(name):
		if name == "Multiracial, non-Hispanic":
			return "Multiracial, non-Hispanic"
		elif name.endswith(", non-Hispanic"):
			return name.replace(", non-Hispanic", "")
		else:
			return name

	# 1-A: Distributions
	fig, axes = plt.subplots(2, 3, figsize=(16, 9))
	axes = axes.flatten()
	for i, q in enumerate(questions):
		sub = df[(df["question"] == q) & (df["stratification1"] == "Overall")]["datavalue"].dropna()
		unit = Q_UNIT[q]
		short = Q_SHORT[q].replace("\n", " ")
		axes[i].hist(sub, bins=30, color="#4C72B0", edgecolor="white", alpha=0.85)
		axes[i].axvline(sub.mean(),   color="#DD8452", lw=2, ls="--", label=f"Mean={sub.mean():.1f}")
		axes[i].axvline(sub.median(), color="#55A868", lw=2, ls=":",  label=f"Median={sub.median():.1f}")
		axes[i].set_title(short, fontsize=9, fontweight="bold")
		axes[i].set_xlabel(unit, fontsize=8)
		axes[i].set_ylabel("Frequency", fontsize=8)
		axes[i].legend(fontsize=7)
	fig.suptitle("Distribution of Each Indicator", fontsize=12)
	plt.tight_layout()
	_save_fig(fig, "P1A_distributions_by_question.png")

	# 1-B: Yearly trends
	fig, axes = plt.subplots(2, 3, figsize=(16, 9))
	axes = axes.flatten()
	for i, q in enumerate(questions):
		sub = df[(df["question"] == q) & (df["stratification1"] == "Overall")]
		trend = sub.groupby("yearstart")["datavalue"].agg(["mean", "std"])
		ax = axes[i]
		ax.plot(trend.index, trend["mean"], marker="o", color="#4C72B0", lw=2)
		ax.fill_between(trend.index,
						trend["mean"] - trend["std"],
						trend["mean"] + trend["std"],
						alpha=0.18, color="#4C72B0")
		ax.set_title(Q_SHORT[q].replace("\n", " "), fontsize=9, fontweight="bold")
		ax.set_xlabel("Year", fontsize=8)
		ax.set_ylabel(Q_UNIT[q], fontsize=8)
		ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
	fig.suptitle("Trend of Each Indicator by year (Overall, Age-adjusted)", fontsize=12)
	plt.tight_layout()
	_save_fig(fig, "yearly_trends_by_question.png")

	# 1-C: Sex comparison
	fig, axes = plt.subplots(2, 3, figsize=(16, 9))
	axes = axes.flatten()
	for i, q in enumerate(questions):
		sub = df[(df["question"] == q) & (df["stratificationcategory1"] == "Sex")]
		ax = axes[i]
		if sub.empty:
			ax.set_visible(False); continue
		sns.boxplot(data=sub, x="stratification1", y="datavalue",
					order=["Male", "Female"], 
					palette=["#4C72B0","#DD8452"], 
					ax=ax, 
					width=0.5)
		ax.set_title(Q_SHORT[q].replace("\n", " "), fontsize=9, fontweight="bold")
		ax.set_xlabel("")
		ax.set_ylabel(Q_UNIT[q], fontsize=8)
		for j, sex in enumerate(["Male", "Female"]):
			med = sub[sub["stratification1"] == sex]["datavalue"].median()
			ax.text(j, med, f"{med:.1f}", ha="center", va="bottom", fontsize=8, color="black")
	fig.suptitle("Sex Compare\n(Age-adjusted)", fontsize=12)
	plt.tight_layout()
	_save_fig(fig, "P1C_sex_comparison_by_question.png")

	# 1-D: Race/Ethnicity comparison
	fig, axes = plt.subplots(2, 3, figsize=(18, 10))
	axes = axes.flatten()

	# Get all unique racial groups (alphabetically sorted)
	all_races = sorted(df[df["stratificationcategory1"] == "Race/Ethnicity"]["stratification1"].unique())

	# Create a color palette mapping each race to a consistent color
	colors = sns.color_palette("Set2", len(all_races))
	race_colors = {race: colors[i] for i, race in enumerate(all_races)}

	for i, q in enumerate(questions):
		sub = df[(df["question"] == q) & (df["stratificationcategory1"] == "Race/Ethnicity")].copy()
		ax = axes[i]
		if sub.empty:
			ax.set_visible(False); continue
		
		# Create shortened names for display
		sub["stratification1_short"] = sub["stratification1"].apply(shorten_race_name)
		
		# Get races present in this question, sorted alphabetically by original name
		races_in_q = sorted(sub["stratification1"].unique())
		races_in_q_short = sorted(set(sub["stratification1_short"].unique()))
		
		# Create palette using shortened names
		palette_q = {shorten_race_name(race): race_colors[race] for race in races_in_q}
		
		sns.barplot(data=sub, 
					x="stratification1_short", 
					y="datavalue", 
					order=races_in_q_short,
					estimator=np.median, 
					errorbar=("ci", 95), 
					palette=palette_q, ax=ax)
		ax.set_title(Q_SHORT[q].replace("\n", " "), fontsize=13, fontweight="bold")
		ax.set_xlabel("")
		ax.set_ylabel(Q_UNIT[q], fontsize=11)
		ax.set_xticklabels(ax.get_xticklabels(), rotation=40, ha="right", fontsize=10)
		ax.tick_params(axis='y', labelsize=10)
	fig.suptitle("Race/Ethnicity Comparison", fontsize=14, fontweight="bold")
	plt.tight_layout()
	_save_fig(fig, "P1D_race_comparison_by_question.png")

	# 1-E: Race/Ethnicity comparison (violinplot alternative)
	fig, axes = plt.subplots(2, 3, figsize=(18, 10))
	axes = axes.flatten()
	for i, q in enumerate(questions):
		sub = df[(df["question"] == q) & (df["stratificationcategory1"] == "Race/Ethnicity")].copy()
		ax = axes[i]
		if sub.empty:
			ax.set_visible(False); continue
		
		# Create shortened names for display
		sub["stratification1_short"] = sub["stratification1"].apply(shorten_race_name)
		
		# Get races present in this question, sorted alphabetically by original name
		races_in_q = sorted(sub["stratification1"].unique())
		races_in_q_short = sorted(set(sub["stratification1_short"].unique()))
		
		# Create palette using shortened names
		palette_q = {shorten_race_name(race): race_colors[race] for race in races_in_q}
		
		# Violinplot
		sns.violinplot(data=sub, 
					x="stratification1_short", 
					y="datavalue", 
					order=races_in_q_short,
					palette=palette_q, 
					ax=ax)
		ax.set_title(Q_SHORT[q].replace("\n", " "), fontsize=13, fontweight="bold")
		ax.set_xlabel("")
		ax.set_ylabel(Q_UNIT[q], fontsize=11)
		ax.set_xticklabels(ax.get_xticklabels(), rotation=40, ha="right", fontsize=10)
		ax.tick_params(axis='y', labelsize=10)
	fig.suptitle("Race/Ethnicity Comparison (Violinplot)", fontsize=14, fontweight="bold")
	plt.tight_layout()
	_save_fig(fig, "P1E_race_comparison_by_question_violin.png")

	# 1-F: Race/Ethnicity comparison (boxplot)
	fig, axes = plt.subplots(2, 3, figsize=(18, 10))
	axes = axes.flatten()
	for i, q in enumerate(questions):
		sub = df[(df["question"] == q) & (df["stratificationcategory1"] == "Race/Ethnicity")].copy()
		ax = axes[i]
		if sub.empty:
			ax.set_visible(False); continue
		
		# Create shortened names for display
		sub["stratification1_short"] = sub["stratification1"].apply(shorten_race_name)
		
		# Get races present in this question, sorted alphabetically by original name
		races_in_q = sorted(sub["stratification1"].unique())
		races_in_q_short = sorted(set(sub["stratification1_short"].unique()))
		
		# Create palette using shortened names
		palette_q = {shorten_race_name(race): race_colors[race] for race in races_in_q}
		
		# Boxplot
		sns.boxplot(data=sub, 
					x="stratification1_short", 
					y="datavalue", 
					order=races_in_q_short,
					palette=palette_q, 
					ax=ax)
		ax.set_title(Q_SHORT[q].replace("\n", " "), fontsize=13, fontweight="bold")
		ax.set_xlabel("")
		ax.set_ylabel(Q_UNIT[q], fontsize=11)
		ax.set_xticklabels(ax.get_xticklabels(), rotation=40, ha="right", fontsize=10)
		ax.tick_params(axis='y', labelsize=10)
	fig.suptitle("Race/Ethnicity Comparison (Boxplot)", fontsize=14, fontweight="bold")
	plt.tight_layout()
	_save_fig(fig, "P1F_race_comparison_by_question_box.png")


def _part2_correlation_analysis(df, Q_SHORT):
	"""Create pivot table and generate correlation heatmap and pairplot."""
	print("\n" + "="*65)
	print("PART 2: Correlation & Multivariate Analysis")
	print("="*65)

	# Create pivot table (state-year level)
	pivot = (df[df["stratification1"] == "Overall"]
			.groupby(["locationabbr", "yearstart", "question"])["datavalue"]
			.mean()
			.unstack("question"))
	pivot.columns = [Q_SHORT[c].replace("\n", " ") for c in pivot.columns]
	pivot = pivot.reset_index()

	print(f"\nPivot shape: {pivot.shape}  (state-year observations)")
	print(f"Missing values per indicator:")
	print(pivot.iloc[:, 2:].isna().sum().to_string())

	# 2-A: Correlation heatmap
	corr = pivot.iloc[:, 2:].corr(method="pearson")
	fig, ax = plt.subplots(figsize=(10, 8))
	mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
	sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdYlGn", center=0,
				vmin=-1, vmax=1, linewidths=0.5, ax=ax,
				annot_kws={"size": 10, "weight": "bold"},
				mask=mask)
	ax.set_title("Pearson_related_matrix\n(state-year level, Overall, Age-adjusted)",
				fontsize=12, fontweight="bold")
	ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha="right", fontsize=9)
	ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=9)
	plt.tight_layout()
	_save_fig(fig, "P2A_correlation_heatmap.png")

	# 2-B: Pairplot
	key_cols = [c for c in pivot.columns 
				if any(k in c for k in
				["COPD Prevalence", "Smoking", "Mortality\n(underlying", "Hosp Any"])]
	if len(key_cols) < 4:
		key_cols = list(pivot.columns[2:6])

	pair_df = pivot[key_cols + ["yearstart"]].dropna()
	pair_df["yearstart"] = pair_df["yearstart"].astype(str)

	g = sns.pairplot(pair_df, vars=key_cols,
					hue="yearstart",
					plot_kws={"alpha": 0.6, "s": 40},
					diag_kind="kde", corner=True)
	g.figure.suptitle("Core Pairplot\n(Colored by year)", y=1.01, fontsize=11)
	_save_fig(g.figure, "P2B_pairplot_key_indicators.png")

	return pivot


def _part3_smoking_mortality_analysis(df, Q_SHORT):
	"""Analyze smoking vs mortality relationships at state-year level."""
	print("\n" + "="*65)
	print("PART 3: Smoking vs. Mortality")
	print("="*65)

	# Create pivot table for analysis
	pivot = (df[df["stratification1"] == "Overall"]
			.groupby(["locationabbr", "yearstart", "question"])["datavalue"]
			.mean()
			.unstack("question"))
	pivot.columns = [Q_SHORT[c].replace("\n", " ") for c in pivot.columns]
	pivot = pivot.reset_index()

	smoke_col    = "Smoking Rate (%)"
	mort_col     = "Mortality (underlying, /100k)"
	mort_any_col = "Mortality (any cause, /100k)"
	prev_col     = "COPD Prevalence (%)"

	# Filter to complete cases
	plot_df = pivot[[smoke_col, mort_col, mort_any_col, prev_col, "locationabbr", "yearstart"]].dropna()
	print(f"  Complete cases for smoking-mortality analysis: {len(plot_df)}")

	# 3-A: Smoking vs mortality scatter plots
	fig, axes = plt.subplots(1, 2, figsize=(14, 6))
	years = sorted(plot_df["yearstart"].unique())
	colors = sns.color_palette("tab10", len(years))

	for ax, (mort, title) in zip(axes, [
		(mort_col,     "Mortality (Underlying Cause, /100k)"),
		(mort_any_col, "Mortality (Any Cause, /100k)"),
	]):
		for yr, col in zip(years, colors):
			sub = plot_df[plot_df["yearstart"] == yr]
			ax.scatter(sub[smoke_col], sub[mort], color=col, alpha=0.7, s=45, label=str(yr))

		x, y = plot_df[smoke_col], plot_df[mort]
		slope, intercept, r, p, _ = stats.linregress(x.dropna(), y.dropna())
		xline = np.linspace(x.min(), x.max(), 100)
		ax.plot(xline, slope * xline + intercept, color="black", lw=2, ls="--",
				label=f"OLS: r={r:.2f}, p={p:.3f}")
		
		ax.set_xlabel("Smoking Rate (%)", fontsize=10)
		ax.set_ylabel(title, fontsize=10)
		ax.set_title(f"Smoking Rate vs {title}", fontsize=10, fontweight="bold")
		ax.legend(fontsize=8, title="Year")

		# Annotate outliers
		threshold_x = plot_df[smoke_col].quantile(0.85)
		threshold_y = plot_df[mort].quantile(0.85)
		for _, row in plot_df.iterrows():
			if row[smoke_col] > threshold_x or row[mort] > threshold_y:
				ax.annotate(row["locationabbr"],
							(row[smoke_col], row[mort]),
							fontsize=6, alpha=0.7,
							xytext=(3, 3),
							textcoords="offset points")

	fig.suptitle("Smoking rate vs. Mortality rate\n(state-year, Overall, Age-adjusted)", fontsize=12)
	plt.tight_layout()
	_save_fig(fig, "P3A_smoking_vs_mortality_scatter.png")

	# 3-B: Smoking vs prevalence
	fig, ax = plt.subplots(figsize=(8, 6))
	for yr, col in zip(years, colors):
		sub = plot_df[plot_df["yearstart"] == yr]
		ax.scatter(sub[smoke_col], sub[prev_col], color=col, alpha=0.7, s=45, label=str(yr))

	x, y = plot_df[smoke_col], plot_df[prev_col]
	slope, intercept, r, p, _ = stats.linregress(x, y)
	xline = np.linspace(x.min(), x.max(), 100)
	ax.plot(xline, slope * xline + intercept, color="black", lw=2, ls="--",
			label=f"OLS: r={r:.2f}, p={p:.3f}")
	ax.set_xlabel("Smoking Rate (%)", fontsize=11)
	ax.set_ylabel("COPD Prevalence (%)", fontsize=11)
	ax.set_title("moking rate vs. COPD prevalence\n(state-year, Overall, Age-adjusted)", fontsize=11, fontweight="bold")
	ax.legend(fontsize=9)
	plt.tight_layout()
	_save_fig(fig, "P3B_smoking_vs_prevalence_scatter.png")

	# 3-C: Correlation statistics
	corr_pairs = [
		(smoke_col, prev_col,     "smoke rate → COPD prevalence"),
		(smoke_col, mort_col,     "smoke rate → Mortality rate (primary cause)"),
		(smoke_col, mort_any_col, "smoke rate → Mortality rate (Any case)"),
		(prev_col,  mort_col,     "COPD prevalence→ Mortality rate (primary cause)"),
		(prev_col,  mort_any_col, "COPD prevalence → Mortality rate (Any case)"),
	]
	print("\n  [Pearson r — state-year level, listwise deletion]")
	print(f"  {'Pair':<35}  {'r':>6}  {'p-value':>10}  {'n':>5}")
	print("  " + "-"*60)
	for xa, ya, name in corr_pairs:
		tmp = pivot[[xa, ya]].dropna()
		if len(tmp) < 5:
			continue
		r, p = stats.pearsonr(tmp[xa], tmp[ya])
		sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
		print(f"  {name:<35}  {r:>6.3f}  {p:>10.4f} {sig:>3}  n={len(tmp)}")


def _part4_hierarchical_analysis(df):
	"""Analyze relationships stratified by sex and race/ethnicity."""
	print("\n" + "="*65)
	print("PART 4: Hierarchical Correlation")
	print("="*65)

	# 4-A: Smoking vs mortality by sex
	fig, axes = plt.subplots(1, 2, figsize=(14, 6))
	for ax, sex in zip(axes, ["Male", "Female"]):
		sex_smoke = (df[(df["question"].str.contains("Current smoking"))
						& (df["stratification1"] == sex)]
					.groupby(["locationabbr", "yearstart"])["datavalue"].mean()
					.rename("smoking"))
		sex_mort  = (df[(df["question"].str.contains("mortality.*underlying cause", regex=True))
						& (df["stratification1"] == sex)]
					.groupby(["locationabbr", "yearstart"])["datavalue"].mean()
					.rename("mortality"))
		merged = pd.concat([sex_smoke, sex_mort], axis=1).dropna()

		ax.scatter(merged["smoking"], merged["mortality"], alpha=0.6, s=40,
				color="#4C72B0" if sex == "Male" else "#DD8452")
		if len(merged) > 2:
			slope, intercept, r, p, _ = stats.linregress(merged["smoking"], merged["mortality"])
			xline = np.linspace(merged["smoking"].min(), merged["smoking"].max(), 100)
			ax.plot(xline, slope*xline + intercept, color="black", lw=2, ls="--",
					label=f"r={r:.2f}, p={p:.3f}")
		ax.set_title(f"{sex}: Smoking Rate vs Mortality (Underlying)", fontsize=10, fontweight="bold")
		ax.set_xlabel("Smoking Rate (%)")
		ax.set_ylabel("Mortality (cases per 100,000)")
		ax.legend(fontsize=9)
		print(f"  {sex}: n={len(merged)}, r={r:.3f}, p={p:.4f}")

	fig.suptitle("Smoking rate vs. Mortality rate\n(Sex, Age-adjusted)", fontsize=12)
	plt.tight_layout()
	_save_fig(fig, "P4A_smoking_mortality_by_sex.png")

	# 4-B: Prevalence vs mortality by race/ethnicity
	races = ["White, non-Hispanic", "Black, non-Hispanic", "Hispanic"]
	fig, axes = plt.subplots(1, 3, figsize=(18, 5))
	for ax, race in zip(axes, races):
		r_prev = (df[(df["question"].str.contains("disease among adults"))
					& (df["stratification1"] == race)]
				.groupby(["locationabbr","yearstart"])["datavalue"].mean().rename("prev"))

		r_mort = (df[(df["question"].str.contains("mortality.*underlying cause", regex=True))
					& (df["stratification1"] == race)]
				.groupby(["locationabbr","yearstart"])["datavalue"].mean().rename("mort"))

		merged = pd.concat([r_prev, r_mort], axis=1).dropna()

		ax.scatter(merged["prev"], merged["mort"], alpha=0.6, s=40, color="#8172B2")

		if len(merged) > 2:
			slope, intercept, r_val, p, _ = stats.linregress(merged["prev"], merged["mort"])
			xline = np.linspace(merged["prev"].min(), merged["prev"].max(), 100)
			ax.plot(xline, slope*xline + intercept, color="black", lw=2, ls="--",
					label=f"r={r_val:.2f}, p={p:.3f}")
			ax.legend(fontsize=9)
			print(f"  {race}: n={len(merged)}, r={r_val:.3f}, p={p:.4f}")
		
		ax.set_title(race, fontsize=10, fontweight="bold")
		ax.set_xlabel("COPD Prevalence (%)")
		ax.set_ylabel("Mortality (/100k)")
	fig.suptitle("Prevalence vs. Mortality of COPD\n(Race/Ethnicity)", fontsize=12)
	plt.tight_layout()
	_save_fig(fig, "P4B_prevalence_mortality_by_race.png")


def _save_fig(fig, fname):
	"""Save figure to eda_png directory and close."""
	path = f"eda_png/{fname}"
	fig.savefig(path, bbox_inches="tight")
	plt.close(fig)
	print(f"  ✓ {path}")


if __name__ == "__main__":
	EDA()
