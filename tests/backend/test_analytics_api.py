import asyncio
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from api.auth import AuthenticatedUser, get_current_user
from api.database import get_session
from api.main import app
from api.models import Base, Team, TeamMembership, Workout, WorkoutCategory

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
