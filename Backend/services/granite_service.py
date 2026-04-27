"""
Service layer for IBM Granite natural-language explanation generation.
Uses Ollama to run Granite locally for generating user-friendly diagnostics.
"""

from collections.abc import Iterable
from fastapi import HTTPException
from sqlalchemy.orm import Session
from config import GRANITE_MODEL
from models.upload import FileWarning
from routes.diagnostics_routes import run_diagnostics
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

def generate_explanation_for_warning(warning_id: int, query: str, db: Session) -> Iterable[str]:
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
        response = ollama.generate(GRANITE_MODEL, prompt, stream=True)
        for chunk in response:
            yield chunk.response
    except ImportError:
        print("Granite model unavailable (Ollama not installed). Ignoring.")
        pass
    except Exception as e:
        print(f"Error generating Granite explanation: {e}")
        pass


def generate_explanation(filename: str, alert_index: int | None = None) -> dict:
    """
    Generate a natural-language explanation of diagnostics using IBM Granite.
    Falls back to a formatted summary if Granite/Ollama is unavailable.
    """
    filename = validate_filename(filename)
    diagnostics = run_diagnostics(filename)
    warnings = diagnostics.get("warnings", [])

    if not warnings:
        return {
            "filename": filename,
            "explanation": "No issues were found in your vehicle data. Everything looks normal.",
            "source": "system",
            "alert_index": alert_index,
        }

    prompt = _build_prompt(warnings, filename, alert_index)

    # Try Granite via Ollama
    try:
        from ollama import generate as ollama_generate
        response = ollama_generate(GRANITE_MODEL, prompt)
        explanation = response.get("response", "").strip()

        if explanation:
            return {
                "filename": filename,
                "explanation": explanation,
                "source": "granite",
                "alert_index": alert_index,
                "total_warnings": len(warnings),
            }
    except ImportError:
        pass
    except Exception:
        pass

    # Fallback
    explanation = _fallback_explanation(warnings, alert_index)
    return {
        "filename": filename,
        "explanation": explanation,
        "source": "fallback",
        "alert_index": alert_index,
        "total_warnings": len(warnings),
        "note": "Granite model unavailable – showing template-based explanation.",
    }


def _fallback_explanation(warnings: list[dict], alert_index: int | None = None) -> str:
    """Generate a readable explanation without the LLM."""
    if alert_index is not None:
        w = warnings[alert_index]
        severity = w.get("severity", "unknown")
        message = w.get("message", "An issue was detected.")
        urgency = "You should address this soon." if severity in ("high", "critical") else "This is not urgent but worth monitoring."
        return f"{message} {urgency}"

    critical = [w for w in warnings if w.get("severity") == "critical"]
    high = [w for w in warnings if w.get("severity") == "high"]
    medium = [w for w in warnings if w.get("severity") == "medium"]
    low = [w for w in warnings if w.get("severity") == "low"]

    parts = [f"Your vehicle scan found {len(warnings)} issue(s)."]

    if critical:
        parts.append(f"{len(critical)} critical issue(s) need immediate attention:")
        for w in critical[:3]:
            parts.append(f"  - {w.get('message', 'Unknown')}")

    if high:
        parts.append(f"{len(high)} high-severity issue(s) found:")
        for w in high[:3]:
            parts.append(f"  - {w.get('message', 'Unknown')}")

    if medium:
        parts.append(f"{len(medium)} medium-severity issue(s) worth monitoring.")

    if low:
        parts.append(f"{len(low)} low-severity item(s) noted.")

    if critical or high:
        parts.append("It is recommended you have your vehicle inspected by a professional.")

    return "\n".join(parts)
