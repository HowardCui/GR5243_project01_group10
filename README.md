# GU5243 Project01
### Collaborators：Haowen Cui(@HowardCui), Yuhan Guo(@FlamyFlame), Selina Peng(@Skyerrrrrrr)，Shengbo Yi(@superwayne66)
## Project Introduction
(project intro ....)

## Data Acquisition
This project utilizes data from the CDC U.S. Chronic Disease Indicators (CDI) dataset, a publicly accessible dataset provided by the Centers for Disease Control and Prevention (CDC).
The CDI dataset includes multiple health-related indicators across U.S. states, covering topics such as chronic diseases, behavioral risk factors, preventive health measures, and demographic stratifications.

This dataset is accessed through the Socrata Open Data API (SODA2). Since this API can return at most 50,000 records per request, we use $limit and $offset to implement the query. To obtain the complete dataset, we used a while loop and set appropriate delays to request data iteratively.

To improve development efficiency, we added a sample loading mode that allows us to load a partial dataset during testing. Additionally, we designed code that saves data locally to avoid repeated API calls while maintaining full reproducibility.

### How to use acquire.py?

The script provides a function:  

get_dataset(use_local=True, sample_n=None)

#### Requirements
Python version: Python 3.12. Install required packages: pip install pandas requests, pandas

#### Parameters
| Parameter | Type        | Description                                                |
| --------- | ----------- | ---------------------------------------------------------- |
| use_local | bool        | If True, load data from local CSV if it exists             |
| sample_n  | int or None | If provided, only download first N rows (for fast testing) |

### Dataset preview
Before performing preprocessing or formal exploratory analysis, we conducted an initial structural and quality assessment of the raw dataset. This step aims to evaluate the dataset’s overall structure, scale, and potential data quality issues.

Specifically, the `init_data_check()` function examines dataset dimensions and column structure, data types across variables, the proportion of missing values per column, the presence of duplicate records, temporal consistency between yearstart and yearend, cases where primary values are missing but alternative values exist, and the distribution of records across health topics. These checks provide an empirical overview of the dataset’s complexity and help identify potential issues that may require further cleaning.

Based on the findings from `init_data_check()`, we observed that the dataset covers a wide range of health topics with varying record counts and data completeness. To conduct a focused yet meaningful analysis, we selected Chronic Obstructive Pulmonary Disease as the primary topic. Chronic Obstructive Pulmonary Disease has a substantial number of records and relatively consistent measurement structures, making it suitable for detailed exploratory analysis.

Thus, we wrote a function called `check_COPD` that focuses on records related to Chronic Obstructive Pulmonary Disease. It evaluates the distribution of COPD-related questions, the consistency of measurement units and value types, and the distribution of numerical indicator values via histograms. This function helps us identify potential inconsistencies and quality issues, which will be beneficial for the subsequent data cleaning process.

Additionally, `data_check_to_justify_cleaning()` performs targeted data quality checks to identify issues that warrant removal during cleaning (e.g., completely empty columns, suspicious data discrepancies, data value footnotes). This function provides empirical justification for each cleaning decision implemented in `clean.py`.

### How to use dataset_preview.py?
The script provides functions:  

init_data_check(dataset)  

data_check_to_justify_cleaning(dataset)  

check_COPD(dataset) 


#### Parameters
| Parameter | Type             | Description                               |
| --------- | ---------------- | ----------------------------------------- |
| dataset   | pandas.DataFrame | The raw dataset obtained from the CDC API |

## Data Cleaning

Before formal analysis, we clean the raw dataset to improve data quality and reduce noise. The `clean.py` module provides the main cleaning pipeline.

### How to use clean.py?

The script provides a function:

clean()

This function applies all cleaning steps sequentially and returns a cleaned pandas DataFrame. It also saves the cleaned dataset to `data/cdc_cleaned_copd.csv`.

```python
from clean import clean
df_cleaned = clean()
```

#### Cleaning Steps & Justifications

