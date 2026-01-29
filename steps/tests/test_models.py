from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from steps.models import StepChallenge, Team, Participant, StepEntry


class StepChallengeModelTest(TestCase):
    def test_str(self):
        challenge = StepChallenge(
            name="Winter Steps",
            start_date=date(2025, 11, 1),
            end_date=date(2025, 12, 31),
        )
        self.assertEqual(str(challenge), "Winter Steps")

    def test_creation(self):
        challenge = StepChallenge.objects.create(
            name="Test Challenge",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            is_active=True,
        )
        self.assertEqual(challenge.name, "Test Challenge")
        self.assertTrue(challenge.is_active)
        self.assertIsNotNone(challenge.created_at)


class TeamModelTest(TestCase):
    def setUp(self):
        self.challenge = StepChallenge.objects.create(
            name="Challenge",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
        )

    def test_str(self):
        team = Team(challenge=self.challenge, name="Runners", color="#ff0000")
        self.assertEqual(str(team), "Runners (Challenge)")


class ParticipantModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice",
            password="pass",
            first_name="Alice",
            last_name="Smith",
        )
        self.challenge = StepChallenge.objects.create(
            name="C",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
        )
        self.team = Team.objects.create(
            challenge=self.challenge,
            name="T",
            color="#000",
        )

    def test_str_uses_full_name(self):
        p = Participant.objects.create(user=self.user, team=self.team)
        self.assertEqual(str(p), "Alice Smith")

    def test_str_falls_back_to_username(self):
        user = User.objects.create_user(username="bob", password="pass")
        p = Participant.objects.create(user=user, team=self.team)
        self.assertEqual(str(p), "bob")


class StepEntryModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice",
            password="pass",
        )
        self.challenge = StepChallenge.objects.create(
            name="Challenge",
            start_date=date.today() - timedelta(days=5),
            end_date=date.today() + timedelta(days=10),
            is_active=True,
        )
        self.team = Team.objects.create(
            challenge=self.challenge,
            name="Team",
            color="#fff",
        )
        self.participant = Participant.objects.create(
            user=self.user,
            team=self.team,
        )

    def test_str(self):
        entry = StepEntry(
            participant=self.participant,
            challenge=self.challenge,
            date=date.today(),
            total_steps=7000,
        )
        entry.save()
        self.assertIn("7000", str(entry))
        self.assertIn("steps", str(entry))

    def test_valid_entry_saves(self):
        StepEntry.objects.create(
            participant=self.participant,
            challenge=self.challenge,
            date=date.today(),
            total_steps=5000,
        )
        self.assertEqual(StepEntry.objects.count(), 1)

    def test_date_outside_challenge_raises_validation_error(self):
        entry = StepEntry(
            participant=self.participant,
            challenge=self.challenge,
            date=date.today() - timedelta(days=20),
            total_steps=5000,
        )
        with self.assertRaises(ValidationError) as cm:
            entry.full_clean()
        self.assertIn("within the challenge period", str(cm.exception))

    def test_decreasing_steps_raises_validation_error(self):
        StepEntry.objects.create(
            participant=self.participant,
            challenge=self.challenge,
            date=date.today() - timedelta(days=1),
            total_steps=10000,
        )
        entry = StepEntry(
            participant=self.participant,
            challenge=self.challenge,
            date=date.today(),
            total_steps=5000,
        )
        with self.assertRaises(ValidationError) as cm:
            entry.full_clean()
        self.assertIn("cannot be less than your previous entry", str(cm.exception))

    def test_closed_challenge_raises_validation_error(self):
        self.challenge.is_active = False
        self.challenge.save()
        entry = StepEntry(
            participant=self.participant,
            challenge=self.challenge,
            date=date.today(),
            total_steps=5000,
        )
        with self.assertRaises(ValidationError) as cm:
            entry.full_clean()
        self.assertIn("closed", str(cm.exception))

    def test_save_calls_full_clean(self):
        """Save() should enforce validation (e.g. date outside window)."""
        entry = StepEntry(
            participant=self.participant,
            challenge=self.challenge,
            date=date.today() + timedelta(days=100),
            total_steps=5000,
        )
        with self.assertRaises(ValidationError):
            entry.save()
