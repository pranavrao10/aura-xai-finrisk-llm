import joblib
import pandas as pd
import numpy as np

pipeline = joblib.load('models/surrogate_top5_pipeline.joblib')

def predict_single(applicant_dict):
    df = pd.DataFrame([applicant_dict])
    prob = pipeline.predict_proba(df)[0, 1]
    pred = pipeline.predict(df)[0]
    return pred, prob
