import joblib
import numpy as np
import pandas as pd
import os

preprocessor_path = os.getenv('preprocessor_path',
                              'data/processed/preprocessor.joblib')
vt_path = os.getenv('vt_path', 'data/processed/vt.joblib')


def load_preprocessor():
    return joblib.load(preprocessor_path)

def load_vt():
    return joblib.load(vt_path)

def preprocess_input(data_df):
    preprocessor = load_preprocessor()
    vt = load_vt()
    processed = preprocessor.transform(data_df)
    processed = vt.transform(processed)
    return processed

