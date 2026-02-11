import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from steps.models import StepChallenge, Team, Participant, StepEntry


# Color mapping: team name to hex color
COLOR_MAP = {
    'Orange Team': '#FFA500',
    'Red Team': '#FF0000',
    'Blue Team': '#0000FF',
    'Green Team': '#008000',
    'Yellow Team': '#FFFF00',
    'Brown Team': '#8B4513',
}


class Command(BaseCommand):
    help = 'Import step challenge data from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to the CSV file to import'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']

        # Validate file exists
        if not os.path.exists(csv_file):
            raise CommandError(f'CSV file not found: {csv_file}')

        self.stdout.write(self.style.SUCCESS('Starting ETL process...'))

        try:
            # Step 1: Create Challenge
            challenge = self._create_challenge()
            self.stdout.write(
                self.style.SUCCESS(f'✓ Challenge created: {challenge.name}')
            )

            # Step 2: Create Teams
            teams_dict = self._create_teams(challenge, csv_file)
            self.stdout.write(
                self.style.SUCCESS(f'✓ {len(teams_dict)} teams created')
            )

            # Step 3: Create Participants
            users_dict = self._create_participants(teams_dict, csv_file)
            self.stdout.write(
                self.style.SUCCESS(f'✓ {len(users_dict)} participants created')
            )

            # Step 4: Create Step Entries
            entry_count = self._create_step_entries(
                challenge, users_dict, csv_file
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ {entry_count} step entries created'
                )
            )

            self.stdout.write(
                self.style.SUCCESS('✓ ETL process completed successfully!')
            )

        except Exception as e:
            raise CommandError(f'Error during ETL: {str(e)}')

    def _create_challenge(self):
        """Create the December 2025 challenge"""
        challenge, created = StepChallenge.objects.get_or_create(
            name='December 2025',
            defaults={
                'start_date': datetime(2025, 12, 1).date(),
                'end_date': datetime(2025, 12, 31).date(),
                'is_active': False,
            }
        )
        if not created:
            self.stdout.write(
                self.style.WARNING(
                    'Challenge already exists. Using existing challenge.'
                )
            )
        return challenge

    def _create_teams(self, challenge, csv_file):
        """Create teams from unique team names in CSV"""
        teams_dict = {}

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            unique_teams = set()

            for row in reader:
                team_name = row['Teams'].strip()
                if team_name:
                    unique_teams.add(team_name)

        for team_name in sorted(unique_teams):
            color = COLOR_MAP.get(team_name, '#808080')  # Default gray
            team, created = Team.objects.get_or_create(
                challenge=challenge,
                name=team_name,
                defaults={'color': color}
            )
            teams_dict[team_name] = team

            status = 'Created' if created else 'Exists'
            self.stdout.write(
                self.style.SUCCESS(f'  {status}: {team_name} ({color})')
            )

        return teams_dict

    def _create_participants(self, teams_dict, csv_file):
        """Create users and participants from CSV data"""
        users_dict = {}
        participants_created = 0

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            unique_members = {}

            # First pass: collect unique members with their team
            for row in reader:
                member_name = row['Member'].strip()
                team_name = row['Teams'].strip()

                if member_name and member_name not in unique_members:
                    unique_members[member_name] = team_name

        # Create users and participants
        for member_name, team_name in sorted(unique_members.items()):
            if not member_name or team_name not in teams_dict:
                continue

            # Parse first and last name
            name_parts = member_name.strip().split()
            if len(name_parts) < 2:
                self.stdout.write(
                    self.style.WARNING(
                        f'  Skipping invalid name: {member_name}'
                    )
                )
                continue

            first_name = name_parts[0]
            last_name = ' '.join(name_parts[1:])
            username = f'{first_name.lower()}.{last_name.lower()}'.replace(
                ' ', ''
            )

            # Create or get user
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': '',
                }
            )

            # Create participant
            team = teams_dict[team_name]
            participant, participant_created = Participant.objects.get_or_create(
                user=user,
                team=team
            )

            if participant_created:
                participants_created += 1

            users_dict[member_name] = {
                'user': user,
                'participant': participant,
                'team': team,
            }

            status = 'Created' if user_created else 'Exists'
            self.stdout.write(
                self.style.SUCCESS(
                    f'  {status}: {username} ({team_name})'
                )
            )

        return users_dict

    def _create_step_entries(self, challenge, users_dict, csv_file):
        """Create step entries from CSV data"""
        entries_created = 0
        entries_skipped = 0
        entries_to_create = []

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                member_name = row['Member'].strip()
                date_str = row['Date'].strip()
                steps_str = row['Steps'].strip()

                # Skip if missing data
                if not member_name or not date_str or not steps_str:
                    entries_skipped += 1
                    continue

                # Skip if member not found
                if member_name not in users_dict:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  Member not found: {member_name}'
                        )
                    )
                    entries_skipped += 1
                    continue

                try:
                    # Parse date
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

                    # Parse steps (remove commas if present)
                    daily_steps = int(steps_str.replace(',', ''))

                    # Get participant
                    participant = users_dict[member_name]['participant']

                    # Create step entry object (don't save yet)
                    entry = StepEntry(
                        participant=participant,
                        challenge=challenge,
                        date=date_obj,
                        daily_steps=daily_steps
                    )
                    entries_to_create.append(entry)

                except (ValueError, KeyError) as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  Error processing row: {row} - {str(e)}'
                        )
                    )
                    entries_skipped += 1
                    continue

        # Bulk create without validation (for historical data)
        if entries_to_create:
            # Use bulk_create with skip_validation workaround
            # We'll use queryset.bulk_create which bypasses the save() validation
            created_entries = StepEntry.objects.bulk_create(
                entries_to_create,
                ignore_conflicts=True,
                batch_size=1000
            )
            entries_created = len(created_entries)

        self.stdout.write(
            self.style.SUCCESS(
                f'  Created: {entries_created} entries'
            )
        )
        if entries_skipped > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'  Skipped: {entries_skipped} entries'
                )
            )

        return entries_created
