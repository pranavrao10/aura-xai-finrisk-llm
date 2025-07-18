# AURA: An Explainable AI Agent for Financial Risk Assessment Using Large Language Models

---

## Overview of Project

AURA is focused on making AI driven credit risk assessments more transparent, explainable, and regulatory compliant. In highly regulated industries like finance, black box models fail to meet trust and compliance standards. AURA bridges this gap by combining advanced machine learning, explainable AI (XAI), and Large Language Models (LLMs) to assess loan default risk with interpretability baked in.

The system predicts the likelihood of loan default and also generates human readable justifications for every decision using SHAP and Retrieval-Augmented Generation (RAG) grounded in real world lending regulations.

---

## Key Features

- **Credit Risk Prediction** using Logistic Regression (Baseline Model) and LightGBM
- **Model Explainability** via SHAP
- **Natural Language Explanations** powered by LLMs via prompt engineering
- **Policy Grounding** through Retrieval-Augmented Generation (RAG)
- **User Interface** built with Streamlit
- **FastAPI Backend & Dockerized Deployment**
- **Evaluation Framework** to measure both accuracy and explainability

---

## How it Works:

1. **Data Collection**: Acquire credit datasets from Lending Club.
2. **EDA/Preprocessing**: Clean, impute, feature engineering, encoding, balance classes.
3. **Modeling**: Train baseline and advanced models.
4. **Explainability**: Add SHAP for per decision transparency.
5. **LLM Integration**: Use Hugging Face Transformers to convert SHAP outputs into readable justifications.
6. **RAG**: Store compliance docs in a vector DB (ChromaDB). Retrieve relevant snippets to contextualize decisions.
7. **Deployment**: Backend with FastAPI, frontend with Streamlit or Gradio, all containerized using Docker.
8. **Evaluation**: Analyze performance + interpretability through metrics and user feedback.

---

## Setup and Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/aura-xai-credit-risk.git
   cd aura-xai-credit-risk
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**

   - **Backend** (FastAPI)
     ```bash
     uvicorn src.api.main:app --reload
     ```
   - **Frontend** (Streamlit or Gradio)
     ```bash
     streamlit run src/ui/app.py
     ```

5. **Optional**: Use Docker
   ```bash
   docker build -t aura-xai .
   docker run -p 8501:8501 aura-xai
   ```

---

## Dataset

- **Primary Dataset**: Lending Club loan data
- **Format**: CSV
- **Source**: [https://www.lendingclub.com/info/download-data.action](https://www.lendingclub.com/info/download-data.action)

### Preprocessing Steps:

- Data Cleaning
- Missing value imputation
- Feature Engineering
- Feature standardization
- Encoding
- Train/Test Split (80:20)

---

## Performance

> _To be updated after model training and evaluation_

| Model         | PR_AUC | Precision | Recall | F1 Score | ROC-AUC | Accuracy |
| ------------- | -------- | --------- | ------ | -------- | ------- | ------ |
| Logistic Reg. | `0.90`   | `0.69`    | `0.90` | `0.78`   | `0.95`  | `0.84` |
| LightGBM      | `0.294`  | `0.243`   | `0.702`| `0.361`  | `0.703` | `0.609`|
| Surrogate LR  | `0.90`   | `0.69`    | `0.89` | `0.78`   | `0.95`  | `0.84` |

### Explainability Evaluation:

- User rating (1–5 clarity scale): `__`
- Alignment with domain knowledge: `__`

---

## Insights

> _To be completed during Results & Discussion phase_

- Most important features influencing loan default
- Comparison between black-box vs. explainable models
- Quality and clarity of SHAP explanations
- Usefulness of LLM + RAG in legal justification generation
- Feedback from mock users and potential compliance stakeholders

---

## Contributors

• Pranav Rao (@pranavrao10)

---
