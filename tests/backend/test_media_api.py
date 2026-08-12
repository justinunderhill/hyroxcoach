import asyncio
from collections.abc import Generator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from api.auth import AuthenticatedUser, get_current_user
from api.database import get_session
from api.main import app
from api.models import Base, Meal, Measurement, Team, TeamMembership, Workout
from api.services import storage

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


@pytest.fixture(autouse=True)
def _stub_storage(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(storage, "create_upload_url", lambda path, mime, ttl: f"https://upload/{path}")
    monkeypatch.setattr(storage, "create_download_url", lambda path, ttl: f"https://download/{path}")
    monkeypatch.setattr(storage, "delete_object", lambda path: None)


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


def make_workout(user_id: str, visibility: str = "private") -> str:
    with SessionFactory.begin() as session:
        team = session.query(Team).one()
        workout = Workout(
            id=uuid4(),
            user_id=user_id,
            team_id=team.id,
            occurred_at=datetime.now(UTC),
            title="Parkrun",
            activity_type="running",
            visibility=visibility,
        )
        session.add(workout)
        session.flush()
        return str(workout.id)


def make_meal(user_id: str, visibility: str = "private") -> str:
    with SessionFactory.begin() as session:
        team = session.query(Team).one()
        meal = Meal(
            id=uuid4(),
            user_id=user_id,
            team_id=team.id,
            occurred_at=datetime.now(UTC),
            description="Oats",
            visibility=visibility,
        )
        session.add(meal)
        session.flush()
        return str(meal.id)


def make_measurement(user_id: str, visibility: str = "private") -> str:
    with SessionFactory.begin() as session:
        measurement = Measurement(
            id=uuid4(), user_id=user_id, weight_kg=80, visibility=visibility
        )
        session.add(measurement)
        session.flush()
        return str(measurement.id)


UPLOAD_PAYLOAD = {
    "purpose": "workout_evidence",
    "mime_type": "image/jpeg",
    "size_bytes": 1_000,
}


def test_upload_intent_rejects_unsupported_mime_type() -> None:
    make_team(ATHLETE_A.id)
    as_user(ATHLETE_A)
    response = asyncio.run(
        api_request(
            "POST",
            "/api/media/upload-intent",
            {**UPLOAD_PAYLOAD, "mime_type": "application/pdf"},
        )
    )
    assert response.status_code == 422


def test_upload_intent_rejects_oversized_file() -> None:
    make_team(ATHLETE_A.id)
    as_user(ATHLETE_A)
    response = asyncio.run(
        api_request(
            "POST",
            "/api/media/upload-intent",
            {**UPLOAD_PAYLOAD, "size_bytes": 999_999_999},
        )
    )
    assert response.status_code == 422


def test_upload_intent_creates_asset_and_returns_upload_url() -> None:
    make_team(ATHLETE_A.id)
    as_user(ATHLETE_A)
    response = asyncio.run(api_request("POST", "/api/media/upload-intent", UPLOAD_PAYLOAD))
    assert response.status_code == 201
    body = response.json()
    assert body["media_asset"]["user_id"] == ATHLETE_A.id
    assert body["upload_url"].startswith("https://upload/")
    assert body["upload_headers"]["Content-Type"] == "image/jpeg"


def test_upload_intent_cannot_attach_to_another_users_workout() -> None:
    make_team(ATHLETE_A.id, extra_member_id=ATHLETE_B.id)
    workout_id = make_workout(ATHLETE_A.id)

    as_user(ATHLETE_B)
    response = asyncio.run(
        api_request(
            "POST",
            "/api/media/upload-intent",
            {**UPLOAD_PAYLOAD, "entity_type": "workout", "entity_id": workout_id},
        )
    )
    assert response.status_code == 404


def test_upload_intent_links_to_owned_workout() -> None:
    make_team(ATHLETE_A.id)
    workout_id = make_workout(ATHLETE_A.id)
    as_user(ATHLETE_A)

    response = asyncio.run(
        api_request(
            "POST",
            "/api/media/upload-intent",
            {**UPLOAD_PAYLOAD, "entity_type": "workout", "entity_id": workout_id},
        )
    )
    assert response.status_code == 201

    list_response = asyncio.run(
        api_request("GET", f"/api/media?entity_type=workout&entity_ids={workout_id}")
    )
    assert list_response.status_code == 200
    items = list_response.json()
    assert len(items) == 1
    assert items[0]["entity_id"] == workout_id
    assert items[0]["view_url"].startswith("https://download/")


def test_private_workout_media_is_not_visible_to_teammate() -> None:
    make_team(ATHLETE_A.id, extra_member_id=ATHLETE_B.id)
    workout_id = make_workout(ATHLETE_A.id, visibility="private")
    as_user(ATHLETE_A)
    asyncio.run(
        api_request(
            "POST",
            "/api/media/upload-intent",
            {**UPLOAD_PAYLOAD, "entity_type": "workout", "entity_id": workout_id},
        )
    )

    as_user(ATHLETE_B)
    list_response = asyncio.run(
        api_request("GET", f"/api/media?entity_type=workout&entity_ids={workout_id}")
    )
    assert list_response.json() == []


def test_team_visible_workout_media_is_visible_to_teammate() -> None:
    make_team(ATHLETE_A.id, extra_member_id=ATHLETE_B.id)
    workout_id = make_workout(ATHLETE_A.id, visibility="team")
    as_user(ATHLETE_A)
    asyncio.run(
        api_request(
            "POST",
            "/api/media/upload-intent",
            {**UPLOAD_PAYLOAD, "entity_type": "workout", "entity_id": workout_id},
        )
    )

    as_user(ATHLETE_B)
    list_response = asyncio.run(
        api_request("GET", f"/api/media?entity_type=workout&entity_ids={workout_id}")
    )
    assert len(list_response.json()) == 1


def test_meal_photo_attach_and_view() -> None:
    make_team(ATHLETE_A.id)
    meal_id = make_meal(ATHLETE_A.id)
    as_user(ATHLETE_A)

    response = asyncio.run(
        api_request(
            "POST",
            "/api/media/upload-intent",
            {
                "purpose": "meal_photo",
                "mime_type": "image/png",
                "size_bytes": 500,
                "entity_type": "meal",
                "entity_id": meal_id,
            },
        )
    )
    assert response.status_code == 201

    list_response = asyncio.run(
        api_request("GET", f"/api/media?entity_type=meal&entity_ids={meal_id}")
    )
    assert len(list_response.json()) == 1


def test_private_measurement_media_requires_ownership_to_view() -> None:
    make_team(ATHLETE_A.id, extra_member_id=ATHLETE_B.id)
    measurement_id = make_measurement(ATHLETE_A.id, visibility="private")
    as_user(ATHLETE_A)
    asyncio.run(
        api_request(
            "POST",
            "/api/media/upload-intent",
            {
                "purpose": "measurement",
                "mime_type": "image/jpeg",
                "size_bytes": 500,
                "entity_type": "measurement",
                "entity_id": measurement_id,
            },
        )
    )

    as_user(ATHLETE_B)
    list_response = asyncio.run(
        api_request("GET", f"/api/media?entity_type=measurement&entity_ids={measurement_id}")
    )
    assert list_response.json() == []

    as_user(ATHLETE_A)
    list_response = asyncio.run(
        api_request("GET", f"/api/media?entity_type=measurement&entity_ids={measurement_id}")
    )
    assert len(list_response.json()) == 1


def test_only_owner_can_delete_media() -> None:
    make_team(ATHLETE_A.id, extra_member_id=ATHLETE_B.id)
    as_user(ATHLETE_A)
    create_response = asyncio.run(api_request("POST", "/api/media/upload-intent", UPLOAD_PAYLOAD))
    media_id = create_response.json()["media_asset"]["id"]

    as_user(ATHLETE_B)
    delete_response = asyncio.run(api_request("DELETE", f"/api/media/{media_id}"))
    assert delete_response.status_code == 404

    as_user(ATHLETE_A)
    delete_response = asyncio.run(api_request("DELETE", f"/api/media/{media_id}"))
    assert delete_response.status_code == 204
