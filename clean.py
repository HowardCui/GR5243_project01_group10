#!/usr/bin/env python 3.12
# -*- coding: utf-8 -*-
# time: 2026/02/13
# name: Haowen Cui, Yuhan Guo, Selina Peng

import pandas as pd
import numpy as np
import os
from acquire import get_dataset


def clean():
    """
    Clean CDC Chronic Disease Indicators data
    :return: pandas DataFrame
        The cleaned dataset containing only COPD-related records and with data quality issues addressed.
    See dataset_preview.py (function data_check_to_justify_cleaning) for the data quality issues we identified that justify these cleaning steps.
    """
    # Read the raw dataset
    df = get_dataset(use_local=True)
    
    # Cleaning operations

    # keep only COPD related records
    df_copd = df[df["topic"] == "Chronic Obstructive Pulmonary Disease"]

    # delete problematic rows, empty & unnecessary columns
    df_copd = delete_empty_columns(df_copd)
    df_copd = data_problematic_rows_removal(df_copd)
    df_copd = delete_unnecessary_columns(df_copd)

    # Save cleaned data
    os.makedirs("data", exist_ok=True)
    df_copd.to_csv("data/cdc_cleaned_copd.csv", index=False)
    print("Cleaned data saved to data/cdc_cleaned_copd.csv")
    
    return df_copd

def delete_empty_columns(df):
    """
    Delete columns that are completely empty (all values are NaN).
    Parameters
    ---
    df : pandas.DataFrame
        The dataset to be cleaned.
    :return: pandas.DataFrame
        The cleaned dataset with empty columns removed.
    """
    return df.dropna(axis=1, how='all')

def data_problematic_rows_removal(df):
    """
    Remove rows with problematic data issues, such as temporal inconsistencies or missing primary data.
    Parameters
    ---
    df : pandas.DataFrame
        The dataset to be cleaned.
    :return: pandas.DataFrame
        The cleaned dataset with problematic rows removed.
    """
    # Remove rows where datavalue is missing, since imputating these values would be unreliable (see README.md for details).
    df = df[~(df["datavalue"].isna())]

    # Compute datavaluealtdiffpct only when both datavalue and datavaluealt are present.
    # If either is missing, set to NaN
    df["datavaluealtdiffpct"] = np.nan
    mask = (df["datavalue"].notna()) & (df["datavaluealt"].notna())
    if mask.any():
        diff = (df.loc[mask, "datavaluealt"] - df.loc[mask, "datavalue"]).abs()
        df.loc[mask, "datavaluealtdiffpct"] = diff / df.loc[mask, "datavalue"]

    # Keep rows where the difference is <=5% or where we don't have an alternative value (NaN)
    # the latter is kept since we will ignore alternative value anyway (see dataset_preview.py for details)
    df = df[df["datavaluealtdiffpct"].isna() | (df["datavaluealtdiffpct"] <= 0.05)]

    # Remove rows with data value footnotes, since they all have missing or potentially unreliable data values (see dataset_preview.py for details).
    df = df[df["datavaluefootnote"].isna()]

    # Remove rows with datavaluetype == "Number": from dataset preview, these rows have multiple units and a vast range of scales
    # Besides, the same sample points are often duplicated with datavaluetype == "Crude/Age averages rate", which is more interpretable and easier to analyze
    df = df[df["datavaluetype"] != "Number"]
    return df

