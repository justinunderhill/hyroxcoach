from datetime import UTC, datetime, timedelta

from api.services.analytics import (
    ExercisePerformanceSample,
    PersonalBest,
    WorkoutSample,
    active_days_in_window,
    category_coverage,
    exercise_progression,
    joint_session_count,
    pace_seconds_per_km,
    personal_bests,
    race_demand_coverage,
    running_summary,
    running_summary_by_context,
    sessions_in_window,
    simulation_history,
    station_metric_history,
    team_station_comparison,
)

NOW = datetime(2026, 8, 12, 12, 0, tzinfo=UTC)


def sample(
    days_ago: float,
    distance_km: float | None = None,
    duration_minutes: int | None = None,
    categories: tuple[str, ...] = (),
    workout_id: str | None = None,
    is_simulation: bool = False,
    paired_workout_id: str | None = None,
) -> WorkoutSample:
    return WorkoutSample(
        id=workout_id or f"w-{days_ago}",
        occurred_at=NOW - timedelta(days=days_ago),
        distance_km=distance_km,
        duration_minutes=duration_minutes,
        category_slugs=categories,
        is_simulation=is_simulation,
        paired_workout_id=paired_workout_id,
    )


def exercise_sample(
    days_ago: float,
    exercise_key: str = "back_squat",
    exercise_name: str = "Back Squat",
    load_kg: float | None = None,
    reps: int | None = None,
    duration_seconds: int | None = None,
    distance_m: float | None = None,
    workout_id: str = "w-1",
    sequence_no: int = 1,
    notes: str | None = None,
) -> ExercisePerformanceSample:
    return ExercisePerformanceSample(
        id=f"perf-{exercise_key}-{days_ago}",
        workout_id=workout_id,
        occurred_at=NOW - timedelta(days=days_ago),
        exercise_key=exercise_key,
        exercise_name=exercise_name,
        sequence_no=sequence_no,
        load_kg=load_kg,
        reps=reps,
        duration_seconds=duration_seconds,
        distance_m=distance_m,
        notes=notes,
    )


def test_pace_seconds_per_km_handles_missing_values() -> None:
    assert pace_seconds_per_km(None, 5.0) is None
    assert pace_seconds_per_km(30, None) is None
    assert pace_seconds_per_km(30, 5.0) == 360.0


def test_sessions_in_window_excludes_older_workouts() -> None:
    samples = [sample(1), sample(6), sample(8), sample(14)]
    assert sessions_in_window(samples, NOW, days=7) == 2


def test_active_days_in_window_counts_distinct_dates() -> None:
    samples = [sample(1), sample(1.2), sample(2)]
    assert active_days_in_window(samples, NOW, days=7) == 2


def test_category_coverage_zero_fills_untouched_categories() -> None:
    samples = [sample(1, categories=("running",)), sample(2, categories=("running", "strength"))]
    coverage = category_coverage(samples, ["running", "strength", "mobility"], NOW, days=7)
    assert coverage == {"running": 2, "strength": 1, "mobility": 0}


def test_category_coverage_respects_window() -> None:
    samples = [sample(30, categories=("running",))]
    coverage = category_coverage(samples, ["running"], NOW, days=7)
    assert coverage == {"running": 0}


def test_running_summary_weekly_distance_and_average_pace() -> None:
    samples = [
        sample(1, distance_km=5.0, duration_minutes=30),
        sample(3, distance_km=10.0, duration_minutes=55),
        sample(10, distance_km=5.0, duration_minutes=25),
    ]
    summary = running_summary(samples, NOW, range_days=28)
    assert summary.weekly_distance_km == 15.0
    assert summary.avg_pace_seconds_per_km is not None
    assert len(summary.recent) == 3


def test_running_summary_detects_best_5k_within_tolerance() -> None:
    samples = [
        sample(1, distance_km=5.0, duration_minutes=25),
        sample(5, distance_km=4.95, duration_minutes=24),
        sample(10, distance_km=10.0, duration_minutes=50),
    ]
    summary = running_summary(samples, NOW, range_days=28)
    assert summary.best_5k_seconds == 24 * 60


def test_running_summary_best_5k_is_none_without_matching_distance() -> None:
    samples = [sample(1, distance_km=10.0, duration_minutes=50)]
    summary = running_summary(samples, NOW, range_days=28)
    assert summary.best_5k_seconds is None


def test_exercise_progression_groups_by_key_and_detects_improving_load() -> None:
    samples = [
        exercise_sample(20, load_kg=60),
        exercise_sample(10, load_kg=70),
        exercise_sample(1, load_kg=90),
    ]
    progressions = exercise_progression(samples)
    assert len(progressions) == 1
    progression = progressions[0]
    assert progression.exercise_key == "back_squat"
    assert progression.primary_metric == "load_kg"
    assert progression.trend == "improving"
    assert len(progression.points) == 3


def test_exercise_progression_detects_declining_time_trial() -> None:
    samples = [
        exercise_sample(20, exercise_key="sled_push", duration_seconds=60),
        exercise_sample(10, exercise_key="sled_push", duration_seconds=75),
        exercise_sample(1, exercise_key="sled_push", duration_seconds=90),
    ]
    progressions = exercise_progression(samples)
    assert progressions[0].primary_metric == "duration_seconds"
    assert progressions[0].trend == "declining"


