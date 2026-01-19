# forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Team


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