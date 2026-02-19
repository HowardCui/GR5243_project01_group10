# GU5243 Project01
### Collaborators：Haowen Cui(@HowardCui), Yuhan Guo(@FlamyFlame), Selina Peng(@Skyerrrrrrr)
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
Before performing any preprocessing or formal exploratory analysis, we conducted an initial structural and quality assessment of the raw dataset. This step aims to evaluate data complexity.
So it mainly checks sample size, variable types, missing value distribution across variables, and potential type inconsistencies.

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

## Data Pre-preprocessing 

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
(...)

## Feature Engineering
(...)

## Conclusion

---


