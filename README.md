# AURA: An Explainable AI Agent for Financial Risk Assessment Using Large Language Models

---

## Overview of Project

AURA is focused on making AI driven credit risk assessments more transparent, explainable, and regulatory compliant. In highly regulated industries like finance, black box models fail to meet trust and compliance standards. AURA bridges this gap by combining advanced machine learning, explainable AI (XAI), and Large Language Models (LLMs) to assess loan default risk with interpretability baked in.

The system predicts the likelihood of loan default and also generates human readable justifications for every decision using SHAP/LIME and Retrieval-Augmented Generation (RAG) grounded in real world lending regulations.

---

## Key Features

- **Credit Risk Prediction** using Logistic Regression, XGBoost, or Neural Networks
- **Model Explainability** via SHAP and LIME
- **Natural Language Explanations** powered by fine tuned LLMs
- **Policy Grounding** through Retrieval-Augmented Generation (RAG)
- **User Interface** built with Streamlit or Gradio
- **FastAPI Backend & Dockerized Deployment**
- **Evaluation Framework** to measure both accuracy and explainability

---

### How it Works:

1. **Data Collection**: Acquire credit datasets from Lending Club.
2. **Preprocessing**: Clean, impute, balance classes (SMOTE).
3. **EDA**: Visualize distributions, correlation matrices, and engineer new features.
4. **Modeling**: Train baseline and advanced models.
5. **Explainability**: Add SHAP/LIME for per decision transparency.
6. **LLM Integration**: Use Hugging Face Transformers to convert SHAP outputs into readable justifications.
7. **RAG**: Store compliance docs in a vector DB (ChromaDB). Retrieve relevant snippets to contextualize decisions.
8. **Deployment**: Backend with FastAPI, frontend with Streamlit or Gradio, all containerized using Docker.
9. **Evaluation**: Analyze performance + interpretability through metrics and user feedback.

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

- Missing value imputation
- Feature standardization
- Handling class imbalance using SMOTE or class weights
- Feature selection via correlation thresholds

---

## Performance

> _To be updated after model training and evaluation_

| Model         | Accuracy | Precision | Recall | F1 Score | ROC-AUC |
| ------------- | -------- | --------- | ------ | -------- | ------- |
| Logistic Reg. | `__`     | `__`      | `__`   | `__`     | `__`    |
| XGBoost       | `__`     | `__`      | `__`   | `__`     | `__`    |
| LightGBM      | `__`     | `__`      | `__`   | `__`     | `__`    |
| Final Model   | `__`     | `__`      | `__`   | `__`     | `__`    |

### Explainability Evaluation:

- User rating (1–5 clarity scale): `__`
- Alignment with domain knowledge: `__`

---

## Insights

> _To be completed during Results & Discussion phase_

- Most important features influencing loan default
- Comparison between black-box vs. explainable models
- Quality and clarity of SHAP/LIME explanations
- Usefulness of LLM + RAG in legal justification generation
- Feedback from mock users and potential compliance stakeholders

---

## Contributors

• Pranav Rao (@pranavrao10)

---
