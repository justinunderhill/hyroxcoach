import asyncio
from collections.abc import Generator
from datetime import UTC, datetime
from uuid import uuid4

from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from api.auth import AuthenticatedUser, get_current_user
from api.database import get_session
from api.main import app
from api.models import AthleteProfile, Base, Meal, Team, TeamMembership

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


async def api_request(method: str, path: str, json: dict | None = None) -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.request(method, path, json=json)


def setup_function() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    app.dependency_overrides = {get_session: override_session}
    with SessionFactory.begin() as session:
        team = Team(id=uuid4(), name="Solo team", created_by=ATHLETE_A.id)
        session.add(team)
        session.flush()
        session.add(
            TeamMembership(team_id=team.id, user_id=ATHLETE_A.id, role="owner", status="active")
        )
        session.add(
            Meal(
                id=uuid4(),
                user_id=ATHLETE_A.id,
                team_id=team.id,
                occurred_at=datetime.now(UTC),
                description="Oats and eggs",
                calories=500,
                protein_g=35,
                visibility="private",
            )
        )


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_no_target_yields_null_target_and_remaining() -> None:
    as_user(ATHLETE_A)
    response = asyncio.run(api_request("GET", "/api/nutrition/daily"))
    assert response.status_code == 200
    body = response.json()
    assert body["target"] is None
    assert body["remaining"]["calories"] is None
    assert body["consumed"]["calories"] == 500
    assert len(body["meals"]) == 1


def test_create_target_and_see_it_reflected_in_daily_totals() -> None:
    as_user(ATHLETE_A)
    create_response = asyncio.run(
        api_request(
            "POST",
            "/api/nutrition/targets",
            {"calories_target": 2200, "protein_g_target": 160},
        )
    )
    assert create_response.status_code == 201

    daily_response = asyncio.run(api_request("GET", "/api/nutrition/daily"))
    body = daily_response.json()
    assert body["target"]["calories_target"] == 2200
    assert body["remaining"]["calories"] == 1700
    assert body["remaining"]["protein_g"] == 125.0
    assert body["remaining"]["carbs_g"] is None


def test_daily_nutrition_only_reflects_the_caller_own_meals() -> None:
    as_user(ATHLETE_B)
    response = asyncio.run(api_request("GET", "/api/nutrition/daily"))
    assert response.status_code == 200
    body = response.json()
    assert body["consumed"]["calories"] == 0
    assert body["meals"] == []


def test_target_requires_at_least_one_value() -> None:
    as_user(ATHLETE_A)
    response = asyncio.run(api_request("POST", "/api/nutrition/targets", {}))
    assert response.status_code == 422


def test_daily_uses_athlete_timezone_for_day_boundary() -> None:
    with SessionFactory.begin() as session:
        session.add(
            AthleteProfile(
                user_id=ATHLETE_A.id, display_name="A", timezone="Pacific/Auckland"
            )
        )
        # 11pm local time in Pacific/Auckland (UTC+12/13) is already the next UTC day.
        session.add(
            Meal(
                id=uuid4(),
                user_id=ATHLETE_A.id,
                team_id=session.query(Team).first().id,
                occurred_at=datetime(2026, 8, 12, 10, 0, tzinfo=UTC),
                description="Late dinner",
                calories=300,
                visibility="private",
            )
        )

    as_user(ATHLETE_A)
    response = asyncio.run(api_request("GET", "/api/nutrition/daily?date=2026-08-12"))
    body = response.json()
    descriptions = [meal["description"] for meal in body["meals"]]
    assert "Late dinner" in descriptions
