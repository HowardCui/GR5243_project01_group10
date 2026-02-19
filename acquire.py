#!/usr/bin/env python 3.12
# -*- coding: utf-8 -*-
# time: 2026/02/04
# name: Haowen Cui, Yuhan Guo, Selina Peng

import sys
import time
import pandas as pd
import requests
import os

#source page: https://data.cdc.gov/Chronic-Disease-Indicators/U-S-Chronic-Disease-Indicators/hksd-2xuw/about_data
def get_dataset(use_local=True, sample_n=None, local_path="data/cdc_raw.csv"):
    """
    get CDC Chronic Disease Indicators data
    Parameters
    ---
    use_local : bool
        If True, load data from local_path.
        If False, download from API and save to raw file path "data/cdc_raw.csv".
    sample_n : int or None
        If provided, only load/download first N rows (for fast testing).
    local_path : str
        Local csv path. Default is raw file path "data/cdc_raw.csv".
        Example for alternative path: "data/cdc_cleaned_copd.csv" for cleaned data.
    :return: pandas DataFrame
    """
    raw_path = "data/cdc_raw.csv"

    if use_local:
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"local file not found: {local_path}")
        print("loading data from local...")
        df = pd.read_csv(local_path)
        if sample_n:
            df = df.head(sample_n)
        return df

    # ----- use_local is False, download from API and save to raw_path -----
    
    if local_path != raw_path:
        print(
            f"warning: local_path '{local_path}' is ignored when use_local=False; "
            f"API data will be saved to '{raw_path}'."
        )

    #SODA2 API request
    url = r'https://data.cdc.gov/resource/hksd-2xuw.json'
    try:
        all_data = []
        offset = 0
        while True:
            params = {
                "$limit": 50000,
                "$offset": offset
            }
            response = requests.get(url, params=params)
            data = response.json()

            if not data:
                break

            all_data.extend(data)
            offset += 50000
            print(f"loaded rows: {len(all_data)}")
            time.sleep(1.0)

            if sample_n and len(all_data) >= sample_n:
                print(f"sample mode: reached {sample_n} rows, stopping download.")
                break

        df = pd.DataFrame(all_data)

        if sample_n:
            df = df.head(sample_n)

        if not sample_n:
            os.makedirs("data", exist_ok=True)
            df.to_csv(raw_path, index=False)
            print(f"saved data to {raw_path}")

        return df

    except Exception as e:
        print(f'request failed: {e}')

if __name__ == "__main__":
    # check python version
    print(f'python version: {sys.version}')
    dataset = get_dataset(use_local=True)
    # preview
    print(dataset.head())
    print(dataset.shape)


