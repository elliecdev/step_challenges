#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'challenges.settings')
django.setup()

from steps.models import StepChallenge, Team, Participant, StepEntry

challenge = StepChallenge.objects.get(name='December 2025')
print(f"Challenge: {challenge.name}")
print(f"  Start: {challenge.start_date}")
print(f"  End: {challenge.end_date}")
print(f"  Active: {challenge.is_active}")
print()

teams = Team.objects.filter(challenge=challenge).order_by('name')
print(f"Teams ({teams.count()}):")
for team in teams:
    count = Participant.objects.filter(team=team).count()
    print(f"  {team.name} ({team.color}) - {count} participants")
print()

participants = Participant.objects.filter(team__challenge=challenge)
print(f"Total Participants: {participants.count()}")

entries = StepEntry.objects.filter(challenge=challenge)
print(f"Total Step Entries: {entries.count()}")
first_date = entries.order_by('date').first()
last_date = entries.order_by('-date').first()
print(f"Date range: {first_date.date} to {last_date.date}")
