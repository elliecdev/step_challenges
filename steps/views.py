from django.shortcuts import render
from django.contrib.auth.views import LoginView
from .forms import BulmaLoginForm

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