1. **Filter to COPD-related records**
   - We keep only records where `topic == "Chronic Obstructive Pulmonary Disease"`
   - *Justification*: Our analysis focuses specifically on COPD; other disease topics are not relevant

2. **Remove rows with missing primary data (`datavalue`)**
   - Rows where `datavalue` is NaN are discarded
   - *Justification*: The primary data value is essential; imputation would be unreliable (see `dataset_preview.py` for column coverage analysis)

3. **Handle alternative data discrepancies**
   - We compute `datavaluealtdiffpct` only when both `datavalue` and `datavaluealt` are present
   - We keep rows where this difference is ≤5% or where alternative data is missing
   - *Justification*: Large discrepancies (>5%) suggest data entry errors; when alternative data is absent, it is safe to ignore (see `data_check_to_justify_cleaning()`)

4. **Remove rows with data value footnotes**
   - All rows where `datavaluefootnote` is non-null are removed
   - *Justification*: Footnotes indicate missing or unreliable data values that require extreme caution; excluding them ensures data reliability (see `data_check_to_justify_cleaning()`)

5. **Remove rows with `datavaluetype == "Number"`**
   - We filter out records where the data value type is "Number" (as opposed to "Crude/Age averages rate")
   - *Justification*: "Number" type records have multiple units and vastly different scales; they are often duplicated with "Crude/Age averages rate" type, which is more interpretable

6. **Drop unnecessary columns**
   - **Data quality columns**: `datavaluealt`, `datavaluealtdiffpct`, `datavaluefootnotesymbol`, `datavaluefootnote` (we have already filtered rows with issues)
   - **Zero-variance columns**: `topic`, `topicid` (all records are COPD, so single value)
   - **Geolocation**: Too fine-grained for our analysis
   - **Confidence limits**: `lowconfidencelimit`, `highconfidencelimit` (often missing, hard to use)
   - *Justification*: These columns either carry no information (after filtering), are redundant, or have too many missing values

7. **Drop redundant ID columns**
   - For each (name, id) pair (e.g., `topic`/`topicid`, `question`/`questionid`), if the ID is a 1-to-1 mapping to the name, we drop the ID column
   - **Special case for location**: If `locationid` maps 1-to-1 to `locationabbr` or `locationdesc`, we drop `locationid`. If it maps 1-to-1 to both, we also drop `locationdesc`
   - *Justification*: Redundant ID columns add no information but increase dimensionality; human-readable names are more interpretable

### Output

The cleaned dataset is saved to `data/cdc_cleaned_copd.csv` and contains only COPD records with:
- Valid, complete primary data values
- Consistent, reliable alternative data (if present)
- No suspicious footnotes or data quality flags
- Essential columns only, with redundant IDs removed

## Exploratory Data Analysis

After cleaning, we conduct a comprehensive exploratory data analysis (EDA) to understand the distributions, trends, and relationships among COPD indicators. The `EDA.py` module generates visualizations across four analytical components.

### How to use EDA.py?

The script is designed to run as a standalone executable:

```bash
python EDA.py
```

Alternatively, import and call the main function:

```python
from EDA import EDA
EDA()
```

#### Requirements
- Python version: Python 3.12
- Required packages: `pandas`, `numpy`, `matplotlib`, `seaborn`, `scipy`
- Input data: `data/cdc_cleaned_copd.csv` (output from cleaning step)

#### Output
All visualizations are saved to the `eda_png/` directory as PNG files (12 plots total):
- **PART 1**: P1A, P1B, P1C, P1D, P1E, P1F (6 plots)
- **PART 2**: P2A, P2B (2 plots)
- **PART 3**: P3A, P3B (2 plots)
- **PART 4**: P4A, P4B (2 plots)

Console output includes summary statistics, missing value counts, and correlation coefficients with p-values.

### Analysis Components

#### PART 1: Individual Indicator Distributions & Demographics

Examines each of the six COPD indicators in isolation:

