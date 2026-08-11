from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class AthleteProfile(Base):
    __tablename__ = "athlete_profiles"
    __table_args__ = (
        CheckConstraint(
            "baseline_5k_seconds IS NULL OR baseline_5k_seconds > 0",
            name="ck_athlete_profiles_baseline_5k_positive",
        ),
        Index("ix_athlete_profiles_user_id", "user_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String(255), unique=True)
    display_name: Mapped[str] = mapped_column(String(80))
    avatar_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    timezone: Mapped[str] = mapped_column(String(64))
    baseline_5k_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    training_availability: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(postgresql.JSONB, "postgresql"), default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Measurement(Base):
    __tablename__ = "measurements"
    __table_args__ = (
        CheckConstraint(
            "weight_kg IS NOT NULL OR waist_cm IS NOT NULL OR notes IS NOT NULL",
            name="ck_measurements_value_present",
        ),
        CheckConstraint(
            "weight_kg IS NULL OR weight_kg > 0",
            name="ck_measurements_weight_positive",
        ),
        CheckConstraint(
            "waist_cm IS NULL OR waist_cm > 0",
            name="ck_measurements_waist_positive",
        ),
        CheckConstraint(
            "visibility IN ('private', 'team')",
            name="ck_measurements_visibility",
        ),
        Index("ix_measurements_user_occurred", "user_id", "occurred_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    waist_cm: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    resting_hr: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[str] = mapped_column(String(16), default="private")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
