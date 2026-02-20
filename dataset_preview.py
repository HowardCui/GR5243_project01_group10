#!/usr/bin/env python 3.12
# -*- coding: utf-8 -*-
# time: 2026/02/16
# name: Haowen Cui, Yuhan Guo, Selina Peng(sp4550)

from acquire import get_dataset
import matplotlib.pyplot as plt
import numpy as np

def init_data_check(dataset):
    """
    Check initial structural and quality of the raw dataset.
    Parameters
    ---
    dataset : pandas.DataFrame
        The raw dataset obtained from the CDC API.
    :return: None
    """
    df = dataset.copy()
    # dataset dimensions
    print('#################')
    print('dataset dimensions')
    print(df.shape)
    print('#################')
    print()
    # Check column names
    print('#################')
    print('column names')
    print(df.columns)
    print('#################')
    print()
    # Review data types
    print('#################')
    print('data types')
    print(df.dtypes)
    print('#################')
    print()
    # Calculate missing value proportions
    print('#################')
    print('missing value proportions:')
    print(df.isna().mean().sort_values(ascending=False).head(20))
    print('#################')
    print()
    # Check duplicate rows
    print('#################')
    print('duplicate rows')
    print(df.duplicated().sum())
    print('#################')
    print()
    # Check temporal consistency of records.
    print('#################')
    print('temporal consistency: yearstart != yearend')
    print((df["yearstart"] != df["yearend"]).sum())
    print('#################')
    print()
    # Identify cases where the primary data is missing but alternative data exists.
    print('#################')
    print('primary missing but alternative exists (count)')
    print((df["datavalue"].isna() & df["datavaluealt"].notna()).sum())
    print('#################')
    print()
    # Check number of records
    print('#################')
    print(df["topic"].value_counts().head(10))
    print('#################')
    print()

def data_check_to_justify_cleaning(dataset):
    """
    Check data quality issues that justify the cleaning steps we will take.
    Parameters
    ---
    dataset : pandas.DataFrame
        The raw dataset obtained from the CDC API.
    :return: None
    """
    df = dataset.copy()
    # Check for columns that are completely empty (all values are NaN).
    empty_cols = df.columns[df.isna().all()]
    print('#################')
    print('Completely empty columns - to be deleted during cleaning:')
    print(empty_cols)
    print('#################')
    print()

    # Check for differences between primary data and alternative data.
    # For records where both datavalue and datavaluealt are present, look at the pairs with large percentage differences.
    # Compute datavaluealtdiffpct only when both columns are present; otherwise set NaN.
    df["datavaluealtdiffpct"] = np.nan
    mask = (df["datavalue"].notna()) & (df["datavaluealt"].notna())
    if mask.any():
        diff = (df.loc[mask, "datavaluealt"] - df.loc[mask, "datavalue"]).abs()
        df.loc[mask, "datavaluealtdiffpct"] = diff / df.loc[mask, "datavalue"]
    print('#################')
    print('Records with >5% difference between primary and alternative data:')
    print('Clearly an error (extra digit) in alternative - entries to be deleted during cleaning:')
    print(df.loc[df["datavaluealtdiffpct"]>0.05, ["datavalue","datavaluealt","datavaluealtdiffpct"]])
    print('Otherwise, no clear differences between primary and alternative data, so we will keep only primary data during cleaning.\n\n')
    print('#################')
    print()

    # Check for records with data value footnotes, which may indicate data quality issues or special cases that require attention during cleaning.
    print('#################')
    print('Records with non-empty data value footnotes & their proportions to total #entries in dataset:')
    print('The following shows that 1) datavaluefootnotesymbol and datavaluefootnote have 1-to-1 mapping, and\n2) Each type of datavaluefootnote corresponds to a specific cause of missing data, or abnormal data that can only be used with extreme caution.')
    print('We will hence delete all records with data value footnotes during cleaning, since they all have missing or potentially unreliable data values.')
    print(df.groupby(["datavaluefootnotesymbol", "datavaluefootnote"]).size()/len(df))
    print('#################')
    print()

def check_COPD(dataset):
    """
    Check initial structural and quality of the COPD(Chronic Obstructive Pulmonary Disease) dataset.
    Parameters
    ---
    dataset : pandas.DataFrame
        The raw dataset obtained from the CDC API.
    :return: None
    """
    df = dataset.copy()
    df_copd = df[df["topic"] == "Chronic Obstructive Pulmonary Disease"]
    question_counts=df_copd["question"].value_counts()

    plt.figure()
    question_counts.plot(kind="bar")
    plt.title("Number of Records by COPD Question")
    plt.ylabel("Count")
    plt.show()

    print('#################')
    print('Number of records for each COPD question, data value unit, and data value type:')
    print(df_copd.groupby(["question","datavalueunit","datavaluetype"]).size())
    print('#################')
    print()

    # --- Histogram for each question ---
    for q in df_copd["question"].unique():
        subset = df_copd[df_copd["question"] == q]

        units = subset["datavalueunit"].dropna().unique()

        if len(units) == 1:
            unit_label = units[0]
        elif len(units) > 1:
            unit_label = "Multiple Units"
            print('#################')
            print(subset["datavaluetype"].unique())
            print('#################')
            print()
        else:
            unit_label = "Value"

        plt.figure()
        subset["datavalue"].hist(bins=30)

        plt.title(f"Distribution of:\n{q}")
        plt.xlabel(f"Indicator Value ({unit_label})")
        plt.ylabel("Frequency (Number of Observations)")
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    dataset = get_dataset(use_local=True)
    init_data_check(dataset)
    data_check_to_justify_cleaning(dataset)
    check_COPD(dataset)
