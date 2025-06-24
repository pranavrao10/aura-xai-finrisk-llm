import os

feature_names = [
    "last_fico_range_high",
    "last_fico_range_low",
    "term",
    "debt_settlement_flag",
    "emp_length_na"
]

user_friendly = {
    "last_fico_range_high": "Highest Recent FICO Score",
    "last_fico_range_low": "Lowest Recent FICO Score",
    "term": "Loan Term (36 or 60 months)",
    "debt_settlement_flag": "Debt Settlement Flag (Y/N)",
    "emp_length_na": "Employment Length Not Provided (1 = missing, 0 = present)"
}