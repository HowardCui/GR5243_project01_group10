#!/usr/bin/env python 3.12
# -*- coding: utf-8 -*-
# time: 2026/02/13
# name: Haowen Cui, Yuhan Guo

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from acquire import get_dataset


def EDA():
	df = pd.read_csv(r'data/cdc_cleaned_copd.csv')

	# ========================
	# EDA starts here
	# ========================

	# TODO: add your EDA code below
	_ = df


if __name__ == "__main__":
	EDA()

