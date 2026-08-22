from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


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


class Team(Base):
    __tablename__ = "teams"
    __table_args__ = (Index("ix_teams_created_by", "created_by"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120))
    created_by: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TeamMembership(Base):
    __tablename__ = "team_memberships"
    __table_args__ = (
        CheckConstraint("role IN ('owner', 'athlete')", name="ck_team_memberships_role"),
        CheckConstraint(
            "status IN ('invited', 'active', 'left')", name="ck_team_memberships_status"
        ),
        Index("ix_team_memberships_user_id", "user_id"),
        Index("ix_team_memberships_team_id", "team_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    team_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("teams.id", ondelete="CASCADE"))
    user_id: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), default="active")
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class GoalEvent(Base):
    __tablename__ = "goal_events"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('hyrox_singles', 'hyrox_doubles')", name="ck_goal_events_event_type"
        ),
        UniqueConstraint("team_id", name="uq_goal_events_team_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    team_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("teams.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120))
    event_type: Mapped[str] = mapped_column(String(24), default="hyrox_doubles")
    event_date: Mapped[date] = mapped_column(Date)
    division: Mapped[str | None] = mapped_column(String(80), nullable=True)
    location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    preparation_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    event_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON().with_variant(postgresql.JSONB, "postgresql"), default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TeamInvite(Base):
    __tablename__ = "team_invites"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_team_invites_token_hash"),
        Index("ix_team_invites_team_id", "team_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    team_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("teams.id", ondelete="CASCADE"))
    invited_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    token_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class WorkoutCategory(Base):
    __tablename__ = "workout_categories"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    category_group: Mapped[str] = mapped_column(String(32))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Workout(Base):
    __tablename__ = "workouts"
    __table_args__ = (
        CheckConstraint(
            "duration_minutes IS NULL OR duration_minutes > 0",
            name="ck_workouts_duration_positive",
        ),
        CheckConstraint(
            "distance_km IS NULL OR distance_km > 0", name="ck_workouts_distance_positive"
        ),
        CheckConstraint("rpe IS NULL OR (rpe BETWEEN 1 AND 10)", name="ck_workouts_rpe_range"),
        CheckConstraint("visibility IN ('team', 'private')", name="ck_workouts_visibility"),
        CheckConstraint("source IN ('manual', 'image', 'integration')", name="ck_workouts_source"),
        Index("ix_workouts_user_occurred", "user_id", "occurred_at"),
        Index("ix_workouts_team_occurred", "team_id", "occurred_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String(255))
    team_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("teams.id", ondelete="RESTRICT"))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    title: Mapped[str] = mapped_column(String(120))
    activity_type: Mapped[str] = mapped_column(String(60))
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    distance_km: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    rpe: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[str] = mapped_column(String(16), default="private")
    source: Mapped[str] = mapped_column(String(16), default="manual")
    is_simulation: Mapped[bool] = mapped_column(Boolean, default=False)
    paired_workout_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("workouts.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    performances: Mapped[list["ExercisePerformance"]] = relationship(
        order_by="ExercisePerformance.sequence_no", cascade="all, delete-orphan"
    )


class WorkoutCategoryLink(Base):
    __tablename__ = "workout_category_links"

    workout_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("workouts.id", ondelete="CASCADE"), primary_key=True
    )
    category_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("workout_categories.id", ondelete="RESTRICT"), primary_key=True
    )


