#!/usr/bin/env python 3.12
# -*- coding: utf-8 -*-
# time: 2026/02/13
# name: Haowen Cui, Yuhan Guo Shengbo Yi


from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
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
    pivot_csv_path: str = "processed/cdc_pivot_features.csv"
    normalized_csv_path: str = "processed/cdc_normalized_features.csv"


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

    
    feature_cols = [c for c in pivot_df.columns if c not in ("locationabbr", "year")]
    
    pivot_df[feature_cols] = pivot_df[feature_cols].apply(
        lambda x: x.fillna(x.mean()), axis=0
    )

    
    scaler = StandardScaler()
    scaled_array = scaler.fit_transform(pivot_df[feature_cols])
    scaled_df = pd.DataFrame(
        scaled_array, columns=[f"{c}_z" for c in feature_cols], index=pivot_df.index
    )
    normalized_df = pd.concat([
        pivot_df[["locationabbr", "year"]], scaled_df
    ], axis=1)

    
    if config.save_csv:
        
        os.makedirs(os.path.dirname(config.pivot_csv_path), exist_ok=True)
        pivot_df.to_csv(config.pivot_csv_path, index=False)
        os.makedirs(os.path.dirname(config.normalized_csv_path), exist_ok=True)
        normalized_df.to_csv(config.normalized_csv_path, index=False)

    return pivot_df, normalized_df


if __name__ == "__main__":
    cfg = FeatureEngineeringConfig(save_csv=True)
    pivot, normalized = build_features(cfg)
    print(
        f"Feature engineering complete. Pivot shape: {pivot.shape}, Normalised shape: {normalized.shape}"
    )
