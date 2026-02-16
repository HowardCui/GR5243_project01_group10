#!/usr/bin/env python 3.12
# -*- coding: utf-8 -*-
# time: 2026/02/13
# name: Haowen Cui, Yuhan Guo

if __name__ == "__main__":
    # dataset check
    df=dataset.copy()
    print(df.shape)
    print(df.columns)
    print(df.dtypes)
    print(df.isna().mean().sort_values(ascending=False).head(20))
