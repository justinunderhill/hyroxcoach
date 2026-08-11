# Step Tracking — HYROX Coach

## Decision
Support steps in the product data model now.

Do **not** implement a browser accelerometer pedometer as the canonical source. Browser motion APIs expose acceleration and rotation, not an authoritative system step total. A foreground PWA pedometer would be device-dependent and unreliable.

## MVP
Support:
- manual daily step entry
- optional source
- optional notes
- personal dashboard display
- weekly total
- 7-day average
- daily trend
- optional team visibility

Fields:
- date
- steps
- source (`manual`, `health_connect`, `apple_health`, `other_import`)
- visibility
- created_at
- updated_at

## Android future integration
Preferred path: **Health Connect**. Health Connect exposes step data through the Steps data type and requires explicit health permissions in an Android app/native integration.

Potential future flow:
```text
HYROX Coach web product
    |
Android native shell/app
    |
Health Connect
    |
sync endpoint
    |
HYROX Coach database
```

## Apple future integration
Treat Apple Health / HealthKit as a native-platform integration. Do not promise direct browser access.

## Analytics
Track steps today, 7-day average, weekly total and week-over-week trend.

Steps are context, not a HYROX readiness score by themselves.

## AI coach
Steps may inform general activity level, recovery/load context and unusually large activity changes. More steps should not automatically be treated as better, especially near hard sessions or taper.
