from typing import Dict, Optional
from openai import OpenAI
from config import settings


def _build_prompt(profile: Dict, goals_text: Optional[str], planning_days: int) -> str:
    name = profile.get("name", "user")
    role = profile.get("role", "")
    hours_per_week = profile.get("hours_per_week")
    hours_per_day = profile.get("hours_per_day")

    availability_str = []
    if hours_per_day:
        availability_str.append(f"~{hours_per_day}h/day")
    if hours_per_week:
        availability_str.append(f"~{hours_per_week}h/week")
    availability = ", ".join(availability_str) if availability_str else "unspecified availability"

    goals_section = goals_text.strip() if goals_text else "Not provided."

    return (
        "You are a concise planning assistant. Produce a compact day-by-day plan "
        "for the next {days} days, prioritized, time-bounded, and feasible.\n"
        "User: {name} ({role}). Availability: {availability}.\n"
        "Goals/inputs: {goals}\n\n"
        "Output format (keep it short):\n"
        "- Priorities: 3-5 bullets (highest to lowest)\n"
        "- Plan: For each day D1..D{days}, 2-5 bullet items with estimated minutes\n"
        "- Notes: 1-2 bullets for risks or dependencies\n"
        "Avoid fluff. Use actionable verbs.\n"
    ).format(days=planning_days, name=name, role=role, availability=availability, goals=goals_section)


def generate_plan(profile: Dict, goals_text: Optional[str]) -> str:
    client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)

    prompt = _build_prompt(profile, goals_text, settings.planning_days)

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": "You are a helpful planning assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
        max_tokens=800,
    )

    content = response.choices[0].message.content if response.choices else ""
    return content.strip() or "(No plan generated)"
