from django.shortcuts import render

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
