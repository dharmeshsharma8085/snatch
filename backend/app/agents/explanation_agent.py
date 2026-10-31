
from openai import AsyncOpenAI

from app.core.config import settings
from app.graph.state import SnatchState


async def openai_explanation_agent(
    state: SnatchState
) -> dict:

    assessment = state["risk_assessment"]

    trace = state.get("agent_trace", [])
    trace.append("OpenAI Explanation Agent")

    fallback = (
        f"SNATCH calculated a risk score of "
        f"{assessment['score']}/100. "
        f"Risk level: {assessment['level']}. "
        f"Detected signals: "
        f"{', '.join(assessment['signals']) or 'none'}. "
        f"Recommended action: "
        f"{assessment['recommended_action']}."
    )

    # Continue working without OpenAI if not configured
    if not settings.openai_api_key or not settings.openai_model:
        return {
            "explanation": fallback,
            "openai_used": False,
            "agent_trace": trace
        }

    try:
        client = AsyncOpenAI(
            api_key=settings.openai_api_key
        )

        prompt = f"""
You are the explanation component of SNATCH,
a smartphone protection platform.

Explain the following deterministic risk assessment
in simple language.

Assessment:
{assessment}

Rules:
1. Never claim theft is confirmed.
2. Never invent device events.
3. Do not change the risk score.
4. Explain the detected signals.
5. Explain the recommended action.
6. Be concise and factual.
"""

        response = await client.responses.create(
            model=settings.openai_model,
            input=prompt
        )

        explanation = response.output_text or fallback

        return {
            "explanation": explanation,
            "openai_used": True,
            "agent_trace": trace
        }

    except Exception:
        # LLM failure must not stop the security workflow
        return {
            "explanation": fallback,
            "openai_used": False,
            "agent_trace": trace,
            "errors": [
                "OpenAI unavailable; deterministic fallback used."
            ]
        }
