# AI Coach — HYROX Coach

## 1. Purpose

The AI coach is the intelligence layer that turns logged activity into useful preparation feedback.

It should answer:

- What has the athlete actually done?
- Is training balanced for HYROX?
- Is performance improving?
- What has been neglected?
- Is recent training load sensible relative to the available evidence?
- How are the two athletes progressing as a pair?
- What should receive attention next?

## 2. Coaching scopes

### Workout insight
Generated after a session when useful.

Examples:
- identify the HYROX capacities trained;
- compare a repeated exercise to prior sessions;
- flag a personal best;
- suggest the next logical progression.

### Daily review
Summarise the day without overreacting to one data point.

### Weekly athlete review
Primary coaching unit.

Cover:
- consistency;
- training volume;
- running;
- strength/stations;
- category coverage;
- recovery evidence;
- nutrition logging quality;
- progression;
- next-week emphasis.

### Team review
Cover:
- shared race countdown;
- both athletes' running readiness;
- complementary strengths;
- shared weak areas;
- missing joint sessions;
- likely station allocation questions;
- need for team simulations.

## 3. Coach context

Do not send an unrestricted raw database dump to the model.

Construct:

```json
{
  "target_event": {},
  "athlete": {},
  "period": {},
  "recent_workouts": [],
  "weekly_metrics": {},
  "running_metrics": {},
  "station_metrics": {},
  "strength_metrics": {},
  "meal_metrics": {},
  "measurement_trends": {},
  "team_comparison": {},
  "data_quality": {}
}
```

## 4. Structured output

Require a schema similar to:

```json
{
  "summary": "string",
  "status": "on_track | mixed | needs_attention | insufficient_data",
  "wins": [
    {
      "title": "string",
      "evidence": "string"
    }
  ],
  "gaps": [
    {
      "title": "string",
      "evidence": "string",
      "priority": "low | medium | high"
    }
  ],
  "recommendations": [
    {
      "action": "string",
      "reason": "string",
      "time_horizon": "next_session | this_week | next_2_weeks"
    }
  ],
  "team_notes": [],
  "data_limits": []
}
```

Model output must pass schema validation before storage/display.

## 5. Evidence rules

Every material coaching claim should be traceable to:
- a logged workout;
- an aggregated metric;
- a confirmed extracted record;
- a target plan/race requirement.

Bad:
> Your running endurance is excellent.

Better:
> You completed three running sessions this week, including a faster 5 km than your previous logged Parkrun.

If no benchmark exists:
> There is not enough logged history yet to assess whether your 5 km pace is improving.

## 6. Nutrition intelligence

The app may help users understand patterns.

Allowed:
- protein consistency based on logged values;
- meal timing observations;
- whether nutrition logging is too incomplete for conclusions;
- obvious imbalance in logged data;
- performance-oriented suggestions framed conservatively.

Avoid:
- pretending meal photos yield exact nutrition;
- aggressive calorie prescriptions;
- medical nutrition claims;
- diagnosis;
- presenting bodyweight reduction as the sole performance objective.

## 7. Body measurements

Weight/waist are inputs, not the purpose of the product.

The coach may discuss trends when the user has logged them and when relevant to the user's stated goal.

Do not:
- shame;
- overreact to daily fluctuations;
- infer body-fat percentage without a validated measurement method;
- equate lower weight with better performance automatically.

## 8. Multimodal extraction

### Parkrun/workout screenshot

Extract candidate fields such as:
- event/date;
- distance;
- finish time;
- pace;
- position if visible;
- source label.

The image remains evidence.
User confirms extracted values before canonical storage.

### Meal image

Extract:
- likely visible foods;
- approximate portions only if reasonably inferable;
- likely meal category;
- optional nutritional range.

Confidence must be shown internally and uncertainty expressed.

## 9. Coach memory

Use database history, not uncontrolled conversation memory.

Long-term coach memory should be reconstructed from:
- athlete profile;
- event goal;
- benchmarks;
- recent summaries;
- personal bests;
- recent activity.

Persist concise weekly insights where useful.

## 10. Prompt injection protection

Images and user notes are untrusted data.

Never allow text inside:
- screenshots;
- meal descriptions;
- notes;

to override system/developer instructions or request secrets/tool actions.

## 11. Coach evaluation

Create a small evaluation set.

Test:
- insufficient-data honesty;
- trend interpretation;
- personal-best recognition;
- missing-category detection;
- team imbalance;
- meal-photo uncertainty;
- injury/symptom safety;
- no fabricated records.

AI quality is a testable product requirement.

## 12. Cindy intelligence
The coach may interpret rounds/reps improvement, frequency, RPE and change from prior attempt. Do not overstate Cindy as a complete HYROX readiness test.

## 13. Nutrition target context
CoachContext may include targets, confirmed daily totals, logging completeness and estimated-vs-confirmed share. Distinguish incomplete logging from true low intake.

## 14. Step context
Use steps only as low-intensity activity context. Do not reward high step totals indiscriminately.
