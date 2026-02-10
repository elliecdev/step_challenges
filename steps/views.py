from django.shortcuts import render
from django.contrib.auth.views import LoginView
from .forms import BulmaLoginForm, StepEntryForm
from django.views.generic import CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from .models import StepEntry, Participant, StepChallenge
from django.utils.timezone import now
from collections import defaultdict
from django.views.generic import TemplateView
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce


challenges = [
    {
        'start': 'November 1, 2025',
        'end': 'December 31, 2025',
        'active': True,
        'name': 'Winter 2025 Challenge'
    },
    {
        'start': 'August 1, 2025',
        'end': 'September 31, 2025',
        'active': False,
        'name': 'Fall 2025 Challenge'
    },
    {
        'start': 'June 1, 2025',
        'end': 'July 31, 2025',
        'active': False,
        'name': 'Summer 2025 Challenge'
    },
    {
        'start': 'March 1, 2025',
        'end': 'April 31, 2025',
        'active': False,
        'name': 'Spring 2025 Challenge'
    }
]


class HomeView(TemplateView):
    template_name = "steps/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # --------------------
        # Current active challenge
        # --------------------
        current_challenge = (
            StepChallenge.objects
            .filter(is_active=True)
            .order_by("-start_date")
            .first()
        )
        context["current_challenge"] = current_challenge
        if not current_challenge:
            return context  # No active challenge → template handles empty state

        # --------------------
        # Challenge timing (REUSED helper)
        # --------------------
        context.update(get_challenge_days(current_challenge))

        # --------------------
        # Participant (if logged in & enrolled)
        # --------------------
        participant = None
        if user.is_authenticated:
            participant = (
                Participant.objects
                .filter(user=user, team__challenge=current_challenge)
                .select_related("team", "user")
                .first()
            )
        context["participant"] = participant

        # --------------------
        # Latest personal entry
        # --------------------
        context["latest_entry"] = (
            StepEntry.objects
            .filter(participant=participant)
            .order_by("-date")
            .first()
            if participant
            else None
        )

        # Total steps for the participant in the current challenge (sum of daily entries)
        context["participant_total_steps"] = (
            StepEntry.objects
            .filter(participant=participant, challenge=current_challenge)
            .aggregate(total=Coalesce(Sum("daily_steps"), 0))["total"]
            if participant
            else 0
        )

        # --------------------
        # Top participants (Top 3)
        # --------------------
        participants = (
            Participant.objects
            .filter(team__challenge=current_challenge)
            .annotate(
                latest_steps=Coalesce(
                    Sum(
                        "step_entries__daily_steps",
                        filter=Q(step_entries__challenge=current_challenge),
                    ),
                    0,
                )
            )
            .select_related("user", "team")
            .order_by("-latest_steps")
        )
        context["top_participants"] = participants[:3]

        # --------------------
        # Top teams (Top 3)
        # --------------------
        teams = (
            Participant.objects
            .filter(team__challenge=current_challenge)
            .values("team__id", "team__name", "team__color")
            .annotate(
                team_total=Coalesce(
                    Sum(
                        "step_entries__daily_steps",
                        filter=Q(step_entries__challenge=current_challenge),
                    ),
                    0,
                )
            )
            .order_by("-team_total")
        )
        context["top_teams"] = teams[:3]

        # --------------------
        # Quick stats
        # --------------------
        total_steps = (
            StepEntry.objects
            .filter(participant__team__challenge=current_challenge)
            .aggregate(total=Coalesce(Sum("daily_steps"), 0))["total"]
        )
        participant_count = Participant.objects.filter(team__challenge=current_challenge).count()
        entry_count = StepEntry.objects.filter(participant__team__challenge=current_challenge).count()
        avg_steps = int(total_steps / participant_count) if participant_count else 0

        context["quick_stats"] = {
            "total_steps": total_steps,
            "participant_count": participant_count,
            "entry_count": entry_count,
            "avg_steps": avg_steps,
        }

        # --------------------
        # Recent activity (latest 5)
        # --------------------
        context["recent_entries"] = (
            StepEntry.objects
            .filter(participant__team__challenge=current_challenge)
            .select_related("participant__user", "participant__team")
            .order_by("-date")[:5]
        )

        return context


class FrontendLoginView(LoginView):
    template_name = "steps/login.html"
    authentication_form = BulmaLoginForm


