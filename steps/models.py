from django.db import models
from django.contrib.auth.models import User
from django.forms import ValidationError


class StepChallenge(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

    # Admin-controlled flag
    is_active = models.BooleanField(
        default=True,
        help_text="Controls whether participants can still add steps."
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Team(models.Model):
    challenge = models.ForeignKey(
        StepChallenge,
        on_delete=models.CASCADE,
        related_name="teams"
    )

    name = models.CharField(max_length=50)
    color = models.CharField(
        max_length=7,
        help_text="Hex color code, e.g. #6c63ff"
    )

    def __str__(self):
        return f"{self.name} ({self.challenge.name})"


class Participant(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="participants"
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class StepEntry(models.Model):
    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name="step_entries"
    )

    challenge = models.ForeignKey(
        StepChallenge,
        on_delete=models.CASCADE,
        related_name="step_entries"
    )

    date = models.DateField()

    # Daily steps entered by the participant for this date
    daily_steps = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("participant", "challenge", "date")
        ordering = ["date"]

    def clean(self):
        if not self.participant_id or not self.challenge_id:
            return
        
        # Block if challenge is closed by admin
        if not self.challenge.is_active:
            raise ValidationError(
                "This challenge is closed. Steps can no longer be added."
            )

        # Ensure step date is within challenge window
        if not (self.challenge.start_date <= self.date <= self.challenge.end_date):  # noqa: E501
            raise ValidationError(
                "Step date must be within the challenge period."
            )

    def save(self, *args, **kwargs):
        self.full_clean()  # Enforce validation everywhere
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.participant} – "
            f"{self.daily_steps} steps on {self.date}"
        )


