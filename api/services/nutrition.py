"""Deterministic nutrition aggregators.

Canonical daily totals are sums of confirmed meal records; targets are
selected by effective date. Missing values remain missing rather than
being invented, per NUTRITION_TRACKING.md.
"""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class MealMacros:
    calories: int | None
    protein_g: float | None
    carbs_g: float | None
    fat_g: float | None


@dataclass(frozen=True)
class DailyTotals:
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float


def daily_totals(meals: list[MealMacros]) -> DailyTotals:
    return DailyTotals(
        calories=sum(meal.calories or 0 for meal in meals),
        protein_g=round(sum(meal.protein_g or 0 for meal in meals), 1),
        carbs_g=round(sum(meal.carbs_g or 0 for meal in meals), 1),
        fat_g=round(sum(meal.fat_g or 0 for meal in meals), 1),
    )


@dataclass(frozen=True)
class NutritionTarget:
    effective_from: date
    calories_target: int | None
    protein_g_target: float | None
    carbs_g_target: float | None
    fat_g_target: float | None


@dataclass(frozen=True)
class Remaining:
    calories: float | None
    protein_g: float | None
    carbs_g: float | None
    fat_g: float | None


def select_effective_target(
    targets: list[NutritionTarget], on_date: date
) -> NutritionTarget | None:
    eligible = [target for target in targets if target.effective_from <= on_date]
    if not eligible:
        return None
    return max(eligible, key=lambda target: target.effective_from)


def remaining_vs_target(totals: DailyTotals, target: NutritionTarget | None) -> Remaining:
    if target is None:
        return Remaining(calories=None, protein_g=None, carbs_g=None, fat_g=None)
    calories_remaining = (
        target.calories_target - totals.calories if target.calories_target is not None else None
    )
    protein_remaining = (
        round(target.protein_g_target - totals.protein_g, 1)
        if target.protein_g_target is not None
        else None
    )
    carbs_remaining = (
        round(target.carbs_g_target - totals.carbs_g, 1)
        if target.carbs_g_target is not None
        else None
    )
    fat_remaining = (
        round(target.fat_g_target - totals.fat_g, 1) if target.fat_g_target is not None else None
    )
    return Remaining(
        calories=calories_remaining,
        protein_g=protein_remaining,
        carbs_g=carbs_remaining,
        fat_g=fat_remaining,
    )