**P1A: Distributions** — Histograms for each indicator (COPD Prevalence, Smoking Rate, Mortality underlying/any cause, Hospitalizations) with mean and median lines overlaid. Helps identify the distribution shape, central tendency, and spread across all state-year observations.

**P1B: Yearly Trends** — Line plots with 95% confidence bands showing how each indicator changes over time (overall, age-adjusted). Reveals temporal patterns and whether indicators are rising, falling, or stable.

**P1C: Sex Comparison** — Boxplots comparing male vs. female values for each indicator. Identifies sex-based disparities in COPD burden.

**P1D, P1E, P1F: Race/Ethnicity Comparison** — Three alternative visualizations (barplot with median + 95% CI, violinplot for full distribution, boxplot for quartiles and outliers) comparing indicators across race/ethnicity groups. All use consistent color mapping for each racial/ethnic group across all six indicators. Highlights racial/ethnic disparities in COPD burden.

**Why**: These univariate and stratified views provide foundational understanding of each indicator's range, variability, temporal trends, and demographic heterogeneity before examining relationships between indicators.

#### PART 2: Correlation & Multivariate Analysis

Examines relationships between all six indicators at the state-year level:

**P2A: Pearson Correlation Heatmap** — Lower-triangular heatmap of Pearson correlations between all indicators (computed from state-year aggregated data). Values range from −1 to +1; colors encode strength and direction.

**P2B: Pairplot** — Scatter plots of key indicator pairs with marginal distributions (KDE on diagonal). Points are colored by year to detect temporal patterns. Shows pairwise relationships visually.

**Why**: Correlation analysis identifies which indicators move together (e.g., smoking and mortality) and which are independent, informing feature engineering and modeling assumptions. Stratifying by year reveals if relationships are stable over time.

#### PART 3: Smoking vs. Mortality Deep Dive

Focuses on the hypothesized relationship between smoking behavior and mortality outcomes:

**P3A: Smoking Rate vs. Mortality Scatter Plots** — Two side-by-side scatter plots (mortality from underlying cause and from any cause) with smoking rate on x-axis. Points colored by year; OLS regression line with r and p-value reported. State abbreviations labeled for outliers (85th percentile or greater on either axis).

**P3B: Smoking vs. Prevalence Scatter** — Scatter plot of smoking rate against COPD prevalence with OLS line and correlation statistics.

**P3C: Correlation Summary Table** — Prints to console a table of Pearson r, p-value, and sample size for five key pairs: smoking→prevalence, smoking→mortality (underlying/any), and prevalence→mortality (underlying/any). Statistical significance flagged with asterisks (*, **, ***, for p < 0.05, 0.01, 0.001).

**Why**: Smoking is a primary risk factor for COPD; this analysis quantifies the strength and significance of associations. Outlier identification highlights states with unusual combinations (e.g., low smoking but high mortality, or vice versa), suggesting unmeasured confounders or data anomalies.

#### PART 4: Hierarchical Correlation by Demographics

Repeats key analyses stratified by sex and race/ethnicity:

**P4A: Smoking vs. Mortality by Sex** — Two smoking-mortality scatter plots (one per sex: Male, Female) with OLS lines and correlations. Tests whether the smoking-mortality relationship differs by sex.

**P4B: Prevalence vs. Mortality by Race/Ethnicity** — Three prevalence-mortality scatter plots (one per race/ethnicity: White non-Hispanic, Black non-Hispanic, Hispanic) with OLS lines and correlations. Tests whether prevalence-mortality relationships differ across racial/ethnic groups.

**Why**: Demographic stratification reveals whether aggregate patterns mask important subgroup heterogeneity. For example, the smoking-mortality link may be stronger for one sex, or the prevalence-mortality relationship may vary by race, reflecting differences in healthcare access, comorbidities, or disease severity.

### Data Filtering & Aggregation

