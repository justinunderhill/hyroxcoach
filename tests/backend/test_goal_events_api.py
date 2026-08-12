import asyncio
from collections.abc import Generator
from uuid import uuid4

from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from api.auth import AuthenticatedUser, get_current_user
from api.database import get_session
from api.main import app
from api.models import Base, Team, TeamMembership

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)

ATHLETE_A = AuthenticatedUser(id="athlete-a", email="a@example.com")
ATHLETE_B = AuthenticatedUser(id="athlete-b", email="b@example.com")
OUTSIDER = AuthenticatedUser(id="outsider", email="o@example.com")


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


GOAL_EVENT_PAYLOAD = {
    "name": "HYROX Doubles London",
    "event_date": "2026-11-01",
    "division": "Open",
    "location": "ExCeL London",
}


def test_get_goal_event_returns_null_when_unset() -> None:
    team_id = make_team(ATHLETE_A.id)
    as_user(ATHLETE_A)
    response = asyncio.run(api_request("GET", f"/api/teams/{team_id}/goal-event"))
    assert response.status_code == 200
    assert response.json() is None


def test_any_team_member_can_set_the_goal_event() -> None:
    team_id = make_team(ATHLETE_A.id, extra_member_id=ATHLETE_B.id)
    as_user(ATHLETE_B)
    response = asyncio.run(
        api_request("PUT", f"/api/teams/{team_id}/goal-event", GOAL_EVENT_PAYLOAD)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "HYROX Doubles London"
    assert body["division"] == "Open"
    assert isinstance(body["days_until_event"], int)

    as_user(ATHLETE_A)
    get_response = asyncio.run(api_request("GET", f"/api/teams/{team_id}/goal-event"))
    assert get_response.json()["name"] == "HYROX Doubles London"


def test_upsert_replaces_the_single_team_goal_event() -> None:
    team_id = make_team(ATHLETE_A.id)
    as_user(ATHLETE_A)
    asyncio.run(api_request("PUT", f"/api/teams/{team_id}/goal-event", GOAL_EVENT_PAYLOAD))

    updated = {**GOAL_EVENT_PAYLOAD, "name": "HYROX Doubles Manchester", "event_date": "2027-02-01"}
    response = asyncio.run(api_request("PUT", f"/api/teams/{team_id}/goal-event", updated))
    assert response.status_code == 200
    assert response.json()["name"] == "HYROX Doubles Manchester"

    get_response = asyncio.run(api_request("GET", f"/api/teams/{team_id}/goal-event"))
    assert get_response.json()["name"] == "HYROX Doubles Manchester"


def test_non_member_cannot_access_goal_event() -> None:
    team_id = make_team(ATHLETE_A.id)
    as_user(OUTSIDER)
    get_response = asyncio.run(api_request("GET", f"/api/teams/{team_id}/goal-event"))
    assert get_response.status_code == 404

    put_response = asyncio.run(
        api_request("PUT", f"/api/teams/{team_id}/goal-event", GOAL_EVENT_PAYLOAD)
    )
    assert put_response.status_code == 404
