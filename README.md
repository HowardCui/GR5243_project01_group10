# GU5243 Project01
### Collaborators：Haowen Cui(@HowardCui), Yuhan Guo(@FlamyFlame)
## Project Introduction
(project intro ....)

## Data Acquisition
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
So it mainly checks sample size, variable types, missing value distribution across variables, and potential type inconsistencies

### How to use dataset_preview.py?
The script provides functions:  

init_data_check(dataset)  

check_COPD(dataset) 


#### Parameters
| Parameter | Type             | Description                               |
| --------- | ---------------- | ----------------------------------------- |
| dataset   | pandas.DataFrame | The raw dataset obtained from the CDC API |

## Data Pre-preprocessing 
(...)
## Conclusion

---
