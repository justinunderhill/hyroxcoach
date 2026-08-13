import asyncio
from collections.abc import Generator
from uuid import uuid4

from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy import create_engine, select
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
                WorkoutCategory(slug="running", name="Running", category_group="running"),
                WorkoutCategory(slug="skierg", name="SkiErg", category_group="hyrox_station"),
            ]
        )


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


def workout_payload(**overrides) -> dict:
    payload = {
        "occurred_at": "2026-08-08T06:00:00+00:00",
        "title": "Parkrun",
        "activity_type": "running",
        "category_slugs": ["running"],
        "duration_minutes": 28,
        "distance_km": 5,
        "rpe": 8,
        "visibility": "private",
        "notes": "Strong finish.",
    }
    payload.update(overrides)
    return payload


def test_create_workout_requires_a_team() -> None:
    as_user(ATHLETE_A)
    response = asyncio.run(api_request("POST", "/api/workouts", workout_payload()))
    assert response.status_code == 422


def test_create_and_fetch_workout() -> None:
    make_team(ATHLETE_A.id)
    as_user(ATHLETE_A)

    create_response = asyncio.run(api_request("POST", "/api/workouts", workout_payload()))
    assert create_response.status_code == 201
    body = create_response.json()
    assert body["title"] == "Parkrun"
    assert body["category_slugs"] == ["running"]
    assert body["user_id"] == ATHLETE_A.id

    get_response = asyncio.run(api_request("GET", f"/api/workouts/{body['id']}"))
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "Parkrun"


def test_unknown_category_slug_is_rejected() -> None:
    make_team(ATHLETE_A.id)
    as_user(ATHLETE_A)

    response = asyncio.run(
        api_request(
            "POST", "/api/workouts", workout_payload(category_slugs=["not-a-real-category"])
        )
    )
    assert response.status_code == 422


def test_private_workouts_are_not_visible_to_teammates() -> None:
    make_team(ATHLETE_A.id, extra_member_id=ATHLETE_B.id)
    as_user(ATHLETE_A)
    create_response = asyncio.run(
        api_request("POST", "/api/workouts", workout_payload(visibility="private"))
    )
    workout_id = create_response.json()["id"]

    as_user(ATHLETE_B)
    get_response = asyncio.run(api_request("GET", f"/api/workouts/{workout_id}"))
    assert get_response.status_code == 404

    list_response = asyncio.run(api_request("GET", "/api/workouts"))
    assert list_response.json() == []


def test_team_visible_workouts_appear_for_teammates() -> None:
    make_team(ATHLETE_A.id, extra_member_id=ATHLETE_B.id)
    as_user(ATHLETE_A)
    create_response = asyncio.run(
        api_request("POST", "/api/workouts", workout_payload(visibility="team"))
    )
    workout_id = create_response.json()["id"]

    as_user(ATHLETE_B)
    get_response = asyncio.run(api_request("GET", f"/api/workouts/{workout_id}"))
    assert get_response.status_code == 200

    list_response = asyncio.run(api_request("GET", "/api/workouts"))
    assert len(list_response.json()) == 1


def test_only_the_owner_can_update_or_delete_a_workout() -> None:
    make_team(ATHLETE_A.id, extra_member_id=ATHLETE_B.id)
    as_user(ATHLETE_A)
    create_response = asyncio.run(
        api_request("POST", "/api/workouts", workout_payload(visibility="team"))
    )
    workout_id = create_response.json()["id"]

    as_user(ATHLETE_B)
    patch_response = asyncio.run(
        api_request("PATCH", f"/api/workouts/{workout_id}", {"title": "Hijacked"})
    )
    assert patch_response.status_code == 404

    delete_response = asyncio.run(api_request("DELETE", f"/api/workouts/{workout_id}"))
    assert delete_response.status_code == 404

    as_user(ATHLETE_A)
    patch_response = asyncio.run(
        api_request("PATCH", f"/api/workouts/{workout_id}", {"title": "Updated title"})
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["title"] == "Updated title"

    with SessionFactory() as session:
        assert session.scalar(select(Workout)).title == "Updated title"


def test_add_exercise_performance_is_owner_only() -> None:
    make_team(ATHLETE_A.id, extra_member_id=ATHLETE_B.id)
    as_user(ATHLETE_A)
    create_response = asyncio.run(
        api_request(
            "POST", "/api/workouts", workout_payload(activity_type="strength", category_slugs=[])
        )
    )
    workout_id = create_response.json()["id"]

    performance_payload = {
        "exercise_name": "SkiErg",
        "sequence_no": 1,
        "distance_m": 1000,
        "duration_seconds": 240,
    }

    as_user(ATHLETE_B)
    forbidden = asyncio.run(
        api_request("POST", f"/api/workouts/{workout_id}/performances", performance_payload)
    )
    assert forbidden.status_code == 404

    as_user(ATHLETE_A)
    created = asyncio.run(
        api_request("POST", f"/api/workouts/{workout_id}/performances", performance_payload)
    )
    assert created.status_code == 201
    assert created.json()["exercise_name"] == "SkiErg"

    detail = asyncio.run(api_request("GET", f"/api/workouts/{workout_id}"))
    assert len(detail.json()["performances"]) == 1


def test_is_simulation_flag_round_trips() -> None:
    make_team(ATHLETE_A.id)
    as_user(ATHLETE_A)
    create_response = asyncio.run(
        api_request("POST", "/api/workouts", workout_payload(is_simulation=True))
    )
    assert create_response.json()["is_simulation"] is True

    default_response = asyncio.run(api_request("POST", "/api/workouts", workout_payload()))
    assert default_response.json()["is_simulation"] is False


def test_paired_workout_id_must_be_a_teammates_team_visible_workout() -> None:
    make_team(ATHLETE_A.id, extra_member_id=ATHLETE_B.id)

    as_user(ATHLETE_B)
    private_partner_workout = asyncio.run(
        api_request("POST", "/api/workouts", workout_payload(visibility="private"))
    ).json()["id"]
    team_partner_workout = asyncio.run(
        api_request("POST", "/api/workouts", workout_payload(visibility="team"))
    ).json()["id"]

    as_user(ATHLETE_A)
    own_workout = asyncio.run(
        api_request("POST", "/api/workouts", workout_payload(visibility="team"))
    ).json()["id"]

    # Cannot pair with a teammate's private workout.
    rejected = asyncio.run(
        api_request(
            "POST",
            "/api/workouts",
            workout_payload(paired_workout_id=private_partner_workout),
        )
    )
    assert rejected.status_code == 422

    # Cannot pair with your own workout.
    rejected_self = asyncio.run(
        api_request("POST", "/api/workouts", workout_payload(paired_workout_id=own_workout))
    )
    assert rejected_self.status_code == 422

    # A teammate's team-visible workout is a valid pairing.
    accepted = asyncio.run(
        api_request(
            "POST",
            "/api/workouts",
            workout_payload(visibility="team", paired_workout_id=team_partner_workout),
        )
    )
    assert accepted.status_code == 201
    assert accepted.json()["paired_workout_id"] == team_partner_workout