- Only **age-adjusted** records are included (filtered by `datavaluetype.str.startswith("Age-adjusted")`)
- For PART 1 univariate plots: data stratified by `stratification1` (e.g., "Overall", "Male", "Female", race categories)
- For PART 2–4 correlations: data aggregated to **state-year level** by taking the mean of all records matching (locationabbr, yearstart, question)
- Missing values computed via **listwise deletion** (pairwise comparisons drop rows with any NaN in the target columns)

### Technical Notes

- **Visualization Library**: Uses `seaborn` for statistical graphics (heatmaps, boxplots, pairplots) and `matplotlib` for custom layouts
- **Statistics**: `scipy.stats.linregress()` for OLS fitting and correlation inference; `scipy.stats.pearsonr()` for bivariate Pearson correlations
- **Color Palettes**: Consistent colors across plots to aid interpretation (blues for overall/male, oranges for female, etc.)
- **Figure Management**: All plots saved with `bbox_inches='tight'` and closed after saving to prevent memory bloat; console messages track file paths

## Feature Engineering
Overview

This feature‑engineering component transforms the cleaned COPD surveillance data into a state–year‑level feature matrix suitable for modeling.  The raw dataset consists of CDC surveillance estimates for chronic obstructive pulmonary disease (COPD) and related indicators measured across U.S. states and years.  The pipeline loads the data, normalizes units, maps long question names to concise indicator names, constructs a wide pivot table with numerous engineered features, filters out low‑quality or redundant columns, and finally normalizes the feature values.

Key objectives of the feature engineering were to:
	•	Normalize disparate units so that indicators measured as percentages, cases per 100 000, or cases per 1 000 all reside on a comparable scale.
	•	Capture demographic variation by computing sex‑ and race‑specific values as well as differences/ratios between demographic groups.
	•	Encode temporal dynamics through year‑over‑year (YoY) changes for each indicator.
	•	Reflect relationships observed in exploratory analysis by creating interaction features (e.g., smoking vs. prevalence differences) and regression residuals that measure deviation from overall trends.
	•	Reduce multicollinearity through targeted pruning of redundant features (log‑transformed versions, subgroup levels when an overall measure exists, ratio features, and highly correlated residual vs. raw variables).
	•	Standardize features for subsequent modeling by imputing missing values and applying z‑score scaling.

The final engineered dataset has 216 rows (one per state–year) and 28 cleaned, normalized features after pruning and low‑variance filtering.

Data Loading and Preprocessing

The pipeline begins by attempting to load the dataset via a provided get_dataset() function; if unavailable, it reads the CSV file cdc_cleaned_copd.csv.  Only rows with an age‑adjusted value type are retained, and the datavalue column is coerced to numeric.  A unit normalization step scales values based on the reported datavalueunit: percentages are multiplied by 10 to convert to “cases per 1 000”, values reported per 100 000 are multiplied by 0.01, and values already per 1 000 are left unchanged.  In addition, a logarithmic transformation (log1p) of the scaled values is computed to help stabilize heavy‑tailed distributions.  The long question field is mapped to a concise indicator name using INDICATOR_MAP (e.g., “Chronic obstructive pulmonary disease among adults” → COPD_Prevalence).

Feature Construction

Pivot Table and Demographic Features

For each state (locationabbr) and calendar year, the script groups the dataset and constructs a row containing engineered features for each of the six indicators:
	•	Overall estimate (*_overall) and its log (*_log_overall) – mean of datavalue_scaled and datavalue_log for the overall stratification; if missing, the mean across available stratifications is used.
	•	Sex‑specific values (*_Male, *_Female) – mean values for male and female stratifications.  A sex difference (_sex_diff) and sex ratio (_sex_ratio) are computed when both values are present.
	•	Race‑specific values (*_White, *_Black) – mean values for non‑Hispanic White and Black stratifications.  A race difference (_race_diff) and race ratio (_race_ratio) capture disparities.
	•	Year‑over‑year change (*_yoy_change) – difference between the indicator’s overall value in the current year and the previous year for the same state, with the first year’s change set to zero.

