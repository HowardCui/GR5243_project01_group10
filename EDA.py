#!/usr/bin/env python 3.12
# -*- coding: utf-8 -*-
# time: 2026/02/13
# name: Haowen Cui, Yuhan Guo

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
from acquire import get_dataset


def plot_1d_distribution(
		df,
		column,
		nbins=None,
		xtitle=None,
		title_extra="",
		png_name=None,
		filter_pair_list=None,
):
	"""
	Plot histogram for a column with optional multi-filter support.

	Parameters
	----------
	df : pandas.DataFrame
		Input data.
	column : str
		Column name to plot (must exist in df).
	nbins : int, optional
		Number of histogram bins.
	xtitle : str, optional
		X-axis label (defaults to column name).
	title_extra : str, optional
		Extra text for title.
	png_name : str, optional
		Save plot to file if provided.
	filter_pair_list : list of tuples, optional
		Filters as [(col1, val1), (col2, val2), ...].
		Combines all filters with AND logic. Skips invalid filters with warning.
		Example: [("state", "CA"), ("age_group", "65+")]

	Examples
	--------
	plot_1d_distribution(df, "age", nbins=20, xtitle="Age (years)")
	plot_1d_distribution(df, "value", filter_pair_list=[("state", "CA")], png_name="out.png")
	"""
	if column not in df.columns:
		print(f"warning: column '{column}' not found in dataset; skip plotting.")
		return

	# Build combined mask from all filter pairs that pass sanity check
	plot_df = df
	applied_filters = []

	if filter_pair_list is not None:
		mask = pd.Series([True] * len(df), index=df.index)
		for column_filter, value_filter in filter_pair_list:
			if column_filter not in df.columns:
				print(
					f"warning: filter column '{column_filter}' not found; "
					"skipping this filter."
				)
			else:
				filter_mask = df[column_filter] == value_filter
				if filter_mask.sum() > 0:
					mask = mask & filter_mask
					applied_filters.append((column_filter, value_filter))
				else:
					print(
						f"warning: filter ({column_filter}={value_filter}) has 0 entries; "
						"skipping this filter."
					)
		plot_df = df[mask]

	series = pd.to_numeric(plot_df[column], errors="coerce").dropna()
	if series.empty:
		print(f"warning: no valid values to plot for '{column}'.")
		return

	plt.figure()
	if nbins is not None:
		plt.hist(series, bins=nbins)
	else:
		plt.hist(series)

	if xtitle is not None:
		plt.xlabel(xtitle)
	else:
		plt.xlabel(column)
	plt.ylabel("Count")

	title_suffix = f" {title_extra}" if title_extra else ""
	if applied_filters:
		filter_str = ", ".join(
			f"{col} = {val}" for col, val in applied_filters
		)
		plt.title(
			f"Distribution of {column}\n"
			f"({filter_str}{title_suffix})"
		)
	else:
		plt.title(f"Distribution of {column}{title_suffix}")

	if png_name is not None:
		png_dir = os.path.dirname(png_name)
		if png_dir:
			os.makedirs(png_dir, exist_ok=True)
		plt.savefig(png_name, bbox_inches="tight")

	plt.show()


def EDA():
	df = get_dataset(use_local=True, local_path="data/cdc_cleaned_copd.csv")

	# ========================
	# EDA starts here
	# ========================

	# TODO: add your EDA code below
	_ = df


if __name__ == "__main__":
	EDA()

