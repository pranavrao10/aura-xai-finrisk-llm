import pandas as pd
import os
import openai
from src.app.config import feature_names, user_friendly
from src.models.predict import predict_single
from src.explain.explainer import generate_response
openai.api_key = os.getenv("OPENAI_API_KEY")

defaults = {
    "last_fico_range_high": 700,
    "last_fico_range_low": 695,
    "term": " 36 months",              
    "debt_settlement_flag": "N",        
    "emp_length_na": 0                  
}



def get_user_input():
    print("\n---Enter Applicant Information---")
    vals = {}
    max_tries = 3
    for feat in feature_names:
        label = user_friendly.get(feat, feat)
        tries = 0

        while True:
            val = input(f"{label}: ")
            val = val.strip()
            if val == "":
                val = defaults[feat]
                break
            # Type conversions:
            if feat in ["last_fico_range_high", "last_fico_range_low"]:
                try:
                    val_int = int(val)
                    if 300 <= val_int <= 850:
                        vals[feat] = val_int
                        break
                    else:
                        raise ValueError
                except ValueError:
                    tries += 1
                    print("Please enter a valid FICO score (integer between 300 and 850).")
            elif feat == "emp_length_na":
                try:
                    val_int = int(val)
                    if val_int in [0, 1]:
                        vals[feat] = val_int
                        break
                    else:
                        raise ValueError
                except ValueError:
                    tries += 1
                    print("Please enter 0 or 1 (0 = Employment Length Present, 1 = Missing).")
            elif feat == "term":
                if val in ["36", " 36 months", "36 months"]:
                    vals[feat] = " 36 months"
                    break
                elif val in ["60", " 60 months", "60 months"]:
                    vals[feat] = " 60 months"
                    break
                else:
                    tries += 1
                    print("Please enter '36' or '60' (months).")
            elif feat == "debt_settlement_flag":
                if val.upper() in ["Y", "N"]:
                    vals[feat] = val.upper()
                    break
                else:
                    tries += 1
                    print("Please enter 'Y' or 'N'.")
            if tries >= max_tries:
                print(f"Too many invalid attempts. Using default: {defaults}")
                vals[feat] = defaults
                break
    return vals

default_risk_threshold = 0.25

if __name__ == "__main__":
    applicant = get_user_input()
    pred, prob = predict_single(applicant)
    high_risk = prob >= default_risk_threshold
    print(
        f"Model prediction: {'High Risk of Default' if high_risk else 'Low Risk of Default'} "
        f"(Probability of default: {prob:.2%})"
    )
    explanation = generate_response(applicant, int(high_risk), prob)
    print("\n--- Reasoning ---")
    print(explanation)