Cross‑indicator Interactions

To encode relationships observed in the exploratory data analysis, several cross‑indicator features are computed:
	•	Smoking vs. COPD prevalence – difference and ratio between overall smoking rate and COPD prevalence (Smoking_vs_Prevalence_Diff and Smoking_vs_Prevalence_Ratio).
	•	Mortality (any vs. underlying cause) – difference and ratio between COPD mortality counts when counted as any cause and when counted only as underlying cause (Mortality_Any_vs_Underlying_Diff and Mortality_Any_vs_Underlying_Ratio).
	•	Hospitalization (principal vs. any diagnosis) – difference and ratio between hospitalization rates where COPD is the principal diagnosis and where it appears anywhere on the discharge summary (Hospitalization_Principal_vs_Any_Diff and Hospitalization_Principal_vs_Any_Ratio).

Residual Features

Linear regression is used to compute residual features that represent deviation from global trends.  For each specified pair of indicators, a simple linear model is fitted across all state–year observations, and the residuals (actual minus predicted values) are stored:
	•	Smoking_Mortality_Underlying_Residual – deviation of mortality (underlying cause) from what would be expected given smoking rates.
	•	Smoking_Mortality_Any_Residual – deviation of mortality (any cause) from smoking rates.
	•	Smoking_Prevalence_Residual – deviation of COPD prevalence from smoking rates.
	•	Prevalence_Mortality_Residual – deviation of mortality (underlying cause) from COPD prevalence.

These residuals capture whether a state’s mortality or prevalence is unusually high or low after accounting for smoking prevalence, a relationship highlighted in the EDA scatter plots.

Feature Pruning and Filtering

Because the initial pivot table contains many highly correlated columns, a pruning step removes obvious sources of multicollinearity:
	•	Log versions (*_log_overall) are dropped since they correlate strongly with the corresponding original values.
	•	Subgroup level columns (male, female, White, Black) are removed when a corresponding overall value exists; disparities are captured instead through difference features.
	•	Ratio features (sex and race ratios, interaction ratios) are eliminated to reduce instability; difference features are retained.
	•	Interaction diff columns like Hospitalization_Principal_vs_Any_Diff are removed when the two underlying hospitalization levels are kept because the diff is almost a deterministic transformation.
	•	Raw vs. residual: when KEEP_RESIDUAL_FEATURES is False (option B), raw indicators such as Smoking_Rate_overall, COPD_Prevalence_overall, Mortality_Underlying_overall and Mortality_Any_Cause_overall are retained while residuals are dropped to avoid multicollinearity.  Conversely, when set to True, residuals are kept and raw indicators are pruned.

After pruning redundant columns, the pipeline imputes any remaining missing values with column means (including replacing infinities with NaNs beforehand) and identifies low‑variance or near‑constant features.  Columns with very small variance or rare binary distributions (e.g., nearly all zeros or ones) are dropped.  The filtering criteria include a variance threshold and, for binary features, a mean between 1 % and 99 % to avoid rare categories.

Multicollinearity Diagnostics

With FAST_MODE disabled, the script calculates a Pearson correlation matrix and the Variance Inflation Factor (VIF) for each feature:
	•	The correlation check reports pairs of features with |correlation| ≥ 0.95.  Initially many pairs exceeded this threshold, such as smoking rate vs. smoking–prevalence difference, but after pruning only one such pair remains.
	•	The VIF check measures how much each feature’s variance is inflated by correlations with other features.  Before pruning, the highest VIF values exceeded 60 000 for hospitalization variables; after pruning and residual/ratio removal, the VIF values decrease substantially (e.g., Smoking Rate overall ~ 218, Smoking vs. prevalence difference ~ 188).  Most remaining features have VIF < 10, indicating acceptable collinearity for linear models.

Final Feature Set and Normalization

