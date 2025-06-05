# Lending Club – Preprocessed Data Manifest

_All data in this folder was generated on {pd.Timestamp.utcnow().date()}._

## 1. Raw Input  
`accepted_2007_to_2018Q4.csv` — full **accepted loans 2007–2018Q4** CSV from Kaggle.

## 2. Target Definition  
* **loan_status → default**  
  * 1 = “Charged Off”  
  * 0 = “Fully Paid”  
* All other statuses were **dropped**.

## 3. Column Filtering  
* **Identifiers & URLs**: `id`, `member_id`, `url`, `policy_code` → _dropped_  
* **Free-text / high-cardinality**: `emp_title`, `title`, `desc` → _dropped_  
* **Post-issuance leakage** (payments, recoveries, balances, hardship flags) → _dropped_  
* **Constant columns** (`nunique()==1`) → _dropped_  
* **High-missing** (> 30% NaN) → _dropped_  
* Final shape after drops: **(1345310, 116)**.

## 4. Feature Engineering  
| Derived Feature | Formula | Notes |
|-----------------|---------|-------|
| `loan_to_income` | `loan_amnt / (annual_inc+1)` | ratio |
| `installment_to_income` | `installment / (annual_inc+1)` | ratio |
| `credit_age_months` | months between `issue_d` and `earliest_cr_line` | borrower history |
| `term_months` / `long_term` | extracted from text “36 months” / `(term==60)` | duration flag |
| Log-transform | `loan_amnt`, `annual_inc` → `log1p()` | reduce skew |

## 5. Missing-Value Strategy  
* **Numeric** → `median` imputation  
* **Ordinal** (`grade`, `sub_grade`, `emp_length`) → sentinel **–1** via `OrdinalEncoder`  
* **Nominal** → `most_frequent` (then rare-lump)  
* Missing-indicator flags added for every column that contained NaNs.

## 6. Encoding  
* **OrdinalEncoder** with explicit category order  
* **OneHotEncoder** with `min_frequency=200` (rare values lumped into “other”)  
* Output kept **sparse CSR**.

## 7. Scaling  
* `StandardScaler(with_mean=False)` applied to numeric features (safe for CSR).

## 8. Variance Filter  
* `VarianceThreshold(0.0)` removed zero-variance columns created after train/test split.

## 9. Train/Test Split  
* Stratified 80 / 20 on `default`  
* Shapes: `Xt_train` (1076248, 134)   `Xt_test` (269062, 134)

## 10. Class Imbalance  
* Ratio ≈ 4.01 : 1    
  * Handled with **`class_weight="balanced"`** for linear & tree models.

## 11. Saved Artefacts  
| File | Description |
|------|-------------|
| `X_train.npz` | CSR matrix – encoded train features |
| `X_test.npz`  | CSR matrix – encoded test features |
| `y_train.csv` | Train labels |
| `y_test.csv`  | Test labels |
| `preprocessor.joblib` | Fitted impute/scale/encode pipeline |
| `vt.joblib` | Fitted variance-threshold mask |

---
