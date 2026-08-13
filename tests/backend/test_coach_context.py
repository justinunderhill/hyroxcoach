from datetime import date, timedelta

from api.services.analytics import RunningSummary
from api.services.coach_context import (
    NutritionContextInputs,
    PeriodInfo,
    TargetEventInfo,
    TeamAthleteSummaryInputs,
    TeamContextInputs,
    assemble_athlete_context,
    assemble_team_context,
)

EMPTY_RUNNING = RunningSummary(
    weekly_distance_km=0, avg_pace_seconds_per_km=None, recent=[], best_5k_seconds=None
)


def _base_athlete_context(**overrides):
    defaults = dict(
        display_name="Justin",
        baseline_5k_seconds=None,
        period=PeriodInfo(scope="weekly", start=date(2026, 8, 14), end=date(2026, 8, 20)),
        target_event=None,
        recent_workouts=[],
        weekly_sessions=0,
        weekly_active_days=0,
        category_coverage_counts={"running": 0, "strength": 0},
        running=EMPTY_RUNNING,
        station_progressions=[],
        strength_progressions=[],
        personal_bests=[],
    )
    defaults.update(overrides)
    return assemble_athlete_context(**defaults)


def test_no_history_yields_data_quality_notes() -> None:
    context = _base_athlete_context()
    notes = context["data_quality"]["notes"]
    assert "No workouts logged in the last 7 days." in notes
    assert "No target event configured yet." in notes
    assert "Not enough exercise history yet to detect personal bests." in notes


def test_neglected_categories_are_zero_count_slugs() -> None:
    context = _base_athlete_context(category_coverage_counts={"running": 2, "strength": 0})
    assert context["weekly_metrics"]["neglected_categories"] == ["strength"]


def test_target_event_countdown_is_passed_through() -> None:
    target = TargetEventInfo(
        name="HYROX Doubles London",
        event_date=date(2026, 11, 1),
        days_until_event=73,
        division="Open",
    )
    context = _base_athlete_context(target_event=target)
    assert context["target_event"] == {
        "name": "HYROX Doubles London",
        "event_date": "2026-11-01",
        "days_until_event": 73,
        "division": "Open",
        "is_taper_week": False,
    }
    assert "No target event configured yet." not in context["data_quality"]["notes"]


def test_target_event_is_taper_week_within_seven_days() -> None:
    target = TargetEventInfo(
        name="HYROX Doubles London",
        event_date=date(2026, 11, 1),
        days_until_event=7,
        division="Open",
    )
    assert target.is_taper_week is True

    past_target = TargetEventInfo(
        name="HYROX Doubles London",
        event_date=date(2026, 11, 1),
        days_until_event=-1,
        division="Open",
    )
    assert past_target.is_taper_week is False


def test_optional_sections_are_none_when_not_supplied() -> None:
    context = _base_athlete_context()
    assert context["meal_metrics"] is None
    assert context["steps_metrics"] is None
    assert context["measurement_trends"] is None
    assert context["cindy_metrics"] is None


def test_partial_nutrition_logging_produces_a_partial_data_note() -> None:
    nutrition = NutritionContextInputs(
        days_logged=3, days_in_range=7, avg_calories=2100, calories_target=2400, estimated_share=0.2
    )
    context = _base_athlete_context(nutrition=nutrition)
    notes = context["data_quality"]["notes"]
    assert any("Nutrition logged on 3 of 7" in note for note in notes)
    assert context["meal_metrics"]["avg_calories"] == 2100


def test_team_context_flags_single_active_athlete() -> None:
    inputs = TeamContextInputs(
        period=PeriodInfo(scope="team_weekly", start=date(2026, 8, 14), end=date(2026, 8, 20)),
        target_event=None,
        athletes=[
            TeamAthleteSummaryInputs(
                display_name="Justin",
                weekly_sessions=3,
                running=EMPTY_RUNNING,
                category_coverage_counts={"running": 3},
            )
        ],
        combined_category_coverage={"running": 3, "strength": 0},
    )
    context = assemble_team_context(inputs)
    assert context["neglected_categories"] == ["strength"]
    notes = context["data_quality"]["notes"]
    assert "Only one athlete has team-visible activity this period." in notes
    assert len(context["athletes"]) == 1


def test_team_context_with_no_athletes_flags_no_shared_activity() -> None:
    inputs = TeamContextInputs(
        period=PeriodInfo(scope="team_weekly", start=date(2026, 8, 14), end=date(2026, 8, 20)),
        target_event=None,
        athletes=[],
        combined_category_coverage={},
    )
    context = assemble_team_context(inputs)
    assert "No shared team-visible workouts logged yet." in context["data_quality"]["notes"]


def test_context_is_json_serializable_with_timedelta_free_dates() -> None:
    import json

    context = _base_athlete_context(
        target_event=TargetEventInfo(
            name="Race",
            event_date=date.today() + timedelta(days=10),
            days_until_event=10,
            division=None,
        )
    )
    json.dumps(context, sort_keys=True, default=str)
