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
from django.db.models import OuterRef, Subquery, Sum


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


def home(request):
    context = {
        'current_challenge': challenges[0],
        'challenges': challenges,
    }
    return render(request, 'steps/home.html', context)


def leaderboard(request):
    context = {
        'current_challenge': challenges[0],
        'challenges': challenges,
    }
    return render(request, 'steps/leaderboard.html', context)


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
        print("DEBUG: entries_by_challenge =", entries_by_challenge)
        print("DEBUG: entries_by_challenge.items =", entries_by_challenge.items)

        # single challenge participant info
        if context["single_challenge"]:
            challenge = challenges.first()
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

        # All challenges user participated in
        challenges = (
            StepChallenge.objects
            .filter(teams__participants__user=self.request.user)
            .distinct()
            .order_by("-start_date")
        )

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
            today = now().date()

            total_days = (challenge.end_date - challenge.start_date).days + 1
            days_elapsed = (today - challenge.start_date).days + 1
            days_elapsed = max(min(days_elapsed, total_days), 0)

            days_left = (challenge.end_date - today).days
            days_left = max(days_left, 0)

            progress_percent = int((days_elapsed / total_days) * 100)

            context.update({
                "days_left": days_left,
                "total_days": total_days,
                "days_elapsed": days_elapsed,
                "progress_percent": progress_percent,
            })

        # 🔹 Subquery to get latest entry per participant
        latest_entry = (
            StepEntry.objects
            .filter(
                participant=OuterRef("pk"),
                challenge=challenge
            )
            .order_by("-date")
            .values("total_steps")[:1]
        )

        # 🧍 Participant leaderboard
        participants = (
            Participant.objects
            .filter(team__challenge=challenge)
            .annotate(latest_steps=Subquery(latest_entry))
            .select_related("user", "team")
            .order_by("-latest_steps")
        )

        context["participants"] = participants

        # 🏆 Team leaderboard
        teams = (
            participants
            .values(
                "team__id",
                "team__name",
                "team__color",
            )
            .annotate(team_steps=Sum("latest_steps"))
            .order_by("-team_steps")
        )

        context["teams"] = teams

        return context