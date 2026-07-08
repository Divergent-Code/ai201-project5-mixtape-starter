# Mixtape Bug Hunt — Submission

## AI Usage
<!-- We'll write this last. -->

## Codebase Map

### How the app is organized

When someone uses the app, their request goes to the **routes** first, which hands it to a **service**, which uses the **models**.

- **routes/** — the front desk: receives the request, doesn't do the real work.
- **services/** — the engine room: where the actual logic lives.
- **models.py** — the data: the app's "nouns" (users, songs, playlists, notifications).

### What each part does

- **app.py** — starts the app and connects the pieces together.
- **models.py** — defines the app's "nouns": User, Song, Playlist, Notification (and a few others).
- **routes/** — the front desk. Four files (songs, playlists, users, feed) that receive web requests and hand them off. They don't hold real logic.
- **services/** — the engine room. Five files, each responsible for one area of logic:
  - `streak_service.py` — listening streaks
  - `feed_service.py` — the "friends listening now" feed
  - `search_service.py` — searching for songs
  - `notification_service.py` — notifications, plus rating and playlist-adding
  - `playlist_service.py` — getting a playlist's songs
- **tests/** — automated checks for streaks, search, and playlists.

### A walk-through of one feature: rating a song

1. A request comes in to rate a song → handled by the `rate` route in **routes/songs.py**.
2. The route hands off to the **`rate_song`** function in **notification_service.py**.
3. `rate_song` checks the score is 1–5, looks up the song and the user, then saves a **`Rating`** to the database (a new one, or updates an existing one) and returns it.

So the path is: **request → routes → service (`rate_song`) → `Rating` model.**

## Root Cause Analysis

### Issue #1 — My listening streak keeps resetting (`streak_service.py`)

- **How I reproduced it:** I ran the existing test `pytest tests/test_streaks.py::test_streak_increments_on_sunday`. It failed with `assert 1 == 2`. The test simulates a user listening on Saturday (streak becomes 1) and then Sunday (streak should become 2), but the streak stayed at 1 — confirming that listening on a Sunday does not add to the streak.

- **How I found the root cause (navigation path):** I knew the streak bug had to live in `streak_service.py`, because each service file owns one area of logic. I opened it and found the function `update_listening_streak`. Its decision block has three branches: (1) listened today → do nothing, (2) listened yesterday → add to streak, (3) otherwise → reset to 1. I noticed branch (2) had an extra condition the others didn't: `and today.weekday() != 6`.

- **The root cause:** In Python, `weekday()` returns 6 for Sunday. So branch (2) — the "add to streak" branch — only runs when today is *not* Sunday. On a Sunday, a user who listened yesterday should still get their streak incremented, but the extra `!= 6` condition blocks branch (2), so execution falls through to branch (3), which resets the streak to 1. That is why the streak "kept resetting" — specifically only when the second listening day landed on a Sunday.

- **My fix:** I removed the `and today.weekday() != 6` condition, so branch (2) now reads `elif days_since_last == 1:`. A streak now increments any time the user listened on the previous day, regardless of which day of the week it is.

- **Side-effect check:** I ran the full `pytest tests/test_streaks.py`. All 5 tests pass, including the ones covering normal weekday increments and skipped-day resets. This confirms the fix restores Sunday behavior without changing how streaks work on other days or how they reset when a day is skipped.
