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
def get_dataset(use_local=True,sample_n=None):
    """
    get CDC Chronic Disease Indicators data
    Parameters
    ---
    use_local : bool
        If True, load data from local if exists.
    sample_n : int or None
        If provided, only download first N rows (for fast testing).
    :return: pandas DataFrame
    """
    #local data path
    local_path = "data/cdc_raw.csv"

    if use_local and os.path.exists(local_path):
        print("loading data from local...")
        df = pd.read_csv(local_path)
        if sample_n:
            df = df.head(sample_n)
        return df

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

        if use_local and not sample_n:
            os.makedirs("data", exist_ok=True)
            df.to_csv(local_path, index=False)
            print(f"saved data to {local_path}")

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



