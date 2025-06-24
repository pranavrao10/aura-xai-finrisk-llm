import openai
import os
from src.app.config import user_friendly


client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_response(applicant_dict, pred, prob):
    lines = []
    for k, v in applicant_dict.items():
        label = user_friendly.get(k, k)
        lines.append(f"{label}: {v}")
    features_txt = "\n".join(lines)
    approval_str = "Low Risk of Default" if pred == 0 else "High Risk of Default"
    prompt = f"""
    You are an AI assistant for banks and credit unions, acting as a highly
    experienced credit/loan officer helping explain credit decisions to bank
    employees in clear language.
    You are designed to provide clear, concise explanations for loan default risk
    and related regulations that affect credit decisons.
    You have access to a database of documents that contain information about loan
    default risk and related regulations, such as the Equal Credit Opportunity Act (ECOA) and Fair Housing Act (FHA).
    You can answer questions about loan default risk.
    You can cite regulations by section number.
    You should not include any information that is not relevant to the question
    asked unless otherwise specified.
    You only use information from the provided features, models, and SHAP analysis
    to generate your response.

    Here are the loan application features:
    {features_txt}

    Prediction: approval_str
    Estimated Probability of Default: {prob:.2f}

    Write a clear, polite explanation to the applicant describing why the 
    application has a {approval_str.lower()}, referencing the most important factors.
    """
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.3,
    )
    return response.choices[0].message.content