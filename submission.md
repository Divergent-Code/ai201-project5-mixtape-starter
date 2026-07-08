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
<!-- One entry per bug. We'll fill these in later. -->