def delete_unnecessary_columns(df):
    """
    Delete columns that are not necessary for our analysis.
    Parameters
    ---
    df : pandas.DataFrame
        The dataset to be cleaned.
    :return: pandas.DataFrame
        The cleaned dataset with unnecessary columns removed.
    """

    df_copy = df.copy()
    
    # drop data value alternative column: we have removed rows with large differences between primary and alternative data
    df_copy = df_copy.drop(columns=["datavaluealt","datavaluealtdiffpct"], errors="ignore")
    
    # drop data value footnote columns: we have removed rows with non-empty data value footnotes, which all have missing or potentially unreliable data values
    df_copy = df_copy.drop(columns=["datavaluefootnotesymbol","datavaluefootnote"], errors="ignore")

    # drop topic & topicid column: we have filtered to keep only COPD-related records, so topic column should be zero-variance
    # safeguard: only drop if it has exactly one unique value
    if "topic" in df_copy.columns and df_copy["topic"].nunique() == 1:
        df_copy = df_copy.drop(columns=["topic"], errors="ignore")
    if "topicid" in df_copy.columns and df_copy["topicid"].nunique() == 1:
        df_copy = df_copy.drop(columns=["topicid"], errors="ignore")
    
    # drop geolocation: too fine for our analysis
    df_copy = df_copy.drop(columns=["geolocation"], errors="ignore")

    # drop confidence limit columns: these are often missing so it's hard to use them in our analysis
    df_copy = df_copy.drop(columns=["lowconfidencelimit","highconfidencelimit"], errors="ignore")

    # check for redundant ID columns and drop them if they are 1-to-1 mappings to their human-readable counterparts
    df_copy = check_redundant_ID_columns(df_copy)

    return df_copy


def check_redundant_ID_columns(df):
    """
    Detect and remove redundant ID columns when they are 1-to-1 mappings to
    their human-readable counterparts.

    Rules implemented:
    - For each pair (name, id) such as `topic`/`topicid`, if `id` maps to a
      single `name` for every non-null id (i.e. id -> name is unique), drop
      the `id` column.
    - Special-case for location: check `locationid` against `locationabbr` and
      `locationdesc`. If `locationid` maps 1-to-1 to either one, drop
      `locationid`. If it maps 1-to-1 to both, also drop `locationdesc`.

    The function is case-insensitive to column-name capitalization: it will
    find the actual column names in the dataframe and drop the original
    columns accordingly.

    Returns a dataframe with redundant columns removed.
    """
    df_copy = df.copy()

    # map lowercase -> actual column name in df
    col_map = {c.lower(): c for c in df_copy.columns}

    def has(col_lower):
        return col_lower in col_map

    def real(col_lower):
        return col_map[col_lower]

    dropped = []

    # Special-case: location
    if has("locationid"):
        locid = real("locationid")
        mapped_to_abbr = False
        mapped_to_desc = False

        if has("locationabbr"):
            la = real("locationabbr")
            tmp = df_copy[[locid, la]].dropna()
            if not tmp.empty:
                mapped_to_abbr = tmp.groupby(locid)[la].nunique().max() == 1

        if has("locationdesc"):
            ld = real("locationdesc")
            tmp = df_copy[[locid, ld]].dropna()
            if not tmp.empty:
                mapped_to_desc = tmp.groupby(locid)[ld].nunique().max() == 1

        if mapped_to_abbr or mapped_to_desc:
            df_copy = df_copy.drop(columns=[locid], errors="ignore")
            dropped.append(locid)
            if mapped_to_abbr and mapped_to_desc and has("locationdesc"):
                # per spec: if id is 1-to-1 with both, also drop LocationDesc
                df_copy = df_copy.drop(columns=[real("locationdesc")], errors="ignore")
                dropped.append(real("locationdesc"))

    # Generic pairs: (name, id) -> drop id if id -> name is unique
    pairs = [
        ("topic", "topicid"),
        ("question", "questionid"),
        ("stratification1", "stratificationid1"),
        ("datavaluetype", "datavaluetypeid"),
        ("stratificationcategory1", "stratificationcategoryid1"),
    ]

    for name_l, id_l in pairs:
        if has(name_l) and has(id_l):
            name_col = real(name_l)
            id_col = real(id_l)
            tmp = df_copy[[id_col, name_col]].dropna()
            if not tmp.empty:
                try:
                    if tmp.groupby(id_col)[name_col].nunique().max() == 1:
                        df_copy = df_copy.drop(columns=[id_col], errors="ignore")
                        dropped.append(id_col)
                except Exception:
                    # in case of unhashable types or other grouping issues,
                    # skip and continue
                    continue

    if dropped:
        print("Dropped redundant columns:", dropped)
    else:
        print("No redundant ID columns detected.")

    return df_copy

if __name__ == "__main__":
    # run cleaning when executed as a script
    clean()
