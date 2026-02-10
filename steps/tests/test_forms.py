from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase

from steps.forms import BulmaLoginForm, StepEntryForm, TeamAdminForm
from steps.models import StepChallenge, Team, Participant, StepEntry


class BulmaLoginFormTest(TestCase):
    def test_username_has_input_class(self):
        form = BulmaLoginForm()
        self.assertIn('class="input"', str(form["username"]) or form["username"].as_widget())

    def test_password_has_input_class(self):
        form = BulmaLoginForm()
        widget_str = str(form["password"].as_widget())
        self.assertIn("input", widget_str)


class TeamAdminFormTest(TestCase):
    def setUp(self):
        self.challenge = StepChallenge.objects.create(
            name="C",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
        )

    def test_team_form_has_color_field(self):
        form = TeamAdminForm(instance=Team(challenge=self.challenge))
        self.assertIn("color", form.fields)
        self.assertIn("name", form.fields)
        # Form renders without error
        self.assertIn("color", form.as_p())


class StepEntryFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u", password="p")
        self.challenge = StepChallenge.objects.create(
            name="C",
            start_date=date.today() - timedelta(days=5),
            end_date=date.today() + timedelta(days=10),
        )
        self.team = Team.objects.create(
            challenge=self.challenge,
            name="T",
            color="#fff",
        )
        self.participant = Participant.objects.create(user=self.user, team=self.team)

    def test_form_has_expected_fields(self):
        form = StepEntryForm()
        self.assertEqual(
            list(form.fields.keys()),
            ["challenge", "date", "daily_steps"],
        )

    def test_form_valid_with_good_data(self):
        form = StepEntryForm(
            data={
                "challenge": self.challenge.pk,
                "date": date.today().isoformat(),
                "daily_steps": "6000",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_date_widget_has_date_type(self):
        form = StepEntryForm()
        # DateInput uses type="date" (Django 4.1+) or attrs
        widget = form.fields["date"].widget
        self.assertTrue(
            getattr(widget, "input_type", None) == "date"
            or widget.attrs.get("type") == "date"
        )
