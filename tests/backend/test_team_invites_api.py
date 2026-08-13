import asyncio
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from api.auth import AuthenticatedUser, get_current_user
from api.database import get_session
from api.main import app
from api.models import Base, Team, TeamInvite, TeamMembership
from api.services.invites import hash_token

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)

ATHLETE_A = AuthenticatedUser(id="athlete-a", email="a@example.com")
ATHLETE_B = AuthenticatedUser(id="athlete-b", email="b@example.com")
ATHLETE_C = AuthenticatedUser(id="athlete-c", email="c@example.com")


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


def insert_raw_invite(
    team_id: str,
    token: str,
    created_by: str,
    expires_at: datetime | None = None,
    accepted_at: datetime | None = None,
) -> None:
    with SessionFactory.begin() as session:
        session.add(
            TeamInvite(
                team_id=UUID(team_id),
                token_hash=hash_token(token),
                expires_at=expires_at or (datetime.now(UTC) + timedelta(days=14)),
                accepted_at=accepted_at,
                created_by=created_by,
            )
        )


def test_create_invite_requires_active_membership() -> None:
    team_id = make_team(ATHLETE_A.id)
    as_user(ATHLETE_B)
    response = asyncio.run(
        api_request("POST", f"/api/teams/{team_id}/invites", {"invited_email": None})
    )
    assert response.status_code == 404


def test_create_invite_returns_plaintext_token_once() -> None:
    team_id = make_team(ATHLETE_A.id)
    as_user(ATHLETE_A)
    response = asyncio.run(
        api_request("POST", f"/api/teams/{team_id}/invites", {"invited_email": "b@example.com"})
    )
    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["token"], str) and len(body["token"]) > 20
    assert body["invited_email"] == "b@example.com"
    assert body["accepted_at"] is None

    with SessionFactory() as session:
        stored = session.scalar(select(TeamInvite))
        assert stored.token_hash == hash_token(body["token"])
        assert stored.token_hash != body["token"]


def test_create_invite_rejected_when_team_already_has_two_athletes() -> None:
    team_id = make_team(ATHLETE_A.id, extra_member_id=ATHLETE_B.id)
    as_user(ATHLETE_A)
    response = asyncio.run(
        api_request("POST", f"/api/teams/{team_id}/invites", {"invited_email": None})
    )
    assert response.status_code == 422


def test_accept_invite_creates_membership_and_marks_accepted() -> None:
    team_id = make_team(ATHLETE_A.id)
    as_user(ATHLETE_A)
    created = asyncio.run(
        api_request("POST", f"/api/teams/{team_id}/invites", {"invited_email": None})
    ).json()

    as_user(ATHLETE_B)
    accept_response = asyncio.run(
        api_request("POST", f"/api/team-invites/{created['token']}/accept")
    )
    assert accept_response.status_code == 200
    body = accept_response.json()
    assert body["team_id"] == team_id
    assert body["role"] == "athlete"
    assert body["status"] == "active"

    with SessionFactory() as session:
        membership = session.scalar(
            select(TeamMembership).where(
                TeamMembership.team_id == UUID(team_id), TeamMembership.user_id == ATHLETE_B.id
            )
        )
        assert membership.status == "active"
        invite = session.scalar(select(TeamInvite))
        assert invite.accepted_at is not None


def test_accept_invite_demotes_other_active_memberships() -> None:
    team_id = make_team(ATHLETE_A.id)
    solo_team_id = make_team(ATHLETE_B.id)
    as_user(ATHLETE_A)
    created = asyncio.run(
        api_request("POST", f"/api/teams/{team_id}/invites", {"invited_email": None})
    ).json()

    as_user(ATHLETE_B)
    asyncio.run(api_request("POST", f"/api/team-invites/{created['token']}/accept"))

    with SessionFactory() as session:
        old_membership = session.scalar(
            select(TeamMembership).where(
                TeamMembership.team_id == UUID(solo_team_id),
                TeamMembership.user_id == ATHLETE_B.id,
            )
        )
        assert old_membership.status == "left"


def test_accept_invite_twice_returns_410() -> None:
    team_id = make_team(ATHLETE_A.id)
    as_user(ATHLETE_A)
    created = asyncio.run(
        api_request("POST", f"/api/teams/{team_id}/invites", {"invited_email": None})
    ).json()

    as_user(ATHLETE_B)
    first = asyncio.run(api_request("POST", f"/api/team-invites/{created['token']}/accept"))
    assert first.status_code == 200

    as_user(ATHLETE_C)
    second = asyncio.run(api_request("POST", f"/api/team-invites/{created['token']}/accept"))
    assert second.status_code == 410


def test_accept_expired_invite_returns_410() -> None:
    team_id = make_team(ATHLETE_A.id)
    insert_raw_invite(
        team_id,
        "expired-token",
        ATHLETE_A.id,
        expires_at=datetime.now(UTC) - timedelta(days=1),
    )
    as_user(ATHLETE_B)
    response = asyncio.run(api_request("POST", "/api/team-invites/expired-token/accept"))
    assert response.status_code == 410


def test_accept_invite_rejected_when_team_already_full() -> None:
    team_id = make_team(ATHLETE_A.id, extra_member_id=ATHLETE_B.id)
    insert_raw_invite(team_id, "some-token", ATHLETE_A.id)
    as_user(ATHLETE_C)
    response = asyncio.run(api_request("POST", "/api/team-invites/some-token/accept"))
    assert response.status_code == 422


def test_unknown_token_returns_404() -> None:
    as_user(ATHLETE_A)
    response = asyncio.run(api_request("POST", "/api/team-invites/not-a-real-token/accept"))
    assert response.status_code == 404


def test_get_team_returns_roster_for_members_only() -> None:
    team_id = make_team(ATHLETE_A.id, extra_member_id=ATHLETE_B.id)
    as_user(ATHLETE_A)
    response = asyncio.run(api_request("GET", f"/api/teams/{team_id}"))
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == team_id
    assert {member["user_id"] for member in body["members"]} == {ATHLETE_A.id, ATHLETE_B.id}

    as_user(ATHLETE_C)
    forbidden = asyncio.run(api_request("GET", f"/api/teams/{team_id}"))
    assert forbidden.status_code == 404


def test_list_team_invites_requires_membership() -> None:
    team_id = make_team(ATHLETE_A.id)
    as_user(ATHLETE_A)
    asyncio.run(api_request("POST", f"/api/teams/{team_id}/invites", {"invited_email": None}))

    listed = asyncio.run(api_request("GET", f"/api/teams/{team_id}/invites"))
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    as_user(ATHLETE_C)
    forbidden = asyncio.run(api_request("GET", f"/api/teams/{team_id}/invites"))
    assert forbidden.status_code == 404
