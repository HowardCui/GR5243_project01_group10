#!/usr/bin/env python 3.12
# -*- coding: utf-8 -*-
# time: 2026/02/13
# name: Haowen Cui, Yuhan Guo Shengbo Yi, Selina Peng


from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

FAST_MODE = False
MAX_FEATURES_FOR_CORR = 300
MAX_FEATURES_FOR_VIF = 120
CORR_THRESH = 0.95
MAX_CORR_PAIRS_PRINT = 30
KEEP_RESIDUAL_FEATURES = False

try:
    from acquire import get_dataset
except ImportError:
    get_dataset = None


INDICATOR_MAP: dict[str, str] = {
    "Chronic obstructive pulmonary disease among adults":
        "COPD_Prevalence",
    "Current smoking among adults with chronic obstructive pulmonary disease":
        "Smoking_Rate",
    "Chronic obstructive pulmonary disease mortality among adults aged 45 years and older, underlying cause":
        "Mortality_Underlying",
    "Chronic obstructive pulmonary disease mortality among adults aged 45 years and older, underlying or contributing cause":
        "Mortality_Any_Cause",
    "Hospitalization for chronic obstructive pulmonary disease as any diagnosis, Medicare-beneficiaries aged 65 years and older":
        "Hospitalization_Any_Dx",
    "Hospitalization for chronic obstructive pulmonary disease as principal diagnosis, Medicare-beneficiaries aged 65 years and older":
        "Hospitalization_Principal_Dx",
}


@dataclass
class FeatureEngineeringConfig:
    save_csv: bool = False
    pivot_csv_path: str = "data/cdc_pivot_features.csv"
    normalized_csv_path: str = "data/cdc_normalized_features.csv"


def load_data() -> pd.DataFrame:
    df: pd.DataFrame | None = None
    if get_dataset is not None:
        try:
            df = get_dataset()
        except Exception:
            df = None
    if df is None:
        for path in (
            os.path.join("data", "cdc_cleaned_copd.csv"),
            "cdc_cleaned_copd.csv",
            os.path.join(os.path.dirname(__file__), "cdc_cleaned_copd.csv"),
        ):
            if os.path.exists(path):
                df = pd.read_csv(path)
                break
        if df is None:
            raise FileNotFoundError(
                "Unable to locate cdc_cleaned_copd.csv. Provide the file in a 'data' folder "
                "or alongside this script or ensure get_dataset() is available."
            )


    df = df[df["datavaluetype"].str.startswith("Age-adjusted")].copy()
    df["datavalue"] = pd.to_numeric(df["datavalue"], errors="coerce")

    unit_scale = {
        "%": 10.0,
        "cases per 100,000": 0.01,
        "cases per 1,000": 1.0,
    }
    df["datavalue_scaled"] = df.apply(
        lambda row: row["datavalue"] * unit_scale.get(str(row.get("datavalueunit")), np.nan),
        axis=1,
    )
    df["datavalue_log"] = np.log1p(df["datavalue_scaled"])
    return df