After pruning and filtering, the feature matrix consists of 28 columns (plus the locationabbr and year identifiers).  The remaining features include:
	•	Overall values for each indicator (COPD_Prevalence_overall, Smoking_Rate_overall, Mortality_Underlying_overall, Mortality_Any_Cause_overall, Hospitalization_Any_Dx_overall, Hospitalization_Principal_Dx_overall) and their YoY changes.
	•	Sex and race difference features (e.g., Mortality_Any_Cause_sex_diff, Mortality_Underlying_race_diff).
	•	Cross‑indicator differences (Smoking_vs_Prevalence_Diff, Mortality_Any_vs_Underlying_Diff).
	•	YoY changes for hospitalization indicators.

Finally, all numeric features are standardized using z‑score normalization via StandardScaler.  The resulting table, normalized_df, retains the state and year columns and appends a suffix _z to each feature name.  The final pivot and normalized tables have shapes (216, 28), indicating 216 state‑year observations and 26 engineered features (excluding identifiers).

Summary

The feature‑engineering pipeline transforms the CDC COPD surveillance data into a comprehensive set of state‑year‑level features.  By normalizing units, encoding demographic differences, constructing interaction and residual features informed by EDA findings, and carefully pruning highly correlated or redundant columns, the process balances richness of information with model‑readiness.  The resulting dataset captures temporal trends, demographic disparities, and relationships between smoking, COPD prevalence, mortality, and hospitalization while controlling multicollinearity—providing a solid foundation for subsequent statistical modeling and inferential analyses.

## Complete Pipeline

To run the entire workflow in sequence (data preview → cleaning → EDA → feature engineering), use the `pipeline.py` module.

### How to use pipeline.py?

The script provides a function:

```python
pipeline(test_acquire_from_URL=False)
```

#### Requirements
- Python version: Python 3.12
- Required packages: All dependencies from `acquire.py`, `dataset_preview.py`, `clean.py`, `EDA.py`, and `features.py`
- Input data: `data/cdc_raw.csv` (will be created on first run with `test_acquire_from_URL=True`)

#### Parameters

| Parameter | Type | Default | Description |
| --------- | ---- | ------- | ----------- |
| test_acquire_from_URL | bool | False | If True, fetch a sample of 100k rows from CDC API using `get_dataset(use_local=False, sample_n=100000)` for testing. If False, skip acquisition and use local data. |

#### Usage Examples

**Option 1: Use local data (recommended for development)**
```python
from pipeline import pipeline
pipeline(test_acquire_from_URL=False)
```

**Option 2: Test with fresh data from CDC API (100k rows)**
```python
from pipeline import pipeline
pipeline(test_acquire_from_URL=True)
```

**Option 3: Run from command line**
```bash
python pipeline.py
```

#### Output

The pipeline executes each step sequentially and prints formatted output separators for clarity:

```
######## Test DATASET_PREVIEW #########
[dataset_preview output...]
#################

######## Test CLEAN #########
[clean output...]
#################

######## Test EDA #########
[EDA output and plot generation...]
#################

######## Test FEATURE_ENGINEERING #########
Feature engineering complete. Pivot shape: (216, 28), Normalized shape: (216, 28)
#################
```

Generated outputs include:
- Cleaned dataset: `data/cdc_cleaned_copd.csv`
- EDA visualizations: `eda_png/P1A.png`, `eda_png/P1B.png`, ..., `eda_png/P4B.png` (12 plots total)
- Feature matrices: `processed/cdc_pivot_features.csv`, `processed/cdc_normalized_features.csv` (if `config.save_csv=True`)

#### Workflow Steps

1. **Data Preview** (optional acquisition): Loads and examines raw data structure, quality issues, and COPD-specific distributions
2. **Data Cleaning**: Filters to COPD records, removes low-quality rows, and retains essential columns
3. **Exploratory Data Analysis**: Generates 12 visualizations exploring distributions, trends, demographics, and relationships
4. **Feature Engineering**: Creates state-year feature matrix with 28 features, handles multicollinearity, and normalizes values

## Conclusion

---