class ExercisePerformance(Base):
    __tablename__ = "exercise_performances"
    __table_args__ = (
        CheckConstraint(
            "rpe IS NULL OR (rpe BETWEEN 1 AND 10)", name="ck_exercise_performances_rpe_range"
        ),
        Index("ix_exercise_performances_workout_sequence", "workout_id", "sequence_no"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    workout_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("workouts.id", ondelete="CASCADE"))
    exercise_name: Mapped[str] = mapped_column(String(120))
    normalized_exercise_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    sequence_no: Mapped[int] = mapped_column(Integer, default=1)
    sets: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    load_kg: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    distance_m: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pace_seconds_per_km: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    calories: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rpe: Mapped[int | None] = mapped_column(Integer, nullable=True)
    performance_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON().with_variant(postgresql.JSONB, "postgresql"), default=dict
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class Meal(Base):
    __tablename__ = "meals"
    __table_args__ = (
        CheckConstraint("calories IS NULL OR calories >= 0", name="ck_meals_calories_positive"),
        CheckConstraint("protein_g IS NULL OR protein_g >= 0", name="ck_meals_protein_positive"),
        CheckConstraint("carbs_g IS NULL OR carbs_g >= 0", name="ck_meals_carbs_positive"),
        CheckConstraint("fat_g IS NULL OR fat_g >= 0", name="ck_meals_fat_positive"),
        CheckConstraint("visibility IN ('team', 'private')", name="ck_meals_visibility"),
        CheckConstraint("source IN ('manual', 'image')", name="ck_meals_source"),
        Index("ix_meals_user_occurred", "user_id", "occurred_at"),
        Index("ix_meals_team_occurred", "team_id", "occurred_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String(255))
    team_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("teams.id", ondelete="RESTRICT"))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    meal_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    description: Mapped[str] = mapped_column(String(500))
    calories: Mapped[int | None] = mapped_column(Integer, nullable=True)
    protein_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 1), nullable=True)
    carbs_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 1), nullable=True)
    fat_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 1), nullable=True)
    nutrition_is_estimated: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[str] = mapped_column(String(16), default="private")
    source: Mapped[str] = mapped_column(String(16), default="manual")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class NutritionTarget(Base):
    __tablename__ = "nutrition_targets"
    __table_args__ = (
        CheckConstraint(
            "calories_target IS NOT NULL OR protein_g_target IS NOT NULL "
            "OR carbs_g_target IS NOT NULL OR fat_g_target IS NOT NULL",
            name="ck_nutrition_targets_value_present",
        ),
        CheckConstraint(
            "calories_target IS NULL OR calories_target >= 0",
            name="ck_nutrition_targets_calories_positive",
        ),
        CheckConstraint(
            "protein_g_target IS NULL OR protein_g_target >= 0",
            name="ck_nutrition_targets_protein_positive",
        ),
        CheckConstraint(
            "carbs_g_target IS NULL OR carbs_g_target >= 0",
            name="ck_nutrition_targets_carbs_positive",
        ),
        CheckConstraint(
            "fat_g_target IS NULL OR fat_g_target >= 0", name="ck_nutrition_targets_fat_positive"
        ),
        Index("ix_nutrition_targets_user_effective", "user_id", "effective_from"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String(255))
    effective_from: Mapped[date] = mapped_column(Date)
    calories_target: Mapped[int | None] = mapped_column(Integer, nullable=True)
    protein_g_target: Mapped[Decimal | None] = mapped_column(Numeric(6, 1), nullable=True)
    carbs_g_target: Mapped[Decimal | None] = mapped_column(Numeric(6, 1), nullable=True)
    fat_g_target: Mapped[Decimal | None] = mapped_column(Numeric(6, 1), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class DailyStep(Base):
    __tablename__ = "daily_steps"
    __table_args__ = (
        CheckConstraint("steps >= 0", name="ck_daily_steps_steps_positive"),
        CheckConstraint(
            "source IN ('manual', 'health_connect', 'apple_health', 'other_import')",
            name="ck_daily_steps_source",
        ),
        CheckConstraint("visibility IN ('team', 'private')", name="ck_daily_steps_visibility"),
        Index("ix_daily_steps_user_date", "user_id", "date"),
        UniqueConstraint("user_id", "date", name="uq_daily_steps_user_date"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String(255))
    date: Mapped[date] = mapped_column(Date)
    steps: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(20), default="manual")
    visibility: Mapped[str] = mapped_column(String(16), default="private")
    step_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON().with_variant(postgresql.JSONB, "postgresql"), default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class MediaAsset(Base):
    __tablename__ = "media_assets"
    __table_args__ = (
        CheckConstraint("size_bytes > 0", name="ck_media_assets_size_positive"),
        CheckConstraint(
            "purpose IN ('workout_evidence', 'meal_photo', 'measurement', 'other')",
            name="ck_media_assets_purpose",
        ),
        CheckConstraint("visibility IN ('team', 'private')", name="ck_media_assets_visibility"),
        Index("ix_media_assets_user_id", "user_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String(255))
    team_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True
    )
    storage_path: Mapped[str] = mapped_column(Text, unique=True)
    mime_type: Mapped[str] = mapped_column(String(80))
    size_bytes: Mapped[int] = mapped_column(Integer)
    purpose: Mapped[str] = mapped_column(String(24))
    visibility: Mapped[str] = mapped_column(String(16), default="private")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class MediaLink(Base):
    __tablename__ = "media_links"
    __table_args__ = (
        CheckConstraint(
            "entity_type IN ('workout', 'meal', 'measurement')",
            name="ck_media_links_entity_type",
        ),
        UniqueConstraint(
            "media_asset_id", "entity_type", "entity_id", name="uq_media_links_asset_entity"
        ),
        Index("ix_media_links_entity", "entity_type", "entity_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    media_asset_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("media_assets.id", ondelete="CASCADE")
    )
    entity_type: Mapped[str] = mapped_column(String(20))
    entity_id: Mapped[UUID] = mapped_column(Uuid)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ExtractionResult(Base):
    __tablename__ = "extraction_results"
    __table_args__ = (
        CheckConstraint(
            "extraction_type IN ('workout', 'meal')", name="ck_extraction_results_type"
        ),
        CheckConstraint("status IN ('succeeded', 'failed')", name="ck_extraction_results_status"),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_extraction_results_confidence_range",
        ),
        Index("ix_extraction_results_media_asset_id", "media_asset_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    media_asset_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("media_assets.id", ondelete="CASCADE")
    )
    extraction_type: Mapped[str] = mapped_column(String(16))
    model_name: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(16))
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    extracted_data: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(postgresql.JSONB, "postgresql"), default=dict
    )
    user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    confirmed_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(postgresql.JSONB, "postgresql"), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CindyResult(Base):
    __tablename__ = "cindy_results"
    __table_args__ = (
        CheckConstraint("full_rounds >= 0", name="ck_cindy_results_full_rounds_positive"),
        CheckConstraint("extra_pullups >= 0", name="ck_cindy_results_extra_pullups_positive"),
        CheckConstraint("extra_pushups >= 0", name="ck_cindy_results_extra_pushups_positive"),
        CheckConstraint("extra_squats >= 0", name="ck_cindy_results_extra_squats_positive"),
        CheckConstraint("total_reps >= 0", name="ck_cindy_results_total_reps_positive"),
        CheckConstraint(
            "total_seconds > 0 AND total_seconds <= 1200", name="ck_cindy_results_total_seconds"
        ),
        CheckConstraint(
            "calories_burned IS NULL OR calories_burned >= 0",
            name="ck_cindy_results_calories_positive",
        ),
        CheckConstraint(
            "calorie_source IS NULL OR calorie_source IN ('external', 'estimated')",
            name="ck_cindy_results_calorie_source",
        ),
        Index("ix_cindy_results_user_id", "user_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    workout_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("workouts.id", ondelete="CASCADE"), unique=True
    )
    user_id: Mapped[str] = mapped_column(String(255))
    full_rounds: Mapped[int] = mapped_column(Integer)
    extra_pullups: Mapped[int] = mapped_column(Integer, default=0)
    extra_pushups: Mapped[int] = mapped_column(Integer, default=0)
    extra_squats: Mapped[int] = mapped_column(Integer, default=0)
    total_reps: Mapped[int] = mapped_column(Integer)
    total_seconds: Mapped[int] = mapped_column(Integer)
    completed_as_prescribed: Mapped[bool] = mapped_column(Boolean)
    calories_burned: Mapped[int | None] = mapped_column(Integer, nullable=True)
    calorie_source: Mapped[str | None] = mapped_column(String(16), nullable=True)
    calorie_estimation_version: Mapped[str | None] = mapped_column(String(16), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class CoachInsight(Base):
    __tablename__ = "coach_insights"
    __table_args__ = (
        CheckConstraint(
            "scope IN ('workout', 'daily', 'weekly', 'team_weekly')", name="ck_coach_insights_scope"
        ),
        Index("ix_coach_insights_lookup", "scope", "team_id", "user_id", "period_start"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    scope: Mapped[str] = mapped_column(String(16))
    user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    team_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("teams.id", ondelete="CASCADE"))
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_record_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    coach_version: Mapped[str] = mapped_column(String(24))
    model_name: Mapped[str] = mapped_column(String(80))
    insight_json: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(postgresql.JSONB, "postgresql")
    )
    context_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
