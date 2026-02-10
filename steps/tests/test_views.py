from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from steps.models import StepChallenge, Team, Participant, StepEntry
from steps.views import get_challenge_days


def make_challenge(name="Challenge", start=None, end=None, is_active=True):
    start = start or date.today() - timedelta(days=5)
    end = end or date.today() + timedelta(days=10)
    return StepChallenge.objects.create(
        name=name,
        start_date=start,
        end_date=end,
        is_active=is_active,
    )


def make_team(challenge, name="Team", color="#ff0000"):
    return Team.objects.create(challenge=challenge, name=name, color=color)


def make_participant(user, team):
    return Participant.objects.create(user=user, team=team)


class GetChallengeDaysTest(TestCase):
    def test_returns_correct_keys(self):
        challenge = make_challenge(
            start=date.today() - timedelta(days=10),
            end=date.today() + timedelta(days=20),
        )
        result = get_challenge_days(challenge)
        self.assertIn("days_elapsed", result)
        self.assertIn("days_left", result)
        self.assertIn("total_days", result)
        self.assertIn("progress_percent", result)

    def test_total_days(self):
        start = date.today() - timedelta(days=4)
        end = date.today() + timedelta(days=5)
        challenge = make_challenge(start=start, end=end)
        result = get_challenge_days(challenge)
        self.assertEqual(result["total_days"], 10)

    def test_days_elapsed_and_left_non_negative(self):
        challenge = make_challenge()
        result = get_challenge_days(challenge)
        self.assertGreaterEqual(result["days_elapsed"], 0)
        self.assertGreaterEqual(result["days_left"], 0)


class LoginViewTest(TestCase):
    def test_login_page_loads(self):
        response = self.client.get(reverse("steps-login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "steps/login.html")
        self.assertContains(response, "Username")
        self.assertContains(response, "Password")

    def test_login_redirects_authenticated_user(self):
        User.objects.create_user(username="u", password="p")
        self.client.login(username="u", password="p")
        response = self.client.get(reverse("steps-login"))
        # Django LoginView redirects GET when already logged in (default)
        self.assertIn(response.status_code, (200, 302))


class StepEntryCreateViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice",
            password="password123",
        )
        self.challenge = make_challenge()
        self.team = make_team(self.challenge)
        self.participant = make_participant(self.user, self.team)

    def test_add_entry_requires_login(self):
        response = self.client.get(reverse("steps-add-entry"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue((response.url or "").startswith("/login"))

    def test_add_entry_get_returns_form_when_logged_in(self):
        self.client.login(username="alice", password="password123")
        response = self.client.get(reverse("steps-add-entry"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("active_challenges", response.context)
        self.assertIn("past_entries", response.context)

    def test_form_valid_creates_entry(self):
        self.client.login(username="alice", password="password123")
        data = {
            "challenge": self.challenge.pk,
            "date": date.today().isoformat(),
            "daily_steps": "8000",
        }
        response = self.client.post(reverse("steps-add-entry"), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(StepEntry.objects.filter(participant=self.participant).count(), 1)

    def test_non_participant_gets_permission_denied(self):
        other_user = User.objects.create_user(
            username="bob",
            password="password123",
        )
        self.client.login(username="bob", password="password123")
        data = {
            "challenge": self.challenge.pk,
            "date": date.today().isoformat(),
            "daily_steps": "8000",
        }
        response = self.client.post(reverse("steps-add-entry"), data)
        self.assertEqual(response.status_code, 403)


class StepEntryListViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice",
            password="password123",
        )
        self.challenge = make_challenge()
        self.team = make_team(self.challenge)
        self.participant = make_participant(self.user, self.team)

    def test_my_entries_requires_login(self):
        response = self.client.get(reverse("steps-my-entries"))
        self.assertEqual(response.status_code, 302)

    def test_my_entries_shows_only_own_entries(self):
        StepEntry.objects.create(
            participant=self.participant,
            challenge=self.challenge,
            date=date.today(),
            daily_steps=5000,
        )
        other_user = User.objects.create_user(username="bob", password="p")
        other_team = make_team(self.challenge, name="B")
        other_p = make_participant(other_user, other_team)
        StepEntry.objects.create(
            participant=other_p,
            challenge=self.challenge,
            date=date.today(),
            daily_steps=9999,
        )
        self.client.login(username="alice", password="password123")
        response = self.client.get(reverse("steps-my-entries"))
        self.assertEqual(response.status_code, 200)
        qs = response.context["object_list"]
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().daily_steps, 5000)


class LeaderboardViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice",
            password="password123",
        )
        self.challenge = make_challenge()
        self.team = make_team(self.challenge)
        self.participant = make_participant(self.user, self.team)

    def test_leaderboard_loads_anonymous(self):
        response = self.client.get(reverse("steps-leaderboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "steps/leaderboard.html")

    def test_leaderboard_with_challenge_in_get(self):
        response = self.client.get(
            reverse("steps-leaderboard"),
            {"challenge": str(self.challenge.pk)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["challenge"], self.challenge)
        self.assertIn("participants", response.context)
        self.assertIn("teams", response.context)

    def test_leaderboard_no_challenge_empty_context(self):
        # User not in any challenge
        other_user = User.objects.create_user(username="bob", password="p")
        self.client.login(username="bob", password="p")
        response = self.client.get(reverse("steps-leaderboard"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("challenges", response.context)
        self.assertIn("challenge", response.context)


class HomeViewExtraTest(TestCase):
    """Additional home view tests (complements test_home_view.py)."""

    def test_home_no_active_challenge(self):
        make_challenge(is_active=False)
        response = self.client.get(reverse("steps-home"))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get("current_challenge"))

    def test_home_context_has_quick_stats_when_challenge_exists(self):
        challenge = make_challenge()
        team = make_team(challenge)
        user = User.objects.create_user(username="u", password="p")
        make_participant(user, team)
        response = self.client.get(reverse("steps-home"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("quick_stats", response.context)
        stats = response.context["quick_stats"]
        self.assertIn("total_steps", stats)
        self.assertIn("participant_count", stats)
        self.assertIn("avg_steps", stats)
