# Lending Club — Data Preprocessing Pipeline

_Generated **2025-07-11**_

---

## 1  Raw Input
**accepted_2007_to_2018Q4.csv** — original Lending Club “accepted loans” CSV (2007–2018 Q4).

---

## 2  Target Definition
| Label | Mapped `loan_status` values |
|-------|-----------------------------|
| **1** | Charged Off, Default, Late (16–30 d), Late (31–120 d), In Grace Period, Does-Not-Meet-Policy Charged Off |
| **0** | Fully Paid, Does-Not-Meet-Policy Fully Paid |

Other statuses were **dropped**.  
Default rate (train split): **20.4%**  
Class imbalance ≈ **3.89:1** (non-default : default)

---

## 3  Column Filtering (Leakage, PII)
* **Exact drops:** `loan_status`, `pymnt_plan`, `member_id`, `id`, `url`, `addr_state`, `zip_code`, `emp_title`, `title`, `desc`
* **Prefix drops:** any column that starts with  
  `last_`, `out_prncp`, `total_rec_`, `total_pymnt`, `recoveries`,  
  `collection_recovery_fee`, `funded_amnt_inv`, `hardship_`,  
  `debt_settlement_`, `settlement_`
* **Constant columns** (`nunique()==1`) removed.
* **High-missing flag rule:** if `train` NaN rate ≥ **5%**, create `<col>_missing` indicator ( dtype int8 ).

_Post-filter dataframe shape:_ **(1382351, 187)**

---

## 4  Temporal Split (`issue_d`)
| Split | Date window               | Rows |
|-------|---------------------------|------|
| Train | ≤ 2016-12-31              | 1,132,562 |
| Val   | 2017-01-01 → 2017-12-31   | 181,728 |
| Test  | ≥ 2018-01-01              | 68,061 |

No random shuffling — ensures forward-looking evaluation.

---

## 5  Pre-processing Steps
### 5.1  Type casting & basic transforms
* **Percent to float**: `int_rate`, `revol_util` → divide by 100.  
* **Log1p**: `loan_amnt`, `annual_inc`, `revol_bal` to reduce skew.

### 5.2  Missing-value handling
* **Numeric** (`168` cols) → median of *train* split.  
* **Categorical** (`15` cols)  
  * NaNs → `"Missing"` level (added if absent).  
  * **Rare bucketing:** any level with < max(10, 0.1 %) occurrences in *train* → `"Other"`.

### 5.3  Feature Engineering
| Feature | Formula | Notes |
|---------|---------|-------|
| `credit_age_months` | `(issue_d – earliest_cr_line)//30` | Age of credit file |
| `loan_to_income` | `loan_amnt / (annual_inc+1)` | Ratio |
| `installment_to_income` | `installment / (annual_inc+1)` | Ratio |
| `fico_mid`, `fico_spread` | Midpoint & range of approval-time FICO | |
| `rev_util_ratio` | `revol_bal / (total_rev_hi_lim+1)` | |
| `dti_inv` | `1 / (dti+1e-3)` | Stabilised inverse |
| `inq_ratio` | `inq_last_12m / (open_acc+1)` | Hard-pull density |
| `int_minus_subgrade_mean` | `int_rate – mean(int_rate) within sub_grade` (calc **on train only**) | Removes grade-level bias |
| `grade_term` | concat(`grade`, `term`) | Categorical cross |
| `purpose_emp_len` | concat(`purpose`, `emp_length`) | High-card cat |
| `fico_mid_sq`, `log_loan_sq` | Squared versions for non-linearity |

Total feature count after engineering: **186**

---

## 6  Encoding & Data Types
* All categoricals kept as native **pandas `category`** → consumed directly by LightGBM.  
* No one-hot nor target-encoding currently applied (reserved for later versions).  

---

## 7  Saved Artefacts
| File | Purpose |
|------|---------|
| `lc_cleaned.parquet` | Full cleaned dataset (train + val + test) |
| `X_train.pkl`, `X_val.pkl`, `X_test.pkl` | Feature DataFrames |
| `y_train.csv`, `y_val.csv`, `y_test.csv` | Target vectors |
| `feature_schema.json` | Lists numeric / categorical columns |
| `README.md` | This manifest |

---

## 8  Reproducibility Guarantees
* **Leakage-proof**: all post-issuance columns removed _before_ split.  
* **Train-only statistics** for imputation & mean-subtractions.  
* **Monotonic date split** prevents future information bleed.  
* Every artefact versioned under `../data/processed/`. 