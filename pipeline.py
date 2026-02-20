#!/usr/bin/env python 3.12
# -*- coding: utf-8 -*-
# time: 2026/02/13
# name: Haowen Cui, Yuhan Guo, Shiyue Peng sp4550, Shengbo Yi

from acquire import get_dataset
from dataset_preview import init_data_check, data_check_to_justify_cleaning, check_COPD
from clean import clean
from EDA import EDA
from features import build_features, FeatureEngineeringConfig


def pipeline(test_acquire_from_URL=False):
    """
    Execute the complete data pipeline: acquisition, preview, cleaning, EDA, and feature engineering.
    
    Parameters
    ---
    test_acquire_from_URL : bool, default False
        If True, fetch dataset of 100k rows from CDC API using get_dataset(use_local=False).
        If False, skip acquisition and proceed directly to preview.
    
    Returns
    -------
    None
    """
    
    # -------- Data Acquisition --------
    if test_acquire_from_URL:
        print("######## Test ACQUISITION #########")
        dataset = get_dataset(use_local=False, sample_n=100000)  # Fetch a sample of 100k rows for testing  
        print("#################")
        print()
    
    # -------- Data Preview --------
    print("######## Test DATASET_PREVIEW #########")
    dataset = get_dataset(use_local=True)
    init_data_check(dataset)
    data_check_to_justify_cleaning(dataset)
    check_COPD(dataset)
    print("#################")
    print()
    
    # -------- Data Cleaning --------
    print("######## Test CLEAN #########")
    df_cleaned = clean()
    print("#################")
    print()
    
    # -------- Exploratory Data Analysis --------
    print("######## Test EDA #########")
    EDA()
    print("#################")
    print()
    
    # -------- Feature Engineering --------
    print("######## Test FEATURE_ENGINEERING #########")
    config = FeatureEngineeringConfig(save_csv=True)
    pivot_df, normalized_df = build_features(config)
    print(f"Feature engineering complete. Pivot shape: {pivot_df.shape}, Normalized shape: {normalized_df.shape}")
    print("#################")
    print()


if __name__ == "__main__":
    pipeline(test_acquire_from_URL=False)