def build_features(config: FeatureEngineeringConfig | None = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    if config is None:
        config = FeatureEngineeringConfig()

    df = load_data()

    df["indicator"] = df["question"].map(INDICATOR_MAP)
    df = df[df["indicator"].notnull()].copy()


    sexes = ["Male", "Female"]
    race_labels = ["White, non-Hispanic", "Black, non-Hispanic"]

    records: list[dict[str, float | str | int]] = []


    for (state, year), group in df.groupby(["locationabbr", "yearstart"]):
        rec: dict[str, float | str | int] = {"locationabbr": state, "year": int(year)}
        for ind in INDICATOR_MAP.values():
            sub = group[group["indicator"] == ind]

            overall = sub.loc[sub["stratification1"] == "Overall", "datavalue_scaled"].mean()
            if np.isnan(overall):
                overall = sub["datavalue_scaled"].mean()
            rec[f"{ind}_overall"] = overall

            overall_log = sub.loc[sub["stratification1"] == "Overall", "datavalue_log"].mean()
            if np.isnan(overall_log):
                overall_log = sub["datavalue_log"].mean()
            rec[f"{ind}_log_overall"] = overall_log

            male = sub.loc[sub["stratification1"] == "Male", "datavalue_scaled"].mean()
            female = sub.loc[sub["stratification1"] == "Female", "datavalue_scaled"].mean()
            rec[f"{ind}_Male"] = male
            rec[f"{ind}_Female"] = female

            rec[f"{ind}_sex_diff"] = np.nan
            rec[f"{ind}_sex_ratio"] = np.nan
            if pd.notna(male) and pd.notna(female):
                rec[f"{ind}_sex_diff"] = male - female
                rec[f"{ind}_sex_ratio"] = male / female if female != 0 else np.nan

            for race in race_labels:
                val = sub.loc[sub["stratification1"] == race, "datavalue_scaled"].mean()

                short = "White" if "White" in race.split(",")[0] else "Black"
                rec[f"{ind}_{short}"] = val
            b_val = rec.get(f"{ind}_Black")
            w_val = rec.get(f"{ind}_White")
            rec[f"{ind}_race_diff"] = np.nan
            rec[f"{ind}_race_ratio"] = np.nan
            if pd.notna(b_val) and pd.notna(w_val):
                rec[f"{ind}_race_diff"] = b_val - w_val
                rec[f"{ind}_race_ratio"] = b_val / w_val if w_val != 0 else np.nan
        records.append(rec)


    pivot_df = pd.DataFrame(records)

    pivot_df.sort_values(["locationabbr", "year"], inplace=True)


    for ind in INDICATOR_MAP.values():
        col = f"{ind}_overall"
        yoy_col = f"{ind}_yoy_change"
        pivot_df[yoy_col] = pivot_df.groupby("locationabbr")[col].diff()

        pivot_df[yoy_col] = pivot_df[yoy_col].fillna(0)


    try:
        pivot_df["Smoking_vs_Prevalence_Diff"] = (
            pivot_df["Smoking_Rate_overall"] - pivot_df["COPD_Prevalence_overall"]
        )
        pivot_df["Smoking_vs_Prevalence_Ratio"] = pivot_df["Smoking_Rate_overall"] / pivot_df["COPD_Prevalence_overall"]

        pivot_df["Mortality_Any_vs_Underlying_Diff"] = (
            pivot_df["Mortality_Any_Cause_overall"] - pivot_df["Mortality_Underlying_overall"]
        )
        pivot_df["Mortality_Any_vs_Underlying_Ratio"] = (
            pivot_df["Mortality_Any_Cause_overall"] / pivot_df["Mortality_Underlying_overall"]
        )

        pivot_df["Hospitalization_Principal_vs_Any_Diff"] = (
            pivot_df["Hospitalization_Principal_Dx_overall"] - pivot_df["Hospitalization_Any_Dx_overall"]
        )
        pivot_df["Hospitalization_Principal_vs_Any_Ratio"] = (
            pivot_df["Hospitalization_Principal_Dx_overall"] / pivot_df["Hospitalization_Any_Dx_overall"]
        )
    except KeyError:
        pass

    import numpy as _np


    def _add_residual_feature(x_col: str, y_col: str, new_col: str) -> None:
        x = pivot_df[x_col]
        y = pivot_df[y_col]
        mask = x.notna() & y.notna()
        if mask.sum() > 1:

            m, b = _np.polyfit(x[mask], y[mask], 1)
            pivot_df[new_col] = y - (m * x + b)
        else:
            pivot_df[new_col] = _np.nan


    _add_residual_feature(
        "Smoking_Rate_overall", "Mortality_Underlying_overall", "Smoking_Mortality_Underlying_Residual"
    )

    _add_residual_feature(
        "Smoking_Rate_overall", "Mortality_Any_Cause_overall", "Smoking_Mortality_Any_Residual"
    )

    _add_residual_feature(
        "Smoking_Rate_overall", "COPD_Prevalence_overall", "Smoking_Prevalence_Residual"
    )

    _add_residual_feature(
        "COPD_Prevalence_overall", "Mortality_Underlying_overall", "Prevalence_Mortality_Residual"
    )

    def prune_obvious_collinearity(df_in: pd.DataFrame) -> pd.DataFrame:
        cols = list(df_in.columns)
        drop = set()

        # 1) Drop log versions (highly correlated with originals in this dataset)
        drop.update([c for c in cols if c.endswith("_log_overall")])

        # 2) If we have an overall level for an indicator, drop subgroup LEVELS
        #    (Male/Female/White/Black) and keep only disparity features (diff/ratio) if desired.
        for ind in INDICATOR_MAP.values():
            base = f"{ind}_overall"
            if base in cols:
                drop.update([f"{ind}_Male", f"{ind}_Female", f"{ind}_White", f"{ind}_Black"])

        # 3) Ratio features are often unstable and collinear with levels/diffs; keep diffs only
        drop.update([c for c in cols if c.endswith("_sex_ratio") or c.endswith("_race_ratio")])

        # 4) Interaction ratios also tend to duplicate information; keep diffs
        drop.update([
            "Smoking_vs_Prevalence_Ratio",
            "Mortality_Any_vs_Underlying_Ratio",
            "Hospitalization_Principal_vs_Any_Ratio",
        ])

        # 4b) OPTION B: don't keep both raw and residual views of the same relationship
        residual_cols = [
            "Smoking_Mortality_Underlying_Residual",
            "Smoking_Mortality_Any_Residual",
            "Smoking_Prevalence_Residual",
            "Prevalence_Mortality_Residual",
        ]
        if not KEEP_RESIDUAL_FEATURES:
            drop.update([c for c in residual_cols if c in cols])
        else:
            drop.update([c for c in [
                "Smoking_Rate_overall",
                "COPD_Prevalence_overall",
                "Mortality_Underlying_overall",
                "Mortality_Any_Cause_overall",
            ] if c in cols])

        # 5) Avoid linear dependence with hospitalization: keep the two levels, drop the diff
        #    (diff is almost deterministic from the two levels)
        if "Hospitalization_Principal_Dx_overall" in cols and "Hospitalization_Any_Dx_overall" in cols:
            drop.add("Hospitalization_Principal_vs_Any_Diff")

        # 6) Remove any dropped columns that don't exist
        drop = [c for c in drop if c in df_in.columns]
        if drop:
            print(f"Pruning {len(drop)} obvious redundant features (logs/subgroup levels/ratios).")
            print("Pruned features (first 30):", drop[:30])
        return df_in.drop(columns=drop, errors="ignore")

    pivot_df = prune_obvious_collinearity(pivot_df)

    feature_cols = [c for c in pivot_df.columns if c not in ("locationabbr", "year")]
    pivot_df[feature_cols] = pivot_df[feature_cols].apply(lambda s: s.fillna(s.mean()), axis=0)
    pivot_df[feature_cols] = pivot_df[feature_cols].replace([np.inf, -np.inf], np.nan).apply(lambda s: s.fillna(s.mean()), axis=0)

    X = pivot_df[feature_cols].to_numpy(dtype=float)

    means = np.nanmean(X, axis=0)
    vars_ = np.nanvar(X, axis=0)

    var_thresh = 1e-10
    keep = vars_ > var_thresh

    is_binary = np.array([
        (lambda u: (len(u) <= 2) and np.isin(u, [0.0, 1.0]).all())(np.unique(X[~np.isnan(X[:, j]), j]))
        for j in range(X.shape[1])
    ])

    rare_thresh = 0.01
    if is_binary.any():
        bin_means = means[is_binary]
        bin_keep = (bin_means >= rare_thresh) & (bin_means <= (1.0 - rare_thresh))
        keep_idx = np.where(is_binary)[0]
        keep[keep_idx] &= bin_keep

    near_const_thresh = 1e-8
    keep &= (np.sqrt(vars_) > near_const_thresh)

    dropped = [feature_cols[i] for i in range(len(feature_cols)) if not keep[i]]
    if dropped:
        print(f"Dropping {len(dropped)} low-variance/near-constant/rare-binary features.")
        print("Dropped features (first 30):", dropped[:30])

    kept_cols = [feature_cols[i] for i in range(len(feature_cols)) if keep[i]]
    pivot_df = pivot_df[["locationabbr", "year"] + kept_cols].copy()

    feature_cols = kept_cols
    X = pivot_df[feature_cols].to_numpy(dtype=float)

    def report_high_correlations(Xmat, names, thresh=CORR_THRESH, max_pairs=MAX_CORR_PAIRS_PRINT):
        Xmat = np.asarray(Xmat, dtype=float)
        p = Xmat.shape[1]
        if p < 2:
            print("\n[Multicollinearity] Not enough features for correlation check.")
            return

        if FAST_MODE and p > MAX_FEATURES_FOR_CORR:
            vars_local = Xmat.var(axis=0)
            idx = np.argsort(vars_local)[-MAX_FEATURES_FOR_CORR:]
            Xmat = Xmat[:, idx]
            names = [names[i] for i in idx]
            p = Xmat.shape[1]
            print(f"\n[Multicollinearity] Correlation check restricted to top-{p} features by variance (FAST_MODE).")

        corr = np.corrcoef(Xmat, rowvar=False)
        corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)

        iu = np.triu_indices(p, k=1)
        vals = corr[iu]
        mask = np.abs(vals) >= thresh

        if not np.any(mask):
            print(f"\n[Multicollinearity] No pairs with |corr| >= {thresh}.")
            return

        sel_vals = vals[mask]
        sel_i = iu[0][mask]
        sel_j = iu[1][mask]

        order = np.argsort(-np.abs(sel_vals))
        order = order[:max_pairs]

        print(f"\n[Multicollinearity] Highly correlated pairs |corr| >= {thresh} (top {len(order)}):")
        for k, t in enumerate(order, start=1):
            i = int(sel_i[t]); j = int(sel_j[t]); c = float(sel_vals[t])
            print(f"  {k:>2}. {names[i]}  vs  {names[j]}  corr={c:.3f}")

    def compute_vif(Xmat, names):
        Xmat = np.asarray(Xmat, dtype=float)
        p = Xmat.shape[1]
        if p == 0:
            return pd.Series(dtype=float)

        if FAST_MODE and p > MAX_FEATURES_FOR_VIF:
            vars_local = Xmat.var(axis=0)
            idx = np.argsort(vars_local)[-MAX_FEATURES_FOR_VIF:]
            Xmat = Xmat[:, idx]
            names = [names[i] for i in idx]
            p = Xmat.shape[1]
            print(f"\n[Multicollinearity] VIF restricted to top-{p} features by variance (FAST_MODE).")

        Xc = Xmat - Xmat.mean(axis=0, keepdims=True)
        Xc = Xc / (Xc.std(axis=0, keepdims=True) + 1e-12)

        R = (Xc.T @ Xc) / max(Xc.shape[0] - 1, 1)
        R = np.nan_to_num(R, nan=0.0, posinf=0.0, neginf=0.0)

        try:
            R_inv = np.linalg.pinv(R)
            vifs = np.diag(R_inv)
        except Exception:
            vifs = np.full(p, np.nan)

        return pd.Series(vifs, index=list(names)).sort_values(ascending=False)

    if FAST_MODE:
        print("\n[Multicollinearity] FAST_MODE=True: skipping correlation/VIF checks. Set FAST_MODE=False to enable.")
    else:
        report_high_correlations(X, feature_cols)
        vifs = compute_vif(X, feature_cols)
        print("\n[Multicollinearity] Top 15 VIF:")
        print(vifs.head(15).to_string())

    scaler = StandardScaler()
    scaled_array = scaler.fit_transform(X)
    scaled_df = pd.DataFrame(scaled_array, columns=[f"{c}_z" for c in feature_cols], index=pivot_df.index)
    normalized_df = pd.concat([pivot_df[["locationabbr", "year"]], scaled_df], axis=1)
    if config.save_csv:
        os.makedirs(os.path.dirname(config.pivot_csv_path), exist_ok=True)
        pivot_df.to_csv(config.pivot_csv_path, index=False)
        os.makedirs(os.path.dirname(config.normalized_csv_path), exist_ok=True)
        normalized_df.to_csv(config.normalized_csv_path, index=False)

    return pivot_df, normalized_df


if __name__ == "__main__":
    cfg = FeatureEngineeringConfig(save_csv=True)
    pivot, normalized = build_features(cfg)
    print(f"Feature engineering complete. Pivot shape: {pivot.shape}, Normalised shape: {normalized.shape}")
