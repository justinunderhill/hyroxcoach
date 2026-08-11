# UX Specification — HYROX Coach

## Design principles

- mobile first;
- fast logging;
- visually calm;
- no bodybuilding-app aesthetic;
- no unnecessary gamification;
- team-first context;
- data should explain itself.

## Main navigation

Recommended bottom navigation on mobile:

1. Dashboard
2. Log
3. Progress
4. Team
5. Coach

Profile/settings through avatar/menu.

## Dashboard

Personal home view.

Top:
- race countdown;
- current-week status;
- latest coach summary.

Then:
- quick log buttons;
- today's/recent activity;
- HYROX category coverage;
- running trend;
- recent progression;
- meals;
- measurements if enabled.

## Quick Log

One prominent action opens:

- Workout
- Meal
- Measurement
- Upload screenshot/photo

### Workout flow

Step 1:
What did you do?

Fields:
- title;
- date/time;
- activity type;
- category tags.

Step 2:
Optional detail:
- duration;
- distance;
- RPE;
- exercise metrics;
- notes;
- photo/screenshot.

Do not make optional performance fields block saving.

## Team view

Header:
- team name;
- event;
- days remaining.

Athlete cards:
- last session;
- weekly sessions;
- running volume;
- selected progress indicator.

Then shared:
- timeline/feed;
- category coverage;
- running comparison;
- station trends;
- joint-session history;
- AI team coach.

## Activity feed

Display:
- athlete;
- activity title;
- categories;
- key metrics;
- timestamp;
- optional media thumbnail.

Meals may appear if shared.

Avoid social-media mechanics like public likes.

## Progress

Filters:
- Running
- HYROX stations
- Strength
- Training consistency
- Measurements

Charts should display actual measurements, not AI-generated scores.

## Coach

Default view:
- current weekly assessment;
- wins;
- gaps;
- recommended actions;
- evidence/data limitations.

Optional chat:
- "How are we tracking?"
- "What should I train tomorrow?"
- "How has my 5 km improved?"
- "Which HYROX stations are we neglecting?"

The backend must inject authorized context.

## Empty states

Use empty states to guide logging.

Example:
"No 5 km benchmark yet. Log a 5 km run or upload a Parkrun result to start tracking your trend."

## Accessibility

- keyboard reachable;
- semantic labels;
- sufficient contrast;
- no information conveyed only by colour;
- appropriate touch targets.

## Cindy screen
Accessible from Quick Log as the only pre-built workout.

Primary layout: large 20:00 timer, current rounds, `+ ROUND`, pause/resume, finish, calories entry/display, post-workout partial reps and RPE.

## Nutrition counter
Dashboard card: calories consumed / target, protein / target, carbs / target and fat / target.

## Steps
Personal dashboard: today, 7-day average and weekly trend. MVP must label manually entered steps appropriately.
