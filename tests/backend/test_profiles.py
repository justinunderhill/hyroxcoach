import asyncio
from collections.abc import Generator

from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from api.auth import AuthenticatedUser, get_current_user
from api.database import get_session
from api.main import app
from api.models import AthleteProfile, Base, Measurement

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)


def override_session() -> Generator[Session, None, None]:
    with SessionFactory() as session:
        yield session


def override_user() -> AuthenticatedUser:
    return AuthenticatedUser(id="athlete-a", email="a@example.com")


async def api_request(method: str, path: str, json: dict | None = None) -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.request(method, path, json=json)


def setup_function() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    app.dependency_overrides = {
        get_current_user: override_user,
        get_session: override_session,
    }


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_get_me_has_an_explicit_empty_profile_state() -> None:
    response = asyncio.run(api_request("GET", "/api/me"))

    assert response.status_code == 200
    assert response.json()["profile"] is None


def test_onboarding_creates_profile_and_private_measurement() -> None:
    response = asyncio.run(
        api_request(
            "PATCH",
            "/api/me",
            {
                "display_name": "Athlete A",
                "timezone": "Africa/Johannesburg",
                "baseline_5k_seconds": 1500,
                "training_days": ["tuesday", "saturday"],
                "weight_kg": 82.4,
                "waist_cm": 84.0,
            },
        )
    )

    assert response.status_code == 200
    assert response.json()["profile"]["display_name"] == "Athlete A"
    with SessionFactory() as session:
        measurement = session.scalar(select(Measurement))
        assert measurement is not None
        assert measurement.user_id == "athlete-a"
        assert measurement.visibility == "private"


def test_profile_reads_are_scoped_to_authenticated_owner() -> None:
    with SessionFactory.begin() as session:
        session.add(
            AthleteProfile(
                user_id="athlete-b",
                display_name="Athlete B",
                timezone="Africa/Johannesburg",
            )
        )

    response = asyncio.run(api_request("GET", "/api/me"))

    assert response.status_code == 200
    assert response.json()["profile"] is None