class StepEntryCreateView(LoginRequiredMixin, CreateView):
    model = StepEntry
    form_class = StepEntryForm

    template_name = "steps/stepentry_form.html"
    success_url = "/add-entry/"

    def get_active_challenges(self):
        return (
            StepChallenge.objects
            .filter(
                is_active=True,
                teams__participants__user=self.request.user
            )
            .distinct()
            .order_by("-start_date")
        )

    def get_initial(self):
        initial = super().get_initial()
        challenges = self.get_active_challenges()

        # Preselect most recent challenge
        if challenges.count() > 1:
            initial["challenge"] = challenges.first()

        # Preselect today's date
        initial["date"] = now().date()

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        challenges = self.get_active_challenges()
        context["active_challenges"] = challenges
        context["single_challenge"] = challenges.count() == 1

        context["past_entries"] = (
            StepEntry.objects
            .filter(participant__user=self.request.user)
            .select_related("challenge")
            .order_by("-date")
        )

        # 🔹 Group past entries by challenge
        entries_by_challenge = defaultdict(list)

        past_entries = (
            StepEntry.objects
            .filter(participant__user=self.request.user)
            .select_related(
                "challenge",
                "participant__team"
            )
            .order_by("-date")
        )

        for entry in past_entries:
            entries_by_challenge[entry.challenge].append(entry)

        context["entries_by_challenge"] = dict(entries_by_challenge)

        # single challenge participant info
        if context["single_challenge"]:
            challenge = challenges.first()
            context.update(get_challenge_days(challenge))

            participant = Participant.objects.select_related(
                "user", "team"
            ).get(
                user=self.request.user,
                team__challenge=challenge
            )

            context["participant"] = participant

        return context

    def form_valid(self, form):
        challenge = form.cleaned_data["challenge"]

        # 🔒 OPTIONAL SAFETY CHECK
        # If only one active challenge exists, enforce it
        active_challenges = StepChallenge.objects.filter(is_active=True)

        if active_challenges.count() == 1:
            challenge = active_challenges.first()
            form.instance.challenge = challenge

        try:
            participant = Participant.objects.get(
                user=self.request.user,
                team__challenge=challenge
            )
        except Participant.DoesNotExist:
            raise PermissionDenied("You are not a participant in this challenge.")

        form.instance.participant = participant

        return super().form_valid(form)


class StepEntryListView(LoginRequiredMixin, ListView):
    model = StepEntry
    template_name = "steps/my_entries.html"

    def get_queryset(self):
        # Show only the logged-in participant's entries
        return StepEntry.objects.filter(participant__user=self.request.user)


class LeaderboardView(TemplateView):
    template_name = "steps/leaderboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # All challenges user participated in (empty for anonymous)
        if self.request.user.is_authenticated:
            challenges = (
                StepChallenge.objects
                .filter(teams__participants__user=self.request.user)
                .distinct()
                .order_by("-start_date")
            )
        else:
            challenges = StepChallenge.objects.none()

        context["challenges"] = challenges

        # Selected challenge
        challenge_id = self.request.GET.get("challenge")

        if challenge_id:
            challenge = StepChallenge.objects.get(id=challenge_id)
        else:
            challenge = challenges.filter(is_active=True).first() or challenges.first()

        context["challenge"] = challenge

        if not challenge:
            return context

        if challenge.is_active:
            context.update(get_challenge_days(challenge))

        # 🧍 Participant leaderboard (sum of daily steps per participant)
        participants = (
            Participant.objects
            .filter(team__challenge=challenge)
            .annotate(
                latest_steps=Coalesce(
                    Sum(
                        "step_entries__daily_steps",
                        filter=Q(step_entries__challenge=challenge),
                    ),
                    0,
                )
            )
            .select_related("user", "team")
            .order_by("-latest_steps")
        )

        context["participants"] = participants

        # 🏆 Team leaderboard
        teams = (
            Participant.objects
            .filter(team__challenge=challenge)
            .values(
                "team__id",
                "team__name",
                "team__color",
            )
            .annotate(
                team_steps=Coalesce(
                    Sum(
                        "step_entries__daily_steps",
                        filter=Q(step_entries__challenge=challenge),
                    ),
                    0,
                )
            )
            .order_by("-team_steps")
        )

        context["teams"] = teams

        return context


def get_challenge_days(challenge):
    """
    Returns a dict with:
    - days_elapsed: number of days passed since challenge started (min 0)
    - days_left: number of days remaining until challenge ends (min 0)
    - total_days: total duration of the challenge
    - progress_percent: percentage of time elapsed in challenge
    """
    today = now().date()
    total_days = (challenge.end_date - challenge.start_date).days + 1
    days_elapsed = (today - challenge.start_date).days + 1
    days_left = (challenge.end_date - today).days
    progress_percent = int((days_elapsed / total_days) * 100)

    return {
        "total_days": max(total_days, 1),
        "days_elapsed": max(days_elapsed, 0),
        "days_left": max(days_left, 0),
        "progress_percent": progress_percent
    }
