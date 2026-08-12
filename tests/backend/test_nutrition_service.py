from datetime import date

from api.services.nutrition import (
    MealMacros,
    NutritionTarget,
    daily_totals,
    remaining_vs_target,
    select_effective_target,
)


def test_daily_totals_sums_non_null_macros() -> None:
    meals = [
        MealMacros(calories=500, protein_g=40, carbs_g=None, fat_g=10),
        MealMacros(calories=None, protein_g=20, carbs_g=30, fat_g=None),
    ]
    totals = daily_totals(meals)
    assert totals.calories == 500
    assert totals.protein_g == 60
    assert totals.carbs_g == 30
    assert totals.fat_g == 10


def test_daily_totals_with_no_meals_is_zero() -> None:
    totals = daily_totals([])
    assert totals.calories == 0
    assert totals.protein_g == 0


def test_select_effective_target_picks_latest_before_or_on_date() -> None:
    targets = [
        NutritionTarget(date(2026, 1, 1), 2000, None, None, None),
        NutritionTarget(date(2026, 6, 1), 2400, None, None, None),
    ]
    effective = select_effective_target(targets, date(2026, 8, 1))
    assert effective is not None
    assert effective.calories_target == 2400


def test_select_effective_target_ignores_future_targets() -> None:
    targets = [NutritionTarget(date(2026, 12, 1), 2400, None, None, None)]
    assert select_effective_target(targets, date(2026, 8, 1)) is None


def test_remaining_vs_target_is_none_without_a_target() -> None:
    totals = daily_totals([MealMacros(calories=500, protein_g=None, carbs_g=None, fat_g=None)])
    remaining = remaining_vs_target(totals, None)
    assert remaining.calories is None


def test_remaining_vs_target_only_fills_configured_macros() -> None:
    totals = daily_totals([MealMacros(calories=500, protein_g=40, carbs_g=None, fat_g=None)])
    target = NutritionTarget(date(2026, 1, 1), 2000, 150, None, None)
    remaining = remaining_vs_target(totals, target)
    assert remaining.calories == 1500
    assert remaining.protein_g == 110
    assert remaining.carbs_g is None
    assert remaining.fat_g is None
