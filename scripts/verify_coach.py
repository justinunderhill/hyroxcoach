"""Exercises the real OpenAI text-generation path for Phase 7 (AI Coach V1):
build a realistic CoachContext -> real model call -> strict schema
validation, via the actual coach.generate_insight() code path (context
hashing included). Not just the mocked pytest suite.
"""

from datetime import date, timedelta

from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker

from api.database import get_engine, set_request_user
from api.models import Team
from api.schemas.coach import CoachInsightData
from api.services import ai_client
from api.services.analytics import RunningSummary
from api.services.coach import generate_insight
from api.services.coach_context import (
    NutritionContextInputs,
    PeriodInfo,
    TargetEventInfo,
    assemble_athlete_context,
)

load_dotenv(".env.local")

today = date.today()
period_start = today - timedelta(days=7)
period_end = today
context = assemble_athlete_context(
    display_name="Test Athlete",
    baseline_5k_seconds=1500,
    period=PeriodInfo(scope="weekly", start=period_start, end=period_end),
    target_event=TargetEventInfo(
        name="HYROX London",
        event_date=today + timedelta(days=60),
        days_until_event=60,
        division="doubles",
    ),
    recent_workouts=[
        {
            "date": (today - timedelta(days=2)).isoformat(),
            "category": "run",
            "notes": "5k tempo",
        },
        {
            "date": (today - timedelta(days=4)).isoformat(),
            "category": "gym",
            "notes": "sled pushes",
        },
    ],
    weekly_sessions=2,
    weekly_active_days=2,
    category_coverage_counts={"run": 1, "gym": 1, "mma": 0, "walk": 0},
    running=RunningSummary(
        weekly_distance_km=5.0,
        avg_pace_seconds_per_km=330,
        best_5k_seconds=1490,
        recent=[],
    ),
    station_progressions=[],
    strength_progressions=[],
    personal_bests=[],
    nutrition=NutritionContextInputs(
        days_logged=3,
        days_in_range=7,
        avg_calories=2400.0,
        calories_target=2600,
        estimated_share=0.6,
    ),
)

fake_user_id = "verify-script-fake-user"
session_factory = sessionmaker(bind=get_engine(), expire_on_commit=False)
session = session_factory()
try:
    set_request_user(session, fake_user_id)
    scratch_team = Team(name="verify-coach-scratch-team", created_by=fake_user_id)
    session.add(scratch_team)
    session.flush()
    insight = generate_insight(
        session,
        scope="weekly",
        user_id=fake_user_id,
        team_id=scratch_team.id,
        period_start=period_start,
        period_end=period_end,
        source_record_id=None,
        context=context,
        reuse_cached=False,
    )
    session.rollback()  # never persist this synthetic run
finally:
    session.close()

parsed = CoachInsightData.model_validate(insight.insight_json)

print(f"model: {ai_client.coach_model_name()}")
print(f"status: {parsed.status}")
print(f"summary: {parsed.summary}")
print(f"wins: {len(parsed.wins)}")
print(f"gaps: {len(parsed.gaps)}")
print(f"recommendations: {len(parsed.recommendations)}")
print(f"data_limits: {parsed.data_limits}")

if not parsed.summary.strip():
    raise SystemExit("Expected a non-empty summary from the model.")
if parsed.status not in ("on_track", "mixed", "needs_attention", "insufficient_data"):
    raise SystemExit(f"Unexpected status: {parsed.status}")

print(
    "\nCoach verified: real OpenAI text call returned schema-valid, "
    "context-grounded coaching output."
)
