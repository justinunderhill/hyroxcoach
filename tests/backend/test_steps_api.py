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
from api.models import Base, Team, TeamMembership

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)

ATHLETE_A = AuthenticatedUser(id="athlete-a", email="a@example.com")
ATHLETE_B = AuthenticatedUser(id="athlete-b", email="b@example.com")

TODAY = datetime.now(UTC).date().isoformat()


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


def make_team(owner_id: str, extra_member_id: str | None = None) -> None:
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


def test_put_creates_then_updates_the_same_day_entry() -> None:
    as_user(ATHLETE_A)
    create_response = asyncio.run(
        api_request("PUT", f"/api/steps/{TODAY}", {"steps": 8000, "source": "manual"})
    )
    assert create_response.status_code == 200
    assert create_response.json()["steps"] == 8000

    update_response = asyncio.run(
        api_request("PUT", f"/api/steps/{TODAY}", {"steps": 9500, "source": "health_connect"})
    )
    assert update_response.status_code == 200
    assert update_response.json()["steps"] == 9500
    assert update_response.json()["source"] == "health_connect"

    list_response = asyncio.run(api_request("GET", "/api/steps"))
    assert len(list_response.json()["entries"]) == 1
    assert list_response.json()["weekly_total"] == 9500


def test_private_steps_are_not_visible_to_teammates() -> None:
    make_team(ATHLETE_A.id, extra_member_id=ATHLETE_B.id)
    as_user(ATHLETE_A)
    asyncio.run(api_request("PUT", f"/api/steps/{TODAY}", {"steps": 8000, "visibility": "private"}))

    as_user(ATHLETE_B)
    response = asyncio.run(api_request("GET", "/api/steps"))
    assert response.json()["entries"] == []
    assert response.json()["weekly_total"] == 0


def test_team_visible_steps_appear_for_teammates() -> None:
    make_team(ATHLETE_A.id, extra_member_id=ATHLETE_B.id)
    as_user(ATHLETE_A)
    asyncio.run(api_request("PUT", f"/api/steps/{TODAY}", {"steps": 8000, "visibility": "team"}))

    as_user(ATHLETE_B)
    response = asyncio.run(api_request("GET", "/api/steps"))
    entries = response.json()["entries"]
    assert len(entries) == 1
    assert entries[0]["user_id"] == ATHLETE_A.id
    # A teammate's shared steps must not pollute the viewer's own weekly total.
    assert response.json()["weekly_total"] == 0
