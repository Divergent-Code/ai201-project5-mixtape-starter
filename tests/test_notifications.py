"""
tests/test_notifications.py — Mixtape

Regression test for Issue #4: rating a song should notify the song's sharer.
"""

import pytest
from app import create_app, db
from models import User, Song, Notification
from services.notification_service import rate_song


@pytest.fixture
def app():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


def test_rating_a_song_notifies_the_sharer(app):
    """
    Regression test for Issue #4.

    When a user rates a song that someone else shared, the original sharer
    should receive a 'song_rated' notification. Before the fix, rate_song
    saved the Rating but never called create_notification, so the sharer
    had zero notifications and this assertion (== 1) would fail.
    """
    with app.app_context():
        sharer = User(username="sharer", email="sharer@example.com")
        rater = User(username="rater", email="rater@example.com")
        db.session.add_all([sharer, rater])
        db.session.commit()

        song = Song(title="Test Track", artist="Tester", shared_by=sharer.id)
        db.session.add(song)
        db.session.commit()

        rate_song(rater.id, song.id, 5)

        notifications = (
            db.session.query(Notification)
            .filter_by(user_id=sharer.id, notification_type="song_rated")
            .all()
        )
        assert len(notifications) == 1


def test_rating_your_own_song_does_not_notify(app):
    """
    The sharer should not be notified when they rate their own song
    (guarded by `if song.shared_by != user_id`).
    """
    with app.app_context():
        sharer = User(username="soloist", email="solo@example.com")
        db.session.add(sharer)
        db.session.commit()

        song = Song(title="Solo Track", artist="Soloist", shared_by=sharer.id)
        db.session.add(song)
        db.session.commit()

        rate_song(sharer.id, song.id, 4)

        notifications = (
            db.session.query(Notification)
            .filter_by(user_id=sharer.id, notification_type="song_rated")
            .all()
        )
        assert len(notifications) == 0
