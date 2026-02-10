from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from steps.models import (
    StepChallenge,
    Team,
    Participant,
    StepEntry,
)


class HomeViewParticipantLookupTest(TestCase):
    def setUp(self):
        # 👤 User
        self.user = User.objects.create_user(
            username="alice",
            password="password123",
            first_name="Alice",
            last_name="Walker",
        )

        # 🏁 Active challenge
        self.challenge = StepChallenge.objects.create(
            name="Spring Step Challenge",
            start_date=date.today() - timedelta(days=5),
            end_date=date.today() + timedelta(days=10),
            is_active=True,
        )

        # 🏆 Team
        self.team = Team.objects.create(
            name="Fast Feet",
            color="#ff3860",
            challenge=self.challenge,
        )

        # 🧍 Participant (IMPORTANT RELATION)
        self.participant = Participant.objects.create(
            user=self.user,
            team=self.team,
        )

        # 👟 Step entry
        StepEntry.objects.create(
            participant=self.participant,
            challenge=self.challenge,
            date=date.today(),
            daily_steps=5000,
        )

    def test_home_view_finds_participant_via_team_challenge(self):
        """
        Regression test:
        Ensures HomeView resolves Participant using team__challenge
        and does NOT attempt Participant.challenge (which does not exist).
        """
        self.client.login(username="alice", password="password123")

        response = self.client.get(reverse("steps-home"))

        # Page loads
        self.assertEqual(response.status_code, 200)

        # Participant is injected into context
        self.assertIn("participant", response.context)

        participant = response.context["participant"]

        # Correct participant returned
        self.assertIsNotNone(participant)
        self.assertEqual(participant.user, self.user)
        self.assertEqual(participant.team, self.team)
        self.assertEqual(participant.team.challenge, self.challenge)

    def test_home_view_no_participant_when_user_not_in_challenge(self):
        other_user = User.objects.create_user(
            username="bob",
            password="password123",
        )

        self.client.login(username="bob", password="password123")

        response = self.client.get(reverse("steps-home"))

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get("participant"))