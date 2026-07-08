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

### Issue #2 — Friends Listening Now shows people from yesterday (`feed_service.py`)

- **How I reproduced it:** There is no existing test for the feed, so I wrote a small throwaway script that seeds fresh data and calls `get_friends_listening_now` for two users. It showed that "kenji" saw his friend "nova" in the Listening Now feed even though nova's most recent listen was ~120 minutes ago — clearly not "now." Meanwhile the friends who listened 10–20 minutes ago also showed up. So the feed was including listens from far too long ago.

- **How I found the root cause (navigation path):** I opened `feed_service.py` (the service that owns the feed) and looked at `get_friends_listening_now`. It builds a `cutoff` time from a constant near the top of the file: `RECENT_THRESHOLD = timedelta(hours=24)`, then keeps every listening event newer than that cutoff. I also read the comments in `seed_data.py`, which said recent events "within the past 30 minutes" should appear and older ones "should NOT appear in 'listening now' after fix." That mismatch — 24 hours in the code vs. 30 minutes intended — told me the threshold value was the problem.

- **The root cause:** `RECENT_THRESHOLD` was set to 24 hours. The feed is meant to show who is listening *right now*, but a 24-hour window counts anyone who listened at any point in the last full day — including yesterday. So the cutoff was far too generous, which is exactly why stale listens (like nova's from 2 hours ago) were treated as "listening now."

- **My fix:** I changed `RECENT_THRESHOLD` from `timedelta(hours=24)` to `timedelta(minutes=30)`, matching the intended "now" window described in the seed data comments. The recency filter logic itself was correct; only the window size was wrong.

- **Side-effect check:** I re-ran my script and confirmed both sides of the boundary: friends who listened 17–27 minutes ago still appear, while the 2-hour-old listen no longer does. I also checked the other function in the same file, `get_activity_feed`, and confirmed it does not use `RECENT_THRESHOLD` at all (it is intentionally not recency-filtered), so my change cannot affect it. Finally I ran the full test suite — the streak and search tests still pass; the only failures are the two pre-existing playlist tests for Issue #5, which are unrelated to this change.

### Issue #3 — The same song keeps showing up twice in search (`search_service.py`)

- **How I reproduced it:** The seed data comments point out that songs with 3+ tags are the ones that expose this issue, so I searched for "Crown Heights Anthem" (which has 3 tags). At first the visible result showed the song only once, which surprised me, so I wrote a diagnostic script to look closer. It confirmed the song has 3 tags, and that the search's underlying database query returns **3 rows** for it (one per tag) — the duplicate is really being produced. The reason it only *appeared* once is that the installed SQLAlchemy version (2.0.51) automatically de-duplicates whole-entity results before returning them, which masks the duplicate on this setup. On a version or query style without that automatic de-duplication (which is how the issue was originally reported), the same song shows up once per tag.

- **How I found the root cause (navigation path):** I opened `search_service.py` and read `search_songs`. The query joins `Song` to the `song_tags` association table with `.outerjoin(song_tags, Song.id == song_tags.c.song_id)`. I checked what the join was used for and found that the `filter` only matches on `Song.title` and `Song.artist` — it never references tags — and that a song's tags are loaded separately via the `Song.tags` relationship (which is why `to_dict()` still lists them). So the join contributed nothing to the search except extra rows: one row per tag. That is why only multi-tag songs are affected.

- **The root cause:** The `outerjoin` to `song_tags` multiplies the result rows by the number of tags a song has. A song with 3 tags produces 3 identical rows. Since the join is not needed for filtering (the search matches title/artist only) and not needed for loading tags (that happens through the relationship), it is pure fan-out — it only creates duplicates, and only for songs that have more than one tag.

- **My fix:** I removed the `.outerjoin(song_tags, Song.id == song_tags.c.song_id)` line so the query selects songs by title/artist alone. Tags still appear in each result because they are loaded through the `Song.tags` relationship, independent of this query.

- **Side-effect check:** I re-ran `pytest tests/test_search.py` — all 5 tests pass, so ordinary searches (by title, by artist, no-match, case-insensitive) still behave correctly, and songs still come back with their tags. Removing the join means the query no longer fans out to one row per tag, so the duplicate cannot occur regardless of whether the database library happens to de-duplicate. I also confirmed the change is isolated to `search_songs` and does not touch `get_song`.

### Issue #4 — Notified on playlist-add but not on rating (`notification_service.py`)

- **How I reproduced it:** There is no existing test for this, so I wrote a script that has "nova" rate a song shared by "darius" and then counts darius's notifications before and after. Before the rating darius had 0 notifications, and after the rating he still had 0 — confirming that rating a song does not notify the song's owner. For contrast, the seed data already contains a working "song added to playlist" notification, so the two actions behave differently.

- **How I found the root cause (navigation path):** The hint said this was architectural, not a typo, so I opened `notification_service.py` and compared the two friend-interaction functions side by side. `add_to_playlist` ends by calling `create_notification(...)` for `song.shared_by` (guarded by `if song.shared_by != added_by_user_id`). I then read `rate_song` line by line and found it saves the `Rating`, commits, and returns — it never calls `create_notification` at all. The working function and the broken function sit right next to each other, which made the missing call obvious.

- **The root cause:** `rate_song` was missing the notification step entirely. It correctly records the rating, but unlike `add_to_playlist` it never creates a `Notification` for the person who shared the song. So the data (the rating) was saved, but the side effect that tells the owner "someone rated your song" was simply absent.

- **My fix:** I added a `create_notification` call at the end of `rate_song`, mirroring the pattern in `add_to_playlist`: after the rating is committed, if the rater is not the song's sharer (`if song.shared_by != user_id`), it creates a `song_rated` notification for `song.shared_by` with a message naming the rater, the song, and the score. I reused the existing `create_notification` helper rather than writing new logic, so it follows the same path as the working notification.

- **Side-effect check:** I re-ran my script and confirmed darius's notification count went from 0 to 1 after the rating. I also ran the full test suite: the streak and search tests still pass and one playlist test passes; the only two failures are the pre-existing Issue #5 playlist tests, which this change does not touch. I specifically preserved the `if song.shared_by != user_id` guard so that a user rating their own song does not receive a self-notification, matching how `add_to_playlist` avoids notifying the person who performed the action.
