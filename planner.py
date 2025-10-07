from typing import Dict, Optional, List
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


def _fallback_plan(profile: Dict, goals_text: Optional[str]) -> str:
    """Generate a very simple heuristic plan if LLM is unavailable.

    Splits goals by commas/semicolons/newlines and round-robins them across days
    based on hours_per_day or hours_per_week.
    """
    days = max(1, settings.planning_days)
    hours_per_day = profile.get("hours_per_day")
    hours_per_week = profile.get("hours_per_week")

    if not hours_per_day and hours_per_week:
        hours_per_day = round(float(hours_per_week) / days, 2)
    if not hours_per_day:
        hours_per_day = 1.0  # default minimal effort

    raw = (goals_text or "").strip()
    if not raw:
        raw = "general review, make progress on main project, study/practice"

    import re
    chunks: List[str] = [s.strip() for s in re.split(r"[\n;,]", raw) if s.strip()]
    if not chunks:
        chunks = ["general review", "make progress", "study/practice"]

    # Priorities = first few chunks
    priorities = chunks[: min(5, len(chunks))]

    # Distribute items across days (2-4 bullets/day depending on list length)
    items_per_day = max(2, min(4, len(chunks)))
    plan_lines: List[str] = []
    idx = 0
    est_minutes = int(float(hours_per_day) * 60)
    per_item = max(20, est_minutes // items_per_day if items_per_day else est_minutes)

    for d in range(1, days + 1):
        day_items = []
        for _ in range(items_per_day):
            goal = chunks[idx % len(chunks)]
            day_items.append(f"- {goal} (~{per_item}m)")
            idx += 1
        plan_lines.append(f"D{d}:\n" + "\n".join(day_items))

    notes = [
        "LLM unavailable: using offline heuristic plan.",
        "Adjust times based on your real schedule; rerun when LLM access returns.",
    ]

    return (
        "Priorities:\n" + "\n".join(f"- {p}" for p in priorities) + "\n\n" +
        "Plan:\n" + "\n\n".join(plan_lines) + "\n\n" +
        "Notes:\n" + "\n".join(f"- {n}" for n in notes)
    )


def generate_plan(profile: Dict, goals_text: Optional[str]) -> str:
    # If API key missing, immediately fallback
    if not settings.openai_api_key:
        return _fallback_plan(profile, goals_text)

    client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    prompt = _build_prompt(profile, goals_text, settings.planning_days)

    try:
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
        return content.strip() or _fallback_plan(profile, goals_text)
    except Exception:
        # Quota errors, network errors, etc.
        return _fallback_plan(profile, goals_text)
