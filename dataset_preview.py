#!/usr/bin/env python 3.12
# -*- coding: utf-8 -*-
# time: 2026/02/16
# name: Haowen Cui, Yuhan Guo

from acquire import get_dataset
import matplotlib.pyplot as plt

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
    print('dataset dimensions')
    print(df.shape)
    print('-')
    # Check column names
    print('column names')
    print(df.columns)
    print('-')
    # Review data types
    print('data types')
    print(df.dtypes)
    print('-')
    # Calculate missing value proportions
    print('missing value proportions:')
    print(df.isna().mean().sort_values(ascending=False).head(20))
    print('-')
    # Check duplicate rows
    print('duplicate rows')
    print(df.duplicated().sum())
    # Check temporal consistency of records.
    print((df["yearstart"] != df["yearend"]).sum())
    print('-')
    # Identify cases where the primary data is missing but alternative data exists.
    print((df["datavalue"].isna() & df["datavaluealt"].notna()).sum())
    # Check number of records
    print(df["topic"].value_counts().head(10))

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

    # --- Histogram for each question ---
    for q in df_copd["question"].unique():
        subset = df_copd[df_copd["question"] == q]

        units = subset["datavalueunit"].dropna().unique()

        if len(units) == 1:
            unit_label = units[0]
        elif len(units) > 1:
            unit_label = "Multiple Units"
            print(subset["datavaluetype"].unique())
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
    check_COPD(dataset)