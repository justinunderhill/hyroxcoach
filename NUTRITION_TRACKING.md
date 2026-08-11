# Nutrition Tracking — HYROX Coach

## Purpose
Nutrition logging supports daily calorie and macro tracking without turning the product into a clinical nutrition application.

## Daily targets
Each athlete may optionally configure:
- calories
- protein in grams
- carbohydrates in grams
- fat in grams

Targets should be effective-dated so historical comparisons remain correct.

## Meal entry
Each meal may contain date/time, meal type, description, calories, protein_g, carbs_g, fat_g, notes, visibility and photo.

## Daily nutrition dashboard
Show:
- calories consumed / target
- protein consumed / target
- carbs consumed / target
- fat consumed / target
- remaining calories
- remaining macros
- meal list

Canonical values are deterministic sums from confirmed meal records.
```text
daily_calories = SUM(meal.calories)
daily_protein = SUM(meal.protein_g)
daily_carbs = SUM(meal.carbs_g)
daily_fat = SUM(meal.fat_g)
```

Missing nutrition values remain missing rather than being invented.

## Macro validation
For informational validation:
```text
protein kcal = protein_g * 4
carb kcal = carbs_g * 4
fat kcal = fat_g * 9
```
Do not require exact equality between macro-derived and entered calorie totals.

## Photo-assisted meal logging
AI may suggest foods visible, likely portions, calorie range and macro range. The user must confirm or edit before estimates are included in canonical daily totals. Store `nutrition_is_estimated`.

## Shared team view
Meals marked `team` may appear in the shared feed. Private nutrition targets and private meals must remain private.

## AI coach
The coach may discuss protein consistency, logging completeness, fuelling around high training load and consistency against the athlete's own configured targets. It must not present meal-photo estimates as exact or prescribe unsafe restriction.
