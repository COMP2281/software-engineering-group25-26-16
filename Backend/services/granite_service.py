"""
Service layer for IBM Granite natural-language explanation generation.
Uses Ollama to run Granite locally for generating user-friendly diagnostics.
"""

from collections.abc import Iterable
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.upload import FileWarning
from routes.diagnostics_routes import run_diagnostics
from services.settings_services import get_model
from services.validators import validate_filename
import ollama

def _build_prompt(warnings: list[dict], filename: str, alert_index: int | None = None) -> str:
    """Build a prompt for Granite based on diagnostic warnings."""
    if alert_index is not None:
        if alert_index < 0 or alert_index >= len(warnings):
            raise HTTPException(
                status_code=400,
                detail=f"Alert index {alert_index} out of range (0-{len(warnings) - 1})."
            )
        w = warnings[alert_index]
        prompt = (
            f"You are a friendly car maintenance advisor. A vehicle diagnostic scan found the "
            f"following issue:\n\n"
            f"- Type: {w.get('type', 'Unknown')}\n"
            f"- Severity: {w.get('severity', 'unknown')}\n"
            f"- Details: {w.get('message', 'No details')}\n"
            f"- Engine run time at detection: {w.get('run_time', 'N/A')}\n\n"
            f"Explain this issue in plain language for someone who knows nothing about cars. "
            f"Include: what the problem is, how serious it is, what the driver should do about it, "
            f"and whether it is safe to keep driving. Keep the response concise (3-5 sentences). "
            f"Do NOT use technical jargon."
        )
    else:
        warning_lines = []
        for i, w in enumerate(warnings[:20]):
            warning_lines.append(
                f"{i+1}. [{w.get('severity', '?').upper()}] {w.get('message', 'Unknown issue')}"
            )
        warning_text = "\n".join(warning_lines)

        prompt = (
            f"You are a friendly car maintenance advisor. A vehicle diagnostic scan of the file "
            f"'{filename}' found {len(warnings)} issue(s):\n\n"
            f"{warning_text}\n\n"
            f"Provide a brief overall summary for someone who knows nothing about cars. "
            f"Explain the most important issues first, whether the car is safe to drive, "
            f"and what actions the driver should take. Keep it concise and avoid jargon. "
            f"If there are many similar warnings, group them together."
        )

    return prompt

def pull_model(model_name: str):
    try:
        ollama.pull(model_name)
        print(f"Finished pulling Granite model ({model_name}).")
    except:
        print("Failed to pull Granite model (perhaps model does not exist?).")
        print("AI chatbot features will not work!")

def generate_explanation_for_warning(warning_id: int, query: str, db: Session = Depends(get_db)) -> Iterable[str]:
    # Get warning
    warning = db.query(FileWarning).filter(FileWarning.id == warning_id).first()

    if warning is None:
        raise HTTPException(status_code=404, detail="Warning not found")

    # Build prompt
    prompt = (
        f"You are a friendly car maintenance advisor. A vehicle diagnostic scan found the "
        f"following issue:\n\n"
        f"- Type: {warning.warning_type}\n"
        f"- Severity: {warning.severity}\n"
        f"- Details: {warning.message}\n"
        f"- Engine run time at detection: {warning.run_time}\n\n"
        f"Explain this issue in plain language for someone who knows nothing about cars. "
        f"Include: what the problem is, how serious it is, what the driver should do about it, "
        f"and whether it is safe to keep driving. Keep the response concise (3-5 sentences). "
        f"Do NOT use technical jargon."
        ) + f"\n\nUser query: {query}"

    # Try Granite via Ollama
    try:
        response = ollama.generate(get_model(db), prompt, stream=True)
        for chunk in response:
            yield chunk.response
    except ImportError:
        print("Granite model unavailable (Ollama not installed). Ignoring.")
        pass
    except Exception as e:
        print(f"Error generating Granite explanation: {e}")
        pass
