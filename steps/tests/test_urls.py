from django.test import TestCase
from django.urls import reverse, resolve

from steps.views import (
    HomeView,
    FrontendLoginView,
    StepEntryCreateView,
    StepEntryListView,
    LeaderboardView,
)


class UrlResolutionTest(TestCase):
    def test_steps_home_resolves(self):
        url = reverse("steps-home")
        self.assertEqual(url, "/")
        self.assertEqual(resolve(url).func.view_class, HomeView)

    def test_steps_login_resolves(self):
        url = reverse("steps-login")
        self.assertEqual(url, "/login/")
        self.assertEqual(resolve(url).func.view_class, FrontendLoginView)

    def test_steps_logout_resolves(self):
        url = reverse("steps-logout")
        self.assertEqual(url, "/logout/")

    def test_steps_add_entry_resolves(self):
        url = reverse("steps-add-entry")
        self.assertEqual(url, "/add-entry/")
        self.assertEqual(resolve(url).func.view_class, StepEntryCreateView)

    def test_steps_my_entries_resolves(self):
        url = reverse("steps-my-entries")
        self.assertEqual(url, "/my-entries/")
        self.assertEqual(resolve(url).func.view_class, StepEntryListView)

    def test_steps_leaderboard_resolves(self):
        url = reverse("steps-leaderboard")
        self.assertEqual(url, "/leaderboard/")
        self.assertEqual(resolve(url).func.view_class, LeaderboardView)
