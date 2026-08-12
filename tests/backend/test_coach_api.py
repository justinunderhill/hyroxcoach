import asyncio
import json
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from api.auth import AuthenticatedUser, get_current_user
from api.database import get_session
from api.main import app
from api.models import AthleteProfile, Base, CoachInsight, Team, TeamMembership, Workout
from api.services import ai_client, coach

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)

ATHLETE_A = AuthenticatedUser(id="athlete-a", email="a@example.com")
ATHLETE_B = AuthenticatedUser(id="athlete-b", email="b@example.com")
OUTSIDER = AuthenticatedUser(id="outsider", email="o@example.com")

VALID_INSIGHT = {
    "summary": "Solid week of consistent running with no station work logged.",
    "status": "on_track",
    "wins": [{"title": "Consistent running", "evidence": "3 sessions logged this week"}],
    "gaps": [
        {
            "title": "No station work",
            "evidence": "Zero SkiErg/Sled sessions in the last 7 days",
            "priority": "medium",
        }
    ],
    "recommendations": [
        {
            "action": "Add one station session",
            "reason": "HYROX events require station work",
            "time_horizon": "this_week",
        }
    ],
    "team_notes": [],
    "data_limits": [],
}

INSUFFICIENT_DATA_INSIGHT = {
    "summary": "Not enough logged history yet to assess this athlete's training.",
    "status": "insufficient_data",
    "wins": [],
    "gaps": [],
    "recommendations": [],
    "team_notes": [],
    "data_limits": ["No workouts logged in the last 7 days."],
}


def override_session() -> Generator[Session, None, None]:
    with SessionFactory() as session:
        yield session


def as_user(user: AuthenticatedUser) -> None:
    app.dependency_overrides[get_current_user] = lambda: user


async def api_request(method: str, path: str, json: dict | None = None) -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.request(method, path, json=json)


def setup_function() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    app.dependency_overrides = {get_session: override_session}


def teardown_function() -> None:
    app.dependency_overrides.clear()


def make_team(owner_id: str, extra_member_id: str | None = None) -> str:
    with SessionFactory.begin() as session:
        team = Team(id=uuid4(), name="Solo team", created_by=owner_id)
        session.add(team)
        session.flush()
        session.add(
            TeamMembership(team_id=team.id, user_id=owner_id, role="owner", status="active")
        )
        if extra_member_id:
            session.add(
                TeamMembership(
                    team_id=team.id, user_id=extra_member_id, role="athlete", status="active"
                )
            )
        return str(team.id)


def make_profile(user_id: str, display_name: str = "Athlete") -> None:
    with SessionFactory.begin() as session:
        session.add(AthleteProfile(user_id=user_id, display_name=display_name, timezone="UTC"))


def make_workout(user_id: str, team_id: str, visibility: str = "team", days_ago: int = 1) -> str:
    with SessionFactory.begin() as session:
        workout = Workout(
            id=uuid4(),
            user_id=user_id,
            team_id=UUID(team_id),
            occurred_at=datetime.now(UTC) - timedelta(days=days_ago),
            title="Parkrun",
            activity_type="running",
            distance_km=5,
            duration_minutes=28,
            visibility=visibility,
        )
        session.add(workout)
        session.flush()
        return str(workout.id)


def _mock_model(monkeypatch: pytest.MonkeyPatch, insight: dict, calls: list | None = None):
    def fake_call(system_prompt: str, user_prompt: str, json_schema: dict) -> str:
        if calls is not None:
            calls.append(user_prompt)
        return json.dumps(insight)

    monkeypatch.setattr(ai_client, "call_text_model", fake_call)


def test_system_prompt_guards_against_prompt_injection() -> None:
    assert "ignore" in coach.SYSTEM_PROMPT.lower()
    assert "untrusted" in coach.SYSTEM_PROMPT.lower()


def test_workout_insight_is_generated_and_persisted(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_model(monkeypatch, VALID_INSIGHT)
    team_id = make_team(ATHLETE_A.id)
    make_profile(ATHLETE_A.id)
    workout_id = make_workout(ATHLETE_A.id, team_id)

    as_user(ATHLETE_A)
    response = asyncio.run(api_request("POST", f"/api/coach/workout/{workout_id}"))
    assert response.status_code == 201
    body = response.json()
    assert body["scope"] == "workout"
    assert body["source_record_id"] == workout_id
    assert body["insight"]["status"] == "on_track"
    assert body["insight"]["wins"][0]["title"] == "Consistent running"

    with SessionFactory() as session:
        rows = session.scalars(select(CoachInsight)).all()
        assert len(rows) == 1
        assert rows[0].coach_version == "coach-v1"


def test_only_owner_can_generate_workout_insight(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_model(monkeypatch, VALID_INSIGHT)
    team_id = make_team(ATHLETE_A.id, extra_member_id=ATHLETE_B.id)
    workout_id = make_workout(ATHLETE_A.id, team_id)

    as_user(ATHLETE_B)
    response = asyncio.run(api_request("POST", f"/api/coach/workout/{workout_id}"))
    assert response.status_code == 404


def test_weekly_review_reuses_cached_insight_for_unchanged_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list = []
    _mock_model(monkeypatch, VALID_INSIGHT, calls)
    make_team(ATHLETE_A.id)
    make_profile(ATHLETE_A.id)

    as_user(ATHLETE_A)
    first = asyncio.run(api_request("GET", "/api/coach/weekly"))
    second = asyncio.run(api_request("GET", "/api/coach/weekly"))

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert len(calls) == 1


def test_weekly_review_regenerates_when_context_changes(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list = []
    _mock_model(monkeypatch, VALID_INSIGHT, calls)
    team_id = make_team(ATHLETE_A.id)
    make_profile(ATHLETE_A.id)

    as_user(ATHLETE_A)
    first = asyncio.run(api_request("GET", "/api/coach/weekly"))
    make_workout(ATHLETE_A.id, team_id)
    second = asyncio.run(api_request("GET", "/api/coach/weekly"))

    assert first.json()["id"] != second.json()["id"]
    assert len(calls) == 2


def test_team_weekly_requires_membership(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_model(monkeypatch, VALID_INSIGHT)
    team_id = make_team(ATHLETE_A.id)

    as_user(OUTSIDER)
    response = asyncio.run(api_request("GET", f"/api/coach/team/{team_id}/weekly"))
    assert response.status_code == 404


def test_team_weekly_context_excludes_private_workouts(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list = []
    _mock_model(monkeypatch, VALID_INSIGHT, calls)
    team_id = make_team(ATHLETE_A.id, extra_member_id=ATHLETE_B.id)
    make_profile(ATHLETE_A.id, display_name="Justin")
    make_profile(ATHLETE_B.id, display_name="Partner")
    make_workout(ATHLETE_A.id, team_id, visibility="private")
    make_workout(ATHLETE_A.id, team_id, visibility="team")

    as_user(ATHLETE_A)
    response = asyncio.run(api_request("GET", f"/api/coach/team/{team_id}/weekly"))
    assert response.status_code == 200
    assert body_prompt_contains_only_shared_session_count(calls[0])


def body_prompt_contains_only_shared_session_count(prompt: str) -> bool:
    context = json.loads(prompt.split("CoachContext (JSON):\n", 1)[1].split("\n\nProduce", 1)[0])
    # Only the one visibility="team" workout should be counted, not the private one.
    return context["athletes"][0]["weekly_sessions"] == 1


def test_model_failure_returns_502_and_persists_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*args: object, **kwargs: object) -> str:
        raise RuntimeError("upstream timeout")

    monkeypatch.setattr(ai_client, "call_text_model", boom)
    make_team(ATHLETE_A.id)
    make_profile(ATHLETE_A.id)

    as_user(ATHLETE_A)
    response = asyncio.run(api_request("GET", "/api/coach/weekly"))
    assert response.status_code == 502

    with SessionFactory() as session:
        assert session.scalars(select(CoachInsight)).all() == []


def test_malformed_model_output_returns_502(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ai_client, "call_text_model", lambda *a, **k: "not valid json")
    make_team(ATHLETE_A.id)
    make_profile(ATHLETE_A.id)

    as_user(ATHLETE_A)
    response = asyncio.run(api_request("GET", "/api/coach/weekly"))
    assert response.status_code == 502


def test_insufficient_data_status_is_preserved(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_model(monkeypatch, INSUFFICIENT_DATA_INSIGHT)
    make_team(ATHLETE_A.id)
    make_profile(ATHLETE_A.id)

    as_user(ATHLETE_A)
    response = asyncio.run(api_request("GET", "/api/coach/weekly"))
    assert response.status_code == 200
    assert response.json()["insight"]["status"] == "insufficient_data"