def test_exercise_progression_trend_is_none_with_single_point() -> None:
    progressions = exercise_progression([exercise_sample(1, load_kg=60)])
    assert progressions[0].trend is None


def test_exercise_progression_separates_distinct_exercises() -> None:
    samples = [
        exercise_sample(5, exercise_key="back_squat", load_kg=60),
        exercise_sample(5, exercise_key="wall_balls", reps=50),
    ]
    progressions = exercise_progression(samples)
    assert {progression.exercise_key for progression in progressions} == {
        "back_squat",
        "wall_balls",
    }


def test_station_metric_history_excludes_non_station_exercises() -> None:
    samples = [
        exercise_sample(5, exercise_key="sled_push", duration_seconds=60),
        exercise_sample(5, exercise_key="back_squat", load_kg=100),
    ]
    stations = station_metric_history(samples)
    assert len(stations) == 1
    assert stations[0].exercise_key == "sled_push"


def test_personal_bests_prefers_lower_duration_and_flags_current() -> None:
    samples = [
        exercise_sample(20, exercise_key="sled_push", duration_seconds=90),
        exercise_sample(1, exercise_key="sled_push", duration_seconds=65),
    ]
    bests = personal_bests(samples)
    assert len(bests) == 1
    best = bests[0]
    assert best.metric == "duration_seconds"
    assert best.best_value == 65
    assert best.is_current is True


def test_personal_bests_is_current_false_when_pb_is_stale() -> None:
    samples = [
        exercise_sample(20, exercise_key="back_squat", load_kg=100),
        exercise_sample(1, exercise_key="back_squat", load_kg=80),
    ]
    bests = personal_bests(samples)
    best = bests[0]
    assert best.best_value == 100
    assert best.is_current is False


def test_race_demand_coverage_weights_running_double_a_station() -> None:
    coverage = {"running": 3, "skierg": 1, "sled_push": 0, "strength": 5}
    result = race_demand_coverage(coverage)
    # running(2) + skierg(1) trained out of total 10 (running=2 + 8 stations=8).
    assert result.trained_weight_pct == 30.0
    assert "sled_push" in result.untrained_categories
    assert "strength" not in result.untrained_categories  # not a race category at all


def test_race_demand_coverage_full_when_all_race_categories_trained() -> None:
    coverage = {"running": 1, **{station: 1 for station in station_slugs()}}
    result = race_demand_coverage(coverage)
    assert result.trained_weight_pct == 100.0
    assert result.untrained_categories == []


def station_slugs() -> list[str]:
    return [
        "skierg",
        "sled_push",
        "sled_pull",
        "burpee_broad_jumps",
        "row",
        "farmers_carry",
        "sandbag_lunges",
        "wall_balls",
    ]


def test_running_summary_by_context_splits_fresh_and_compromised() -> None:
    samples = [
        sample(2, distance_km=5.0, duration_minutes=25, is_simulation=False),
        sample(3, distance_km=3.0, duration_minutes=20, is_simulation=True),
    ]
    result = running_summary_by_context(samples, NOW, range_days=28)
    assert result.fresh.weekly_distance_km == 5.0
    assert result.compromised.weekly_distance_km == 3.0


def test_simulation_history_includes_station_splits_ordered() -> None:
    sim = sample(1, duration_minutes=75, is_simulation=True, workout_id="sim-1")
    non_sim = sample(2, duration_minutes=30, is_simulation=False, workout_id="w-plain")
    splits = [
        exercise_sample(
            1, exercise_key="wall_balls", workout_id="sim-1", sequence_no=2, notes="tough"
        ),
        exercise_sample(1, exercise_key="skierg", workout_id="sim-1", sequence_no=1),
        exercise_sample(2, exercise_key="skierg", workout_id="w-plain", sequence_no=1),
    ]
    history = simulation_history([sim, non_sim], splits)
    assert len(history) == 1
    record = history[0]
    assert record.workout_id == "sim-1"
    assert [split.exercise_key for split in record.station_splits] == ["skierg", "wall_balls"]
    assert record.station_splits[1].notes == "tough"


def test_team_station_comparison_flags_stronger_athlete_and_shared_gaps() -> None:
    bests_by_user = {
        "athlete-a": [
            PersonalBest(
                exercise_key="sled_push",
                exercise_name="Sled Push",
                metric="duration_seconds",
                best_value=60,
                achieved_at=NOW,
                is_current=True,
            )
        ],
        "athlete-b": [
            PersonalBest(
                exercise_key="sled_push",
                exercise_name="Sled Push",
                metric="duration_seconds",
                best_value=75,
                achieved_at=NOW,
                is_current=True,
            )
        ],
    }
    comparisons, gaps = team_station_comparison(bests_by_user)
    sled_push = next(item for item in comparisons if item.exercise_key == "sled_push")
    assert sled_push.stronger_user_id == "athlete-a"  # lower duration wins
    assert "skierg" in gaps  # neither athlete has any skierg data


def test_joint_session_count_deduplicates_mutual_pairs() -> None:
    samples_by_user = {
        "athlete-a": [sample(1, workout_id="a-1", paired_workout_id="b-1")],
        "athlete-b": [sample(1, workout_id="b-1", paired_workout_id="a-1")],
    }
    assert joint_session_count(samples_by_user, NOW, days=7) == 1
