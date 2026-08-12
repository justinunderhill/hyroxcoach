import asyncio
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from api.auth import AuthenticatedUser, get_current_user
from api.database import get_session
from api.main import app
from api.models import (
    AthleteProfile,
    Base,
    ExercisePerformance,
    Team,
    TeamMembership,
    Workout,
    WorkoutCategory,
    WorkoutCategoryLink,
)

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)

ATHLETE_A = AuthenticatedUser(id="athlete-a", email="a@example.com")
ATHLETE_B = AuthenticatedUser(id="athlete-b", email="b@example.com")


def override_session() -> Generator[Session, None, None]:
    with SessionFactory() as session:
        yield session


def as_user(user: AuthenticatedUser) -> None:
    app.dependency_overrides[get_current_user] = lambda: user


async def api_request(method: str, path: str) -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.request(method, path)


def setup_function() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    app.dependency_overrides = {get_session: override_session}
    with SessionFactory.begin() as session:
        session.add(WorkoutCategory(slug="running", name="Running", category_group="running"))
        team = Team(id=uuid4(), name="Solo team", created_by=ATHLETE_A.id)
        session.add(team)
        session.flush()
        session.add(
            TeamMembership(team_id=team.id, user_id=ATHLETE_A.id, role="owner", status="active")
        )
        session.add(
            Workout(
                id=uuid4(),
                user_id=ATHLETE_A.id,
                team_id=team.id,
                occurred_at=datetime.now(UTC) - timedelta(days=1),
                title="Parkrun",
                activity_type="running",
                distance_km=5.0,
                duration_minutes=25,
                visibility="private",
            )
        )


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_analytics_only_reflects_the_caller_own_workouts() -> None:
    as_user(ATHLETE_A)
    response_a = asyncio.run(api_request("GET", "/api/analytics/me"))
    assert response_a.status_code == 200
    assert response_a.json()["consistency"]["sessions_last_7_days"] == 1
    assert response_a.json()["running"]["weekly_distance_km"] == 5.0

    as_user(ATHLETE_B)
    response_b = asyncio.run(api_request("GET", "/api/analytics/me"))
    assert response_b.status_code == 200
    assert response_b.json()["consistency"]["sessions_last_7_days"] == 0
    assert response_b.json()["data_note"] is not None


def test_me_surfaces_station_history_and_personal_bests() -> None:
    with SessionFactory.begin() as session:
        team = session.scalar(select(Team).where(Team.created_by == ATHLETE_A.id))
        workout = Workout(
            id=uuid4(),
            user_id=ATHLETE_A.id,
            team_id=team.id,
            occurred_at=datetime.now(UTC) - timedelta(days=2),
            title="HYROX sim",
            activity_type="hyrox",
            visibility="private",
        )
        session.add(workout)
        session.flush()
        session.add(
            ExercisePerformance(
                workout_id=workout.id,
                exercise_name="Sled Push",
                normalized_exercise_key="sled_push",
                duration_seconds=70,
            )
        )

    as_user(ATHLETE_A)
    response = asyncio.run(api_request("GET", "/api/analytics/me"))
    body = response.json()
    assert len(body["station_history"]) == 1
    assert body["station_history"][0]["exercise_key"] == "sled_push"
    assert len(body["personal_bests"]) == 1
    assert body["personal_bests"][0]["best_value"] == 70


def test_team_analytics_requires_active_membership() -> None:
    with SessionFactory.begin() as session:
        other_team = Team(id=uuid4(), name="Other team", created_by=ATHLETE_B.id)
        session.add(other_team)
        session.flush()
        session.add(
            TeamMembership(
                team_id=other_team.id, user_id=ATHLETE_B.id, role="owner", status="active"
            )
        )
        other_team_id = other_team.id

    as_user(ATHLETE_A)
    response = asyncio.run(api_request("GET", f"/api/analytics/team/{other_team_id}"))
    assert response.status_code == 404


def test_team_analytics_combines_athletes_and_flags_gaps() -> None:
    with SessionFactory.begin() as session:
        team = session.scalar(select(Team).where(Team.created_by == ATHLETE_A.id))
        session.add(
            TeamMembership(
                team_id=team.id, user_id=ATHLETE_B.id, role="athlete", status="active"
            )
        )
        session.add(
            AthleteProfile(user_id=ATHLETE_A.id, display_name="Athlete A", timezone="UTC")
        )
        session.add(
            AthleteProfile(user_id=ATHLETE_B.id, display_name="Athlete B", timezone="UTC")
        )
        strength_category = WorkoutCategory(
            id=uuid4(), slug="strength", name="Strength", category_group="strength"
        )
        session.add(strength_category)
        strength_workout = Workout(
            id=uuid4(),
            user_id=ATHLETE_B.id,
            team_id=team.id,
            occurred_at=datetime.now(UTC) - timedelta(days=1),
            title="Strength",
            activity_type="strength",
            visibility="team",
        )
        session.add(strength_workout)
        session.flush()
        session.add(
            WorkoutCategoryLink(
                workout_id=strength_workout.id, category_id=strength_category.id
            )
        )
        team_id = team.id

    as_user(ATHLETE_A)
    response = asyncio.run(api_request("GET", f"/api/analytics/team/{team_id}"))
    assert response.status_code == 200
    body = response.json()

    by_user = {athlete["user_id"]: athlete for athlete in body["athletes"]}
    assert set(by_user) == {ATHLETE_A.id, ATHLETE_B.id}
    assert by_user[ATHLETE_A.id]["display_name"] == "Athlete A"
    assert by_user[ATHLETE_B.id]["display_name"] == "Athlete B"
    assert by_user[ATHLETE_A.id]["running"]["weekly_distance_km"] == 5.0
    assert body["combined_category_coverage"]["strength"] == 1
    assert "strength" not in body["neglected_categories"]
    assert "running" in body["neglected_categories"]


def test_team_analytics_excludes_a_teammates_private_workout() -> None:
    with SessionFactory.begin() as session:
        team = session.scalar(select(Team).where(Team.created_by == ATHLETE_A.id))
        session.add(
            TeamMembership(
                team_id=team.id, user_id=ATHLETE_B.id, role="athlete", status="active"
            )
        )
        session.add(
            Workout(
                id=uuid4(),
                user_id=ATHLETE_B.id,
                team_id=team.id,
                occurred_at=datetime.now(UTC) - timedelta(days=1),
                title="Private strength session",
                activity_type="strength",
                visibility="private",
            )
        )
        team_id = team.id

    as_user(ATHLETE_A)
    response = asyncio.run(api_request("GET", f"/api/analytics/team/{team_id}"))
    body = response.json()
    by_user = {athlete["user_id"]: athlete for athlete in body["athletes"]}
    assert by_user[ATHLETE_B.id]["consistency"]["sessions_last_7_days"] == 0
