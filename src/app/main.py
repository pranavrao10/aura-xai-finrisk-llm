from __future__ import annotations
import os, json, argparse, sys
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from src.app.config import ui_features, user_friendly, decision_threshold, near_threshold_band
from src.models.predict import predict_with_explanations, save_prediction_log
from src.explain.explainer import generate_explanation

console = Console()

valid_grades = set("ABCDEFG")
valid_terms  = {36, 60}          
fico_min, fico_max = 300, 850

defaults = {
    "grade": "B",
    "term": 36,
    "acc_open_past_24mths": 5,
    "dti": 15.0,
    "fico_mid": 700
}

def coerce(feature: str, raw: str):
    if feature == "grade":
        g = raw.upper()
        if g not in valid_grades:
            raise ValueError(f"Grade must be a letter between A-G. Got '{g}'")
        return g
    if feature == "term":
        try:
            n = int(str(raw).strip().split()[0])
        except Exception:
            raise ValueError(f"Term must be 36 or 60. Got '{raw}'")
        if n not in valid_terms:
            raise ValueError(f"Term must be 36 or 60. Got '{raw}'")
        return n
    if feature == "acc_open_past_24mths":
        try:
            n = int(raw)
        except Exception:
            raise ValueError(f"Cannot be negative or non-integer. Got '{raw}'")
        if n < 0:
            raise ValueError(f"Cannot be negative or non-integer. Got '{raw}'")
        return n
    if feature == "dti":
        try:
            d = float(raw)
        except Exception:
            raise ValueError(f"DTI must be numeric and cannot be negative (ex: 15 or 15.2). Got '{raw}'")
        if d < 0:
            raise ValueError(f"DTI must be numeric and cannot be negative (ex: 15 or 15.2). Got '{raw}'")
        if d is not float(d):
            raise ValueError(f"DTI must be numeric and cannot be negative (ex: 15 or 15.2). Got '{raw}'")
        return d
    if feature == "fico_mid":
        try:
            f = int(raw)
        except Exception:
            raise ValueError(f"FICO must be between 300 and 850. Got '{raw}'")
        if not (fico_min <= f <= fico_max):
            raise ValueError(f"FICO must be between 300 and 850. Got '{raw}'")
        return f

    raise ValueError("Unknown feature")

def prompt_input(feature: str):
    label = user_friendly.get(feature, feature)
    coerce_ = coerce
    default = defaults[feature]
    while True:
        try:
            raw = input(f"{label}: ").strip()
        except Exception as e:
            rprint(f"[red]‣ {e}. Please enter a valid value.")
        if raw == "":
            rprint("[yellow]Blank not accepted. Enter a value.")
            continue
        try:
            val = coerce(feature, raw)
            return val
        except Exception as e:
            rprint(f"[red]Invalid value ({e}). Please re-enter.")


def collect_applicant():
    rprint("[bold cyan]--- Enter Applicant Information ---")
    payload = {}
    for f in ui_features:
        payload[f] = prompt_input(f)
    return payload

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=str, help="JSON payload for applicant")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM explanation")
    args = parser.parse_args()

    if args.json:
        try:
            applicant = json.loads(args.json)
        except Exception as e:
            rprint(f"[red]Invalid JSON supplied ({e}). Exiting.")
            sys.exit(1)
    else:
        applicant = collect_applicant()

    try:
        pred_bundle = predict_with_explanations(applicant, max_reasons=5)
    except Exception as e:
        rprint(f"[red]Prediction failed: {e}")
        sys.exit(2)

    save_prediction_log(pred_bundle)

    risk_color = "red" if pred_bundle["risk_class"] == "High" else "green"
    near_flag = abs(pred_bundle["threshold_delta"]) <= near_threshold_band
    header = f"[bold {risk_color}]Risk Assessment[/bold {risk_color}]"
    details = (
        f"Probability of Default: {pred_bundle['prob_default']:.2%}\n"
        f"Decision Threshold: {pred_bundle['threshold']:.2%} (policy={pred_bundle['threshold_policy']})\n"
        f"Above Threshold By: {pred_bundle['threshold_delta']:.2%}\n"
        f"Near Threshold: {near_flag}"
    )
    console.print(Panel(details, title=header, border_style=risk_color))

    if args.no_llm:
        rprint("[yellow]LLM explanation skipped (--no-llm).")
        return

    explanation = generate_explanation(pred_bundle)
    rprint("\n[bold cyan]Explanation[/bold cyan]")
    rprint(explanation["narrative"])

if __name__ == "__main__":
    main()