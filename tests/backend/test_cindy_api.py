import asyncio
from collections.abc import Generator
from datetime import UTC, datetime
from uuid import uuid4

from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from api.auth import AuthenticatedUser, get_current_user
from api.database import get_session
from api.main import app
from api.models import (
    Base,
    Measurement,
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
ATHLETE_NO_TEAM = AuthenticatedUser(id="athlete-no-team", email="lonely@example.com")


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
    with SessionFactory.begin() as session:
        session.add_all(
            [
                WorkoutCategory(slug="strength", name="Strength", category_group="strength"),
                WorkoutCategory(
                    slug="functional_conditioning",
                    name="Functional Conditioning",
                    category_group="conditioning",
                ),
            ]
        )
        team = Team(id=uuid4(), name="Solo team", created_by=ATHLETE_A.id)
        session.add(team)
        session.flush()
        session.add(
            TeamMembership(team_id=team.id, user_id=ATHLETE_A.id, role="owner", status="active")
        )


def teardown_function() -> None:
    app.dependency_overrides.clear()


def cindy_payload(**overrides) -> dict:
    payload = {
        "total_seconds": 1150,
        "full_rounds": 8,
        "extra_pullups": 2,
        "extra_pushups": 0,
        "extra_squats": 0,
        "visibility": "team",
    }
    payload.update(overrides)
    return payload


def test_complete_requires_a_team() -> None:
    as_user(ATHLETE_NO_TEAM)
    response = asyncio.run(api_request("POST", "/api/workouts/cindy/complete", cindy_payload()))
    assert response.status_code == 422


def test_complete_creates_workout_and_result_atomically() -> None:
    as_user(ATHLETE_A)
    response = asyncio.run(
        api_request("POST", "/api/workouts/cindy/complete", cindy_payload())
    )
    assert response.status_code == 201
    body = response.json()
    assert body["total_reps"] == 8 * 30 + 2
    assert body["completed_as_prescribed"] is False

    with SessionFactory() as session:
        workout = session.scalar(select(Workout))
        assert workout is not None
        assert workout.title == "Cindy"
        assert workout.activity_type == "cindy"

        slugs = set(
            session.scalars(
                select(WorkoutCategory.slug)
                .join(WorkoutCategoryLink, WorkoutCategoryLink.category_id == WorkoutCategory.id)
                .where(WorkoutCategoryLink.workout_id == workout.id)
            )
        )
        assert slugs == {"strength", "functional_conditioning"}


def test_early_finish_is_saved_as_not_completed_as_prescribed() -> None:
    as_user(ATHLETE_A)
    response = asyncio.run(
        api_request(
            "POST", "/api/workouts/cindy/complete", cindy_payload(total_seconds=600, full_rounds=4)
        )
    )
    assert response.status_code == 201
    assert response.json()["completed_as_prescribed"] is False


def test_full_twenty_minutes_is_completed_as_prescribed() -> None:
    as_user(ATHLETE_A)
    response = asyncio.run(
        api_request("POST", "/api/workouts/cindy/complete", cindy_payload(total_seconds=1200))
    )
    assert response.json()["completed_as_prescribed"] is True


def test_estimated_calories_are_labelled_and_use_latest_bodyweight() -> None:
    with SessionFactory.begin() as session:
        session.add(
            Measurement(
                user_id=ATHLETE_A.id,
                occurred_at=datetime(2026, 8, 1, tzinfo=UTC),
                weight_kg=90,
                visibility="private",
            )
        )

    as_user(ATHLETE_A)
    response = asyncio.run(
        api_request(
            "POST", "/api/workouts/cindy/complete", cindy_payload(estimate_calories=True)
        )
    )
    body = response.json()
    assert body["calorie_source"] == "estimated"
    assert body["calorie_estimation_version"] is not None
    assert body["calories_burned"] > 0


def test_external_calories_are_labelled_accordingly() -> None:
    as_user(ATHLETE_A)
    response = asyncio.run(
        api_request(
            "POST", "/api/workouts/cindy/complete", cindy_payload(calories_burned=180)
        )
    )
    body = response.json()
    assert body["calorie_source"] == "external"
    assert body["calorie_estimation_version"] is None
    assert body["calories_burned"] == 180


def test_analytics_reports_latest_best_and_change() -> None:
    as_user(ATHLETE_A)
    asyncio.run(
        api_request(
            "POST",
            "/api/workouts/cindy/complete",
            cindy_payload(
                occurred_at="2026-08-01T06:00:00+00:00", full_rounds=7, total_seconds=1200
            ),
        )
    )
    asyncio.run(
        api_request(
            "POST",
            "/api/workouts/cindy/complete",
            cindy_payload(
                occurred_at="2026-08-08T06:00:00+00:00", full_rounds=9, total_seconds=1200
            ),
        )
    )

    response = asyncio.run(api_request("GET", "/api/analytics/cindy"))
    body = response.json()
    assert body["latest"]["full_rounds"] == 9
    assert body["personal_best"]["full_rounds"] == 9
    assert body["change_from_previous"]["full_rounds_change"] == 2
    assert len(body["history"]) == 2
