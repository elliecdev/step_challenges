# forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Team, StepEntry


class BulmaLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"class": "input"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "input"})
    )


class TeamAdminForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = "__all__"
        widgets = {
            "color": forms.TextInput(
                attrs={
                    "type": "color",
                    "style": "width: 60px; height: 34px; padding: 0;",
                }
            )
        }


class StepEntryForm(forms.ModelForm):
    class Meta:
        model = StepEntry
        fields = ["challenge", "date", "daily_steps"]
        widgets = {
            "date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "input",
                }
            ),
            "daily_steps": forms.NumberInput(
                attrs={"class": "input"}
            ),
        }
