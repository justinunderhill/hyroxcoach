# Product Requirements — HYROX Coach

## 1. Product vision

Create a HYROX coaching application that works equally well for a single athlete training solo (HYROX Singles) and for two athletes training together (HYROX Doubles) — each logs their own preparation independently, and a pair also sees how they are progressing as a team.

The application should behave like a lightweight performance operating system for a HYROX athlete, solo or paired. There is no larger team/squad mode — a team caps at exactly two athletes.

## 2. Primary users

### Athlete
Can:
- sign up/sign in;
- create/edit profile;
- join a team;
- log workouts;
- log meals;
- record body measurements;
- upload screenshots/photos;
- view personal analytics;
- view shared team activity;
- receive coaching feedback.

### Team
A shared logical space containing:
- athletes;
- target HYROX event;
- preparation start/end dates;
- shared dashboard;
- team readiness;
- team coaching insights.

## 3. Authentication and onboarding

### Requirements
- Email/password or magic-link authentication.
- Athlete creates display name and profile.
- A solo team is created automatically for every new athlete — training solo requires no extra setup.
- Team creator can optionally invite one partner via secure invite link/code to upgrade to a Doubles pair (capped at two athletes; no larger team/squad mode).
- Each user can belong to the team after accepting invitation.
- Target event date and competition format (Singles or Doubles) are stored on the team.

### Onboarding questions
Keep onboarding short:
- display name;
- target event;
- race date;
- division;
- optional baseline 5 km time;
- optional baseline bodyweight/waist;
- known training availability.

Do not require sensitive data to use the product.

## 4. Workout logging

### Goal
Logging must work for structured or unstructured training.

### Workout fields
- date/time;
- title;
- activity type;
- one or more HYROX categories;
- duration;
- distance optional;
- perceived effort/RPE optional;
- notes;
- location optional;
- source: manual / image extraction / imported later;
- visibility: team / private;
- media attachments.

### Exercise details
A workout may contain repeatable exercise-performance entries:
- exercise;
- sets;
- reps;
- load;
- distance;
- time;
- pace;
- calories optional if externally measured;
- notes.

Support flexible values because HYROX stations use different units.

### Example workouts
- Parkrun 5 km
- MMA sparring
- Ring strength
- Zone 2 walk
- 6 × 1 km intervals
- Sled session
- HYROX simulation
- Mobility/recovery session

## 5. Meal logging

Meal logging must be lightweight.

### Manual meal fields
- date/time;
- meal type;
- description;
- optional calories;
- optional protein;
- optional carbs;
- optional fats;
- notes;
- visibility;
- photo.

### Photo-assisted meal logging
User can upload a meal image.

AI may:
- describe visible food;
- suggest likely components;
- provide approximate nutritional ranges only when useful;
- clearly label estimates;
- ask the user to confirm/edit.

The system must not claim precise calories from a photograph.

## 6. Measurements

Personal profile supports time-series measurements:
- bodyweight;
- waist circumference;
- optional resting heart rate;
- optional custom notes.

Measurements are private by default but may be shared with the team if the user opts in.

## 7. Screenshot/media uploads

Supported examples:
- Parkrun result screenshot;
- Strava/watch result;
- treadmill display;
- workout whiteboard;
- meal photo;
- progress image if later enabled.

### Requirements
- private storage bucket;
- signed URLs;
- attachment metadata;
- AI extraction status;
- extracted JSON;
- extraction confidence;
- manual confirmation.

## 8. Personal dashboard

Must show:
- current training week;
- recent workouts;
- recent meals;
- measurement trend;
- running trend;
- exercise progression;
- HYROX category coverage;
- recent coach feedback;
- upcoming planned emphasis.

## 9. Shared team dashboard

Must show both athletes without requiring account switching.

### Dashboard sections
- days until race;
- latest activity from each athlete;
- weekly training comparison;
- combined category coverage;
- running progress;
- key exercise/station trends;
- recent meals if shared;
- readiness gaps;
- AI team coach summary;
- consistency streak/trend;
- upcoming focus.

Avoid turning it into a competition between brothers unless the metric is genuinely useful.

## 10. Progress analytics

### Running
Track:
- 5 km best and recent time;
- 1 km performance;
- weekly distance;
- interval pace where recorded;
- training frequency.

### HYROX stations
Track performance where data exists:
- SkiErg;
- Sled Push;
- Sled Pull;
- Burpee Broad Jumps;
- Row;
- Farmers Carry;
- Sandbag Lunges;
- Wall Balls.

### Strength
Track repeated exercises over time:
- load;
- reps;
- estimated volume where meaningful;
- personal bests.

### Consistency
Track:
- sessions/week;
- active days;
- planned-category coverage;
- recent inactivity.

Do not invent a readiness score until its formula is documented.

## 11. AI coach

See `AI_COACH.md`.

The coach should operate at:
- workout level;
- daily level;
- weekly level;
- team level.

## 12. Notifications — later phase

Possible future features:
- missed training prompts;
- weekly review;
- race countdown;
- partner activity;
- coach recommendation.

Not required for initial MVP.

## 13. Future integrations

Do not include in MVP unless easy:
- Strava;
- Garmin;
- Apple Health;
- Google Health Connect;
- Parkrun API/data import;
- wearable recovery metrics.

Design identifiers/source fields so integrations can be added later.

## 14. Cindy — pre-built workout
Cindy is the only predefined workout in the MVP.

Standard: 20-minute AMRAP of 5 pull-ups, 10 push-ups and 15 air squats.

Requirements: built-in timer, pause/resume, round counter, partial-rep capture, optional RPE, calories burned with provenance, history and personal-best tracking. See `CINDY_WORKOUT.md`.

## 15. Daily calorie and macro counter
Athletes may configure targets for calories, protein, carbohydrates and fats. The daily nutrition view totals confirmed meal records and displays consumed vs target. See `NUTRITION_TRACKING.md`.

## 16. Steps
MVP: manual daily steps, personal trend, weekly average and optional team visibility.

Future: native Health Connect / HealthKit integration.

Do not build a raw browser accelerometer pedometer as the primary source. See `STEPS_TRACKING.md`.
