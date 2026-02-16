#!/usr/bin/env python 3.12
# -*- coding: utf-8 -*-
# time: 2026/02/16
# name: Haowen Cui, Yuhan Guo

from acquire import get_dataset

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

if __name__ == "__main__":
    dataset = get_dataset(use_local=True)
    init_data_check(dataset)
