# Cindy Workout — HYROX Coach

## Purpose
Cindy is the only pre-built workout in the MVP. All other workouts remain flexible and are classified using HYROX-relevant categories.

## Standard workout
**20-minute AMRAP**
- 5 pull-ups
- 10 push-ups
- 15 air squats

## Workout screen
Include a 20:00 countdown timer, Start / Pause / Resume / Finish controls, current round counter, optional partial-rep entry, elapsed time, optional RPE, calories burned and notes.

The timer must remain accurate if the screen loses focus. Use timestamps as the source of truth rather than relying only on a visual decrementing timer.

## Round logging
Primary action: `+ ROUND`

Optional partial-rep controls:
- Pull-ups +1
- Push-ups +1
- Squats +1

## Completion result
Store:
- completed_at
- total_seconds
- full_rounds
- extra_pullups
- extra_pushups
- extra_squats
- total_reps
- RPE optional
- calories_burned nullable
- calorie_source
- notes

Formula:
```text
total_reps = (full_rounds * 30) + extra_pullups + extra_pushups + extra_squats
```

## Calories burned
Allow two sources:
1. **External/user-entered value** from a watch or device.
2. **App estimate** using a documented formula based on duration, bodyweight if available and an explicit intensity/MET assumption.

Any app-generated value must be labelled **Estimated calories**.
Store `calorie_source = external | estimated` and `calorie_estimation_version` when estimated.

## Progress tracking
Track latest result, best full rounds, best total reps, change from previous attempt, calories when logged, RPE trend and date history.

Cindy should not be treated as a complete HYROX readiness test.

## Categories
Automatically tag Strength and Functional conditioning. Do not label Cindy as a HYROX simulation.

## Early finish
If stopped before 20 minutes, save the workout with `completed_as_prescribed = false` rather than discarding it.
