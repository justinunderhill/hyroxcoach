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


def meal_payload(**overrides) -> dict:
    payload = {
        "occurred_at": "2026-08-08T07:00:00+00:00",
        "meal_type": "breakfast",
        "description": "Oats, banana, protein shake",
        "calories": 550,
        "protein_g": 40,
        "carbs_g": 70,
        "fat_g": 12,
        "visibility": "private",
    }
    payload.update(overrides)
    return payload


def test_create_meal_requires_a_team() -> None:
    as_user(ATHLETE_A)
    response = asyncio.run(api_request("POST", "/api/meals", meal_payload()))
    assert response.status_code == 422


def test_create_and_list_own_meals() -> None:
    make_team(ATHLETE_A.id)
    as_user(ATHLETE_A)

    create_response = asyncio.run(api_request("POST", "/api/meals", meal_payload()))
    assert create_response.status_code == 201
    assert create_response.json()["description"] == "Oats, banana, protein shake"

    list_response = asyncio.run(api_request("GET", "/api/meals"))
    assert len(list_response.json()) == 1


def test_private_meals_are_not_visible_to_teammates() -> None:
    make_team(ATHLETE_A.id, extra_member_id=ATHLETE_B.id)
    as_user(ATHLETE_A)
    asyncio.run(api_request("POST", "/api/meals", meal_payload(visibility="private")))

    as_user(ATHLETE_B)
    list_response = asyncio.run(api_request("GET", "/api/meals"))
    assert list_response.json() == []


def test_team_visible_meals_appear_for_teammates() -> None:
    make_team(ATHLETE_A.id, extra_member_id=ATHLETE_B.id)
    as_user(ATHLETE_A)
    asyncio.run(api_request("POST", "/api/meals", meal_payload(visibility="team")))

    as_user(ATHLETE_B)
    list_response = asyncio.run(api_request("GET", "/api/meals"))
    assert len(list_response.json()) == 1


def test_only_the_owner_can_update_or_delete_a_meal() -> None:
    make_team(ATHLETE_A.id, extra_member_id=ATHLETE_B.id)
    as_user(ATHLETE_A)
    create_response = asyncio.run(
        api_request("POST", "/api/meals", meal_payload(visibility="team"))
    )
    meal_id = create_response.json()["id"]

    as_user(ATHLETE_B)
    patch_response = asyncio.run(
        api_request("PATCH", f"/api/meals/{meal_id}", {"description": "Hijacked"})
    )
    assert patch_response.status_code == 404

    delete_response = asyncio.run(api_request("DELETE", f"/api/meals/{meal_id}"))
    assert delete_response.status_code == 404

    as_user(ATHLETE_A)
    patch_response = asyncio.run(
        api_request("PATCH", f"/api/meals/{meal_id}", {"description": "Updated"})
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["description"] == "Updated"
