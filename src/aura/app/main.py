from __future__ import annotations
import os, json, argparse, sys
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from aura.app.config import ui_features, user_friendly, decision_threshold, validate_one, validate_ui_payload, InputError, near_threshold_band
from aura.models.predict import predict_with_explanations, save_prediction_log
from aura.explain.explainer import generate_explanation

console = Console()
quit_hint_printed = False  

def show_quit_hint_once():
    global quit_hint_printed
    if quit_hint_printed:
        return
    console.print(
        Panel.fit(
            "[dim]Tip: Type 'quit' or 'exit' anytime to abort.[/dim]",
            border_style="grey35"
        )
    )
    quit_hint_printed = True

defaults = {
    "grade": "B",
    "term": 36,
    "acc_open_past_24mths": 5,
    "dti": 15.0,
    "fico_mid": 700
}

def prompt_input(feature: str):
    show_quit_hint_once()
    label = user_friendly.get(feature, feature)
    prompt = f"{label}: "
    while True:
        try:
            raw = input(prompt).strip()
        except KeyboardInterrupt:
            rprint("\n[red]Interrupted (Ctrl+C). Exiting…[/red]")
            sys.exit(130)
        except EOFError:
            rprint("\n[red]EOF received (Ctrl+D). Exiting…[/red]")
            sys.exit(131)
        except Exception as e:
            rprint(f"[red]‣ {e}. Please enter a valid value.")
            continue
        if raw.lower() in {"quit", "exit"}:
            rprint("[yellow]Exiting. Goodbye![/yellow]")
            sys.exit(0)
        if raw == "":
            rprint("[yellow]Blank not accepted. Enter a value.[/yellow]")
            continue
        try:
            return validate_one(feature, raw)
        except InputError as e:
            rprint(f"[red]Invalid value ({e}). Please re-enter.")


def collect_applicant():
    rprint("[bold cyan]--- Enter Applicant Information ---")
    payload = {f: prompt_input(f) for f in ui_features}
    return validate_ui_payload(payload, require_all=True)

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