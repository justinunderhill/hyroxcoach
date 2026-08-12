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


def test_measurement_requires_at_least_one_value() -> None:
    as_user(ATHLETE_A)
    response = asyncio.run(api_request("POST", "/api/measurements", {}))
    assert response.status_code == 422


def test_measurements_are_private_by_default() -> None:
    make_team(ATHLETE_A.id, extra_member_id=ATHLETE_B.id)
    as_user(ATHLETE_A)
    create_response = asyncio.run(
        api_request("POST", "/api/measurements", {"weight_kg": 82.4})
    )
    assert create_response.status_code == 201
    assert create_response.json()["visibility"] == "private"

    as_user(ATHLETE_B)
    list_response = asyncio.run(api_request("GET", "/api/measurements"))
    assert list_response.json() == []


def test_team_visible_measurement_appears_for_teammates() -> None:
    make_team(ATHLETE_A.id, extra_member_id=ATHLETE_B.id)
    as_user(ATHLETE_A)
    asyncio.run(
        api_request(
            "POST", "/api/measurements", {"weight_kg": 82.4, "visibility": "team"}
        )
    )

    as_user(ATHLETE_B)
    list_response = asyncio.run(api_request("GET", "/api/measurements"))
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["user_id"] == ATHLETE_A.id


def test_owner_can_update_a_measurement() -> None:
    as_user(ATHLETE_A)
    create_response = asyncio.run(
        api_request("POST", "/api/measurements", {"weight_kg": 82.4})
    )
    measurement_id = create_response.json()["id"]

    update_response = asyncio.run(
        api_request(
            "PATCH", f"/api/measurements/{measurement_id}", {"weight_kg": 81.9, "notes": "fasted"}
        )
    )
    assert update_response.status_code == 200
    assert update_response.json()["weight_kg"] == "81.90"
    assert update_response.json()["notes"] == "fasted"


def test_only_owner_can_update_a_measurement() -> None:
    make_team(ATHLETE_A.id, extra_member_id=ATHLETE_B.id)
    as_user(ATHLETE_A)
    create_response = asyncio.run(
        api_request("POST", "/api/measurements", {"weight_kg": 82.4, "visibility": "team"})
    )
    measurement_id = create_response.json()["id"]

    as_user(ATHLETE_B)
    update_response = asyncio.run(
        api_request("PATCH", f"/api/measurements/{measurement_id}", {"weight_kg": 70.0})
    )
    assert update_response.status_code == 404


def test_only_owner_can_delete_a_measurement() -> None:
    make_team(ATHLETE_A.id, extra_member_id=ATHLETE_B.id)
    as_user(ATHLETE_A)
    create_response = asyncio.run(
        api_request("POST", "/api/measurements", {"weight_kg": 82.4, "visibility": "team"})
    )
    measurement_id = create_response.json()["id"]

    as_user(ATHLETE_B)
    delete_response = asyncio.run(api_request("DELETE", f"/api/measurements/{measurement_id}"))
    assert delete_response.status_code == 404

    as_user(ATHLETE_A)
    delete_response = asyncio.run(api_request("DELETE", f"/api/measurements/{measurement_id}"))
    assert delete_response.status_code == 204
