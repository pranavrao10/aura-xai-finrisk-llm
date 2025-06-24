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
    print("\n--- Enter Applicant Info ---")
    vals = {}
    for feat in feature_names:
        label = user_friendly.get(feat, feat)
        val = input(f"{label}: ")
        if val == "":
            val = defaults[feat]
        # Type conversions:
        if feat in ["last_fico_range_high", "last_fico_range_low", "emp_length_na"]:
            val = int(val)
        elif feat == "term":
            # Accept either '36' or '60' or the full string
            if val.strip() in ["36", " 36 months"]:
                val = " 36 months"
            elif val.strip() in ["60", " 60 months"]:
                val = " 60 months"
            else:
                print("Invalid value for term. Defaulting to 36 months.")
                val = " 36 months"
        elif feat == "debt_settlement_flag":
            val = val.strip().upper()
            if val not in ["Y", "N"]:
                print("Invalid value for debt settlement flag. Defaulting to 'N'.")
                val = "N"
        vals[feat] = val
    return vals

if __name__ == "__main__":
    applicant = get_user_input()
    pred, prob = predict_single(applicant)
    print(f"Model prediction: {'Low Risk of Default' if pred == 0 else 'High Risk of Default'} (Probability of default: {prob:.2%})")
    explanation = generate_response(applicant, pred, prob)
    print("\n--- Reasoning ---")
    print(explanation